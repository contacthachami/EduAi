"""Router pour les résumés automatiques par chapitre."""

import asyncio
import logging
from typing import Set

from fastapi import APIRouter, HTTPException

from backend.models.schemas import SummaryResponse, ChapterSummary
from backend.database.mongodb import (
    get_course_by_id,
    get_chunks_by_course,
    get_cached_summary,
    save_cached_summary,
)
from backend.services.summarizer import summarize_course

logger = logging.getLogger(__name__)
router = APIRouter()

# Track which courses are currently being generated (to avoid duplicate work)
_generating: Set[str] = set()
_gen_lock = asyncio.Lock()


async def _generate_in_background(course_id: str, chunks: list) -> None:
    """Génère les résumés en arrière-plan et les sauvegarde en cache."""
    try:
        logger.info("Début de la génération en arrière-plan pour le cours %s", course_id)
        summaries = await asyncio.to_thread(summarize_course, chunks)

        chapters_data = [
            {
                "title": s["title"],
                "summary": s["summary"],
                "pages": s["pages"],
                "key_concepts": s["key_concepts"],
            }
            for s in summaries
        ]
        await save_cached_summary(course_id, chapters_data)
        logger.info("Résumés générés et mis en cache pour le cours %s", course_id)
    except Exception:
        logger.exception("Erreur lors de la génération des résumés pour %s", course_id)
    finally:
        async with _gen_lock:
            _generating.discard(course_id)


@router.get("/{course_id}", response_model=SummaryResponse)
async def get_summary(course_id: str):
    """Renvoie les résumés depuis le cache, ou lance la génération en arrière-plan."""
    # Vérifier que le cours existe
    course = await get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    # ── Cache : retourner immédiatement si déjà généré ──
    cached = await get_cached_summary(course_id)
    if cached:
        logger.info("Résumés servis depuis le cache pour le cours %s", course_id)
        return SummaryResponse(
            course_id=course_id,
            status="ready",
            chapters=[ChapterSummary(**ch) for ch in cached["chapters"]],
        )

    # ── Pas en cache : lancer la génération en arrière-plan ──
    async with _gen_lock:
        already_running = course_id in _generating
        if not already_running:
            _generating.add(course_id)

    if not already_running:
        chunks = await get_chunks_by_course(course_id)
        if not chunks:
            async with _gen_lock:
                _generating.discard(course_id)
            raise HTTPException(status_code=503, detail="Cours pas encore indexé.")
        # Fire-and-forget background task
        asyncio.create_task(_generate_in_background(course_id, chunks))

    return SummaryResponse(
        course_id=course_id,
        status="generating",
        chapters=[],
    )
