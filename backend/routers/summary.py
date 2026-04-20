"""Router pour les résumés automatiques par chapitre."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from backend.models.schemas import SummaryResponse, ChapterSummary
from backend.database.mongodb import get_course_by_id, get_chunks_by_course
from backend.services.summarizer import summarize_course

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{course_id}", response_model=SummaryResponse)
async def get_summary(course_id: str):
    """Génère les résumés de tous les chapitres d'un cours."""
    # Vérifier que le cours existe
    course = await get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    # Récupérer les chunks
    chunks = await get_chunks_by_course(course_id)
    if not chunks:
        raise HTTPException(status_code=503, detail="Cours pas encore indexé.")

    # Générer les résumés dans un thread pour ne pas bloquer l'event loop
    summaries = await asyncio.to_thread(summarize_course, chunks)

    return SummaryResponse(
        course_id=course_id,
        chapters=[
            ChapterSummary(
                title=s["title"],
                summary=s["summary"],
                pages=s["pages"],
                key_concepts=s["key_concepts"],
            )
            for s in summaries
        ],
    )
