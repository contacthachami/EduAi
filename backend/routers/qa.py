"""Router pour le système de Questions-Réponses."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

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

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Pose une question sur un cours — pipeline RAG complet."""
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

    # Vérifier la confiance des résultats
    if not context_chunks or all(c["score"] < 0.3 for c in context_chunks):
        return AnswerResponse(
            answer="Je n'ai pas trouvé d'information pertinente dans ce cours pour cette question.",
            confidence=0.0,
            sources=[],
            session_id=request.session_id or str(uuid.uuid4()),
        )

    # Inférence CamemBERT-QA (blocking ML call → thread)
    qa_result = await asyncio.to_thread(answer_question, request.question, context_chunks)

    # Générer ou réutiliser le session_id
    session_id = request.session_id or str(uuid.uuid4())

    # Sauvegarder l'échange en base
    exchange = {
        "question": request.question,
        "answer": qa_result["answer"],
        "confidence": qa_result["confidence"],
        "timestamp": datetime.now(timezone.utc),
        "sources": qa_result["sources"],
    }
    await save_qa_exchange(session_id, request.course_id, exchange)

    return AnswerResponse(
        answer=qa_result["answer"],
        confidence=qa_result["confidence"],
        sources=[
            SourceDocument(**s) for s in qa_result["sources"]
        ],
        session_id=session_id,
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
