"""Router pour le système de Questions-Réponses."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.config import get_settings
from backend.models.schemas import (
    QuestionRequest, AnswerResponse, SourceDocument, HistoryEntry,
)
from backend.database.mongodb import (
    get_course_by_id, get_chunks_by_course, save_qa_exchange, get_qa_history,
)
from backend.services.embedder import embed_query
from backend.services.retriever import search
from backend.services.qa_engine import answer_question
from backend.services.llm_qa import answer_with_llm, stream_answer_with_llm
from backend.services.llm_client import LLMUnavailable

logger = logging.getLogger(__name__)
router = APIRouter()


# Seuil minimal de pertinence pour considérer qu'on a un *vrai* contexte du cours.
# En dessous : on appelle quand même le LLM (pour gérer salutations / hors-sujet),
# mais on ne lui passe PAS d'extraits, et on ne renvoie pas de sources.
_RELEVANCE_THRESHOLD = 0.30


def _select_relevant(context_chunks: list[dict]) -> tuple[list[dict], list[dict]]:
    """Sépare les extraits assez pertinents (≥ seuil) du reste.

    Retourne (extraits_pertinents, top_3_pour_sources).
    Si aucun extrait n'est au-dessus du seuil → listes vides : le LLM répondra
    de façon conversationnelle (salutation) ou refusera (hors-sujet).
    """
    relevant = [c for c in context_chunks if c["score"] >= _RELEVANCE_THRESHOLD]
    if not relevant:
        return [], []
    top = sorted(relevant, key=lambda c: c["score"], reverse=True)[:3]
    return relevant, top


async def _load_history(session_id: str, max_turns: int = 3) -> list[dict]:
    """Charge les `max_turns` derniers tours (=2*max_turns messages) en format LLM."""
    try:
        exchanges = await get_qa_history(session_id)
    except Exception:
        logger.exception("Impossible de charger l'historique Q&A")
        return []
    if not exchanges:
        return []
    recent = exchanges[-max_turns:]
    msgs: list[dict] = []
    for ex in recent:
        q = (ex.get("question") or "").strip()
        a = (ex.get("answer") or "").strip()
        if q:
            msgs.append({"role": "user", "content": q})
        if a:
            msgs.append({"role": "assistant", "content": a})
    return msgs


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Pose une question sur un cours — pipeline RAG conversationnel (Groq-first).

    Contrairement à l'ancienne version, on n'écarte plus brutalement les questions
    à faible score : le LLM gère lui-même salutations, hors-sujet et réponses
    sourcées (cf. prompt système dans `llm_qa.py`).
    """
    settings = get_settings()

    # Validation
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    # Vérifier que le cours existe
    course = await get_course_by_id(request.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    # Récupérer les chunks du cours
    chunks = await get_chunks_by_course(request.course_id)
    if not chunks:
        raise HTTPException(status_code=503, detail="Cours pas encore indexé, réessayez dans quelques instants.")

    course_title = course.get("title") or course.get("name") or ""

    # Encoder la question (blocking ML call → thread)
    query_vector = await asyncio.to_thread(embed_query, request.question)

    # Recherche FAISS — top-k chunks similaires
    try:
        search_results = search(request.course_id, query_vector, k=settings.top_k_retrieval)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Index de recherche indisponible pour ce cours.")

    # Récupérer les chunks correspondants
    context_chunks: list[dict] = []
    for result in search_results:
        idx = result["index"]
        if idx < len(chunks):
            chunk = chunks[idx]
            context_chunks.append({
                "text": chunk["text"],
                "page": chunk["page"],
                "chapter": chunk.get("chapter", ""),
                "score": result["score"],
            })

    session_id = request.session_id or str(uuid.uuid4())
    relevant, top = _select_relevant(context_chunks)
    history = await _load_history(session_id)

    # ── 1. LLM conversationnel (gère salutations, hors-sujet, et RAG sourcé) ──
    llm_answer = None
    try:
        llm_answer = await answer_with_llm(
            request.question,
            relevant,
            course_title=course_title,
            history=history,
        )
    except Exception:
        logger.exception("LLM Q&A a planté")
        llm_answer = None

    if llm_answer:
        if top:
            confidence = sum(c["score"] for c in top) / max(len(top), 1)
            sources_data = [
                {
                    "chunk_text": c["text"][:500],
                    "page": c["page"],
                    "chapter": c["chapter"],
                    "similarity_score": float(c["score"]),
                }
                for c in top
            ]
        else:
            confidence = 0.0
            sources_data = []
        exchange = {
            "question": request.question,
            "answer": llm_answer,
            "confidence": float(confidence),
            "timestamp": datetime.now(timezone.utc),
            "sources": sources_data,
            "llm_used": True,
        }
        await save_qa_exchange(session_id, request.course_id, exchange)
        return AnswerResponse(
            answer=llm_answer,
            confidence=float(confidence),
            sources=[SourceDocument(**s) for s in sources_data],
            session_id=session_id,
            llm_used=True,
        )

    # ── 2. Fallback CamemBERT-QA extractif (si LLM KO ET on a du contexte) ──
    if not relevant:
        # Pas de LLM et rien de pertinent dans le cours → message générique
        msg = (
            "Je n'ai pas trouvé d'information pertinente dans le cours pour ce message, "
            "et l'assistant LLM est temporairement indisponible. Reformule ta question "
            "sur le contenu du cours."
        )
        return AnswerResponse(
            answer=msg,
            confidence=0.0,
            sources=[],
            session_id=session_id,
            llm_used=False,
        )

    qa_result = await asyncio.to_thread(answer_question, request.question, relevant)

    exchange = {
        "question": request.question,
        "answer": qa_result["answer"],
        "confidence": qa_result["confidence"],
        "timestamp": datetime.now(timezone.utc),
        "sources": qa_result["sources"],
        "llm_used": False,
    }
    await save_qa_exchange(session_id, request.course_id, exchange)

    return AnswerResponse(
        answer=qa_result["answer"],
        confidence=qa_result["confidence"],
        sources=[
            SourceDocument(**s) for s in qa_result["sources"]
        ],
        session_id=session_id,
        llm_used=False,
    )


@router.get("/history/{session_id}", response_model=list[HistoryEntry])
async def get_history(session_id: str):
    """Récupère l'historique d'une session de Q&A."""
    exchanges = await get_qa_history(session_id)
    return [
        HistoryEntry(
            question=ex["question"],
            answer=ex["answer"],
            timestamp=ex["timestamp"],
            sources=[SourceDocument(**s) for s in ex.get("sources", [])],
        )
        for ex in exchanges
    ]


# ─── Streaming SSE pour le Q&A (effet ChatGPT) ────────────────────

async def _retrieve_contexts(course_id: str, question: str) -> tuple[list[dict], list[dict]]:
    """Récupère les extraits pertinents (≥ seuil) et le top-3 pour les sources.

    Retourne (relevant_chunks, top_3_for_sources).
    Listes vides si aucun extrait n'est pertinent (le LLM gérera : salutation/refus).
    """
    settings = get_settings()
    chunks = await get_chunks_by_course(course_id)
    if not chunks:
        return [], []
    query_vector = await asyncio.to_thread(embed_query, question)
    try:
        search_results = search(course_id, query_vector, k=settings.top_k_retrieval)
    except FileNotFoundError:
        return [], []
    context_chunks: list[dict] = []
    for result in search_results:
        idx = result["index"]
        if idx < len(chunks):
            chunk = chunks[idx]
            context_chunks.append({
                "text": chunk["text"],
                "page": chunk["page"],
                "chapter": chunk.get("chapter", ""),
                "score": result["score"],
            })
    return _select_relevant(context_chunks)


@router.post("/ask/stream")
async def ask_question_stream(request: QuestionRequest):
    """Stream la réponse Q&A token-par-token via SSE.

    Format SSE :
      event: sources\\n
      data: {"sources":[...], "session_id":"..."}\\n\\n
      event: token\\n
      data: {"text":"..."}\\n\\n
      ...
      event: done\\n
      data: {"finished":true}\\n\\n

    Si le LLM est indisponible, fallback en un seul event 'token' avec la réponse extractive.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    course = await get_course_by_id(request.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    course_title = course.get("title") or course.get("name") or ""
    relevant, top = await _retrieve_contexts(request.course_id, request.question)
    session_id = request.session_id or str(uuid.uuid4())
    history = await _load_history(session_id)

    sources_data = [
        {
            "chunk_text": c["text"][:500],
            "page": c["page"],
            "chapter": c["chapter"],
            "similarity_score": float(c["score"]),
        }
        for c in top
    ]
    confidence = (sum(c["score"] for c in top) / len(top)) if top else 0.0

    async def event_stream():
        # 1) On envoie d'abord les sources (vide si salutation/hors-sujet)
        payload = {
            "sources": sources_data,
            "session_id": session_id,
            "confidence": float(confidence),
        }
        yield f"event: sources\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # 2) On stream le LLM (gère salutation / RAG / refus hors-sujet)
        full_answer_parts: list[str] = []
        llm_used = False
        try:
            async for chunk in stream_answer_with_llm(
                request.question,
                relevant,
                course_title=course_title,
                history=history,
            ):
                full_answer_parts.append(chunk)
                yield f"event: token\ndata: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
            llm_used = True
        except LLMUnavailable as exc:
            logger.info("LLM stream indisponible (%s) → fallback", exc)
            if relevant:
                qa_result = await asyncio.to_thread(answer_question, request.question, relevant)
                fallback_msg = qa_result["answer"]
            else:
                fallback_msg = (
                    "L'assistant est temporairement indisponible. Réessaie dans un instant, "
                    "ou pose une question précise sur le contenu du cours."
                )
            full_answer_parts = [fallback_msg]
            yield f"event: token\ndata: {json.dumps({'text': fallback_msg}, ensure_ascii=False)}\n\n"
        except Exception:
            logger.exception("Erreur stream LLM")
            if relevant:
                qa_result = await asyncio.to_thread(answer_question, request.question, relevant)
                fallback_msg = qa_result["answer"]
            else:
                fallback_msg = "Une erreur est survenue. Réessaie dans un instant."
            full_answer_parts = [fallback_msg]
            yield f"event: token\ndata: {json.dumps({'text': fallback_msg}, ensure_ascii=False)}\n\n"

        full_answer = "".join(full_answer_parts).strip()

        # 3) Persister l'échange
        try:
            exchange = {
                "question": request.question,
                "answer": full_answer,
                "confidence": float(confidence),
                "timestamp": datetime.now(timezone.utc),
                "sources": sources_data,
                "llm_used": llm_used,
            }
            await save_qa_exchange(session_id, request.course_id, exchange)
        except Exception:
            logger.exception("Impossible de sauvegarder l'échange Q&A")

        # 4) Event final
        yield f"event: done\ndata: {json.dumps({'finished': True, 'llm_used': llm_used})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
