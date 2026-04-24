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


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Pose une question sur un cours — pipeline RAG complet (LLM-first, fallback CamemBERT)."""
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

    # Encoder la question (blocking ML call → thread)
    query_vector = await asyncio.to_thread(embed_query, request.question)

    # Recherche FAISS — top-k chunks similaires
    try:
        search_results = search(request.course_id, query_vector, k=settings.top_k_retrieval)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Index de recherche indisponible pour ce cours.")

    # Récupérer les chunks correspondants
    context_chunks = []
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

    # Vérifier la confiance des résultats
    if not context_chunks or all(c["score"] < 0.3 for c in context_chunks):
        return AnswerResponse(
            answer="Je n'ai pas trouvé d'information pertinente dans ce cours pour cette question.",
            confidence=0.0,
            sources=[],
            session_id=session_id,
            llm_used=False,
        )

    # ── 1. Tentative LLM (RAG génératif, plus naturel) ──
    llm_answer = None
    try:
        llm_answer = await answer_with_llm(request.question, context_chunks)
    except Exception:
        logger.exception("LLM Q&A a planté")
        llm_answer = None

    if llm_answer:
        # Confiance basée sur le score moyen des top-3 sources
        top = sorted(context_chunks, key=lambda c: c["score"], reverse=True)[:3]
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

    # ── 2. Fallback CamemBERT-QA extractif ──
    qa_result = await asyncio.to_thread(answer_question, request.question, context_chunks)

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
    """Récupère les contextes pertinents. Retourne (context_chunks, top_sources)."""
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
    if not context_chunks or all(c["score"] < 0.3 for c in context_chunks):
        return [], []
    top = sorted(context_chunks, key=lambda c: c["score"], reverse=True)[:3]
    return context_chunks, top


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

    context_chunks, top = await _retrieve_contexts(request.course_id, request.question)
    session_id = request.session_id or str(uuid.uuid4())

    if not context_chunks:
        async def empty_gen():
            payload = {
                "sources": [],
                "session_id": session_id,
            }
            yield f"event: sources\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            msg = "Je n'ai pas trouvé d'information pertinente dans ce cours pour cette question."
            yield f"event: token\ndata: {json.dumps({'text': msg}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps({'finished': True, 'llm_used': False})}\n\n"
        return StreamingResponse(empty_gen(), media_type="text/event-stream")

    sources_data = [
        {
            "chunk_text": c["text"][:500],
            "page": c["page"],
            "chapter": c["chapter"],
            "similarity_score": float(c["score"]),
        }
        for c in top
    ]
    confidence = sum(c["score"] for c in top) / max(len(top), 1)

    async def event_stream():
        # 1) On envoie d'abord les sources
        payload = {
            "sources": sources_data,
            "session_id": session_id,
            "confidence": float(confidence),
        }
        yield f"event: sources\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # 2) On stream le LLM, ou on fallback CamemBERT
        full_answer_parts: list[str] = []
        llm_used = False
        try:
            async for chunk in stream_answer_with_llm(request.question, context_chunks):
                full_answer_parts.append(chunk)
                yield f"event: token\ndata: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
            llm_used = True
        except LLMUnavailable as exc:
            logger.info("LLM stream indisponible (%s) → fallback extractif", exc)
            qa_result = await asyncio.to_thread(answer_question, request.question, context_chunks)
            full_answer_parts = [qa_result["answer"]]
            yield f"event: token\ndata: {json.dumps({'text': qa_result['answer']}, ensure_ascii=False)}\n\n"
        except Exception:
            logger.exception("Erreur stream LLM")
            qa_result = await asyncio.to_thread(answer_question, request.question, context_chunks)
            full_answer_parts = [qa_result["answer"]]
            yield f"event: token\ndata: {json.dumps({'text': qa_result['answer']}, ensure_ascii=False)}\n\n"

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
