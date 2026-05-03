"""Router pour les résumés automatiques par chapitre."""

import asyncio
import logging
from typing import Set

from fastapi import APIRouter, HTTPException, Depends

from backend.config import get_settings
from backend.models.schemas import (
    SummaryResponse,
    ChapterSummary,
    PipelineMeta,
    PipelineStep,
)
from backend.database.mongodb import (
    get_course_by_id,
    get_chunks_by_course,
    get_cached_summary,
    save_cached_summary,
)
from backend.services.summarizer import summarize_course
from backend.services.llm_summarizer import refine_chapter
from backend.services.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Track which courses are currently being generated (to avoid duplicate work)
_generating: Set[str] = set()
_gen_lock = asyncio.Lock()


def _build_pipeline_meta(any_llm: bool) -> PipelineMeta:
    """Décrit le pipeline NLP + Deep Learning + LLM réellement appliqué au cours.

    Cette métadonnée est exposée au frontend pour montrer (jury / utilisateur)
    que EduAI repose sur de vraies briques NLP et Deep Learning, pas seulement
    sur un appel LLM externe.
    """
    settings = get_settings()
    steps: list[PipelineStep] = [
        PipelineStep(
            name="Extraction & segmentation",
            family="NLP",
            model="PyMuPDF + chunker maison",
            detail=f"Découpage en passages de ≈{settings.chunk_size} tokens (overlap {settings.chunk_overlap}).",
        ),
        PipelineStep(
            name="Analyse linguistique",
            family="NLP",
            model="spaCy fr_core_news_lg",
            detail="Tokenisation, POS-tagging, lemmatisation, NER pour extraire les concepts clés.",
        ),
        PipelineStep(
            name="Embeddings sémantiques",
            family="Deep Learning",
            model=settings.embedding_model.split("/")[-1],
            detail="Encodeur Transformer multilingue (BERT distillé, 384-d) pour représenter le sens du texte.",
        ),
        PipelineStep(
            name="Indexation vectorielle",
            family="Deep Learning",
            model="FAISS (Facebook AI Similarity Search)",
            detail="Recherche de voisinage en haute dimension pour regrouper les passages sémantiquement proches.",
        ),
        PipelineStep(
            name="Résumé extractif",
            family="NLP",
            model="TextRank + scoring multi-critères",
            detail="Sélection des phrases les plus représentatives par chapitre (graph-based ranking).",
        ),
    ]
    llm_model = None
    if any_llm:
        if settings.llm_backend == "groq":
            llm_model = settings.groq_model
            steps.append(PipelineStep(
                name="Reformulation pédagogique",
                family="LLM",
                model=f"Groq · {llm_model}",
                detail="Réécriture narrative finale du résumé extractif (titre + corps + concepts).",
            ))
        else:
            llm_model = settings.ollama_model
            steps.append(PipelineStep(
                name="Reformulation pédagogique",
                family="LLM",
                model=f"Ollama · {llm_model}",
                detail="Réécriture narrative finale du résumé extractif (titre + corps + concepts).",
            ))
    return PipelineMeta(
        steps=steps,
        llm_backend=settings.llm_backend if any_llm else "none",
        llm_model=llm_model,
    )


def _chapter_techniques(llm_used: bool) -> list[str]:
    """Liste compacte des techniques appliquées à ce chapitre (pour badges UI)."""
    techs = ["spaCy NLP", "BERT embeddings", "FAISS", "TextRank"]
    if llm_used:
        techs.append("LLM refined")
    return techs


async def _generate_in_background(course_id: str, chunks: list) -> None:
    """Génère les résumés en arrière-plan : extractif puis raffinement LLM par chapitre."""
    try:
        logger.info("Début de la génération en arrière-plan pour le cours %s", course_id)
        # ── Étape 1 : pipeline extractif (rapide, robuste, fallback garanti) ──
        summaries = await asyncio.to_thread(summarize_course, chunks)

        # ── Étape 2 : raffinement LLM par chapitre (séquentiel pour ne pas
        #            saturer la RAM/CPU et garantir l'ordre des logs).
        #            Le LLM produit titre + corps + concepts en 1 appel ──
        for s in summaries:
            extractive_title = s["title"]
            try:
                refined = await refine_chapter(
                    title=extractive_title,
                    bullets=s["summary"],
                    key_concepts=s.get("key_concepts", []) or [],
                )
            except Exception:
                logger.exception("LLM refine_chapter a échoué pour '%s'", extractive_title)
                refined = None

            if refined and refined.get("body"):
                s["pedagogic"] = refined["body"]
                s["llm_used"] = True
                # Override des champs extractifs pollués (titres = 1ère phrase, concepts = bruit Wikidata)
                if refined.get("title"):
                    s["title"] = refined["title"]
                if refined.get("key_concepts"):
                    s["key_concepts"] = refined["key_concepts"]
                logger.info(
                    "LLM ✓ '%s' → '%s' (%d c., %d concepts)",
                    extractive_title[:40],
                    s["title"],
                    len(refined["body"]),
                    len(s["key_concepts"]),
                )
            else:
                s["pedagogic"] = None
                s["llm_used"] = False
                logger.info("LLM ✗ chapitre '%s' (fallback extractif)", extractive_title)

        chapters_data = [
            {
                "title": s["title"],
                "summary": s["summary"],
                "pages": s["pages"],
                "key_concepts": s["key_concepts"],
                "pedagogic": s.get("pedagogic"),
                "llm_used": s.get("llm_used", False),
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


async def pregenerate_summary_in_background(course_id: str) -> None:
    """À appeler depuis le pipeline d'upload : pré-génère la fiche."""
    async with _gen_lock:
        if course_id in _generating:
            return
        _generating.add(course_id)
    try:
        cached = await get_cached_summary(course_id)
        if cached:
            async with _gen_lock:
                _generating.discard(course_id)
            return
        chunks = await get_chunks_by_course(course_id)
        if not chunks:
            logger.warning("Pas de chunks pour pré-générer la fiche de %s", course_id)
            async with _gen_lock:
                _generating.discard(course_id)
            return
        # _generate_in_background s'occupe lui-même du discard dans son finally.
        await _generate_in_background(course_id, chunks)
    except Exception:
        logger.exception("Erreur pré-génération fiche pour %s", course_id)
        async with _gen_lock:
            _generating.discard(course_id)


@router.get("/{course_id}", response_model=SummaryResponse)
async def get_summary(course_id: str, current_user: dict = Depends(get_current_user)):
    """Renvoie les résumés depuis le cache, ou lance la génération en arrière-plan."""
    course = await get_course_by_id(course_id, user_id=current_user["user_id"])
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    # ── Cache : retourner immédiatement si déjà généré ──
    cached = await get_cached_summary(course_id)
    if cached:
        logger.info("Résumés servis depuis le cache pour le cours %s", course_id)
        chapters = [ChapterSummary(**ch) for ch in cached["chapters"]]
        # Enrichit chaque chapitre avec ses techniques (pour badges UI)
        for ch in chapters:
            if not ch.techniques:
                ch.techniques = _chapter_techniques(ch.llm_used)
        any_llm = any(c.llm_used for c in chapters)
        return SummaryResponse(
            course_id=course_id,
            status="ready",
            chapters=chapters,
            llm_enabled=any_llm,
            pipeline_meta=_build_pipeline_meta(any_llm),
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
        llm_enabled=False,
        pipeline_meta=_build_pipeline_meta(any_llm=True),
    )
