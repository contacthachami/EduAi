"""Router pour la gestion des cours (upload, liste, détail, suppression)."""

import asyncio
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from backend.config import get_settings
from backend.models.schemas import CourseUploadResponse, CourseInfo, CourseDetail
from backend.database.mongodb import (
    insert_course, get_all_courses, get_course_by_id,
    delete_course_by_id, insert_chunks, get_chunks_by_course,
    update_course_status,
)
from backend.services.pdf_extractor import extract_pdf, get_total_pages
from backend.services.chunker import create_chunks
from backend.services.embedder import embed_texts
from backend.services.retriever import create_index, delete_index
from backend.services.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Track courses currently being (re-)indexed to avoid duplicate work
_indexing: set[str] = set()
_indexing_lock = asyncio.Lock()


async def _index_in_background(course_id: str, texts: list[str]) -> None:
    """Génère les embeddings, crée l'index FAISS, puis lance la pré-génération
    de la fiche pédagogique et du quiz par défaut en arrière-plan."""
    try:
        logger.info("Indexation en arrière-plan pour %s (%d chunks)…", course_id, len(texts))
        embeddings = await asyncio.to_thread(embed_texts, texts)
        await asyncio.to_thread(create_index, course_id, embeddings)
        await update_course_status(course_id, "ready")
        logger.info("Indexation terminée pour le cours %s", course_id)

        # ── Pré-génération LLM (fiche + quiz) en background ──
        try:
            from backend.routers.summary import pregenerate_summary_in_background
            from backend.routers.quiz import pregenerate_quiz_in_background
            asyncio.create_task(pregenerate_summary_in_background(course_id))
            asyncio.create_task(pregenerate_quiz_in_background(course_id))
            logger.info("Pré-génération fiche+quiz lancée pour %s", course_id)
        except Exception:
            logger.exception("Impossible de lancer la pré-génération LLM pour %s", course_id)
    except Exception:
        logger.exception("Erreur lors de l'indexation du cours %s", course_id)
        await update_course_status(course_id, "error")
    finally:
        async with _indexing_lock:
            _indexing.discard(course_id)


@router.post("/upload", response_model=CourseUploadResponse)
async def upload_course(
    file: UploadFile = File(...),
    course_name: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload un PDF de cours → extraction → chunking → indexation FAISS."""
    settings = get_settings()
    user_id = current_user["user_id"]

    # ── Vérifier quota selon le plan de l'utilisateur ──────────────────────
    from backend.database.mongodb import get_db
    from bson import ObjectId
    db = get_db()
    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    user_plan = user_doc.get("plan", "free") if user_doc else "free"

    if user_plan != "pro":
        # Plan gratuit : maximum 3 cours à vie
        FREE_PLAN_LIMIT = 3
        user_courses_count = await db.courses.count_documents({"user_id": user_id})
        if user_courses_count >= FREE_PLAN_LIMIT:
            raise HTTPException(
                status_code=403,
                detail="UPGRADE_REQUIRED",
            )

    # Validation du fichier
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Seuls les fichiers PDF sont acceptés.")

    file_bytes = await file.read()

    # Vérifier la taille
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_pdf_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux ({size_mb:.1f} MB). Maximum : {settings.max_pdf_size_mb} MB.",
        )

    # Extraction du texte
    try:
        page_blocks = extract_pdf(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    total_pages = get_total_pages(file_bytes)

    # Chunking
    chunks = create_chunks(page_blocks, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise HTTPException(status_code=422, detail="Aucun contenu extractible trouvé dans le PDF.")

    # Détecter les chapitres
    chapters = list({c["chapter"] for c in chunks})

    # Sauvegarder le cours dans MongoDB (statut "processing" d'abord)
    course_data = {
        "user_id": user_id,
        "name": course_name,
        "filename": file.filename,
        "created_at": datetime.now(timezone.utc),
        "chunks_count": len(chunks),
        "pages": total_pages,
        "chapters": chapters,
        "status": "processing",
    }
    course_id = await insert_course(course_data)

    # Sauvegarder les chunks dans MongoDB
    chunk_docs = [
        {
            "course_id": course_id,
            "text": c["text"],
            "page": c["page"],
            "chapter": c["chapter"],
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]
    await insert_chunks(chunk_docs)

    # Lancer l'indexation en arrière-plan (embeddings + FAISS)
    texts = [c["text"] for c in chunks]
    async with _indexing_lock:
        _indexing.add(course_id)
    asyncio.create_task(_index_in_background(course_id, texts))

    logger.info("Cours uploadé : '%s' — %d chunks, %d pages (indexation en cours)", course_name, len(chunks), total_pages)

    return CourseUploadResponse(
        course_id=course_id,
        course_name=course_name,
        chunks_count=len(chunks),
        pages_count=total_pages,
        status="processing",
    )


@router.get("", response_model=list[CourseInfo])
async def list_courses(current_user: dict = Depends(get_current_user)):
    """Liste tous les cours de l'utilisateur."""
    courses = await get_all_courses(user_id=current_user["user_id"])
    return [
        CourseInfo(
            id=c["id"],
            name=c["name"],
            created_at=c["created_at"],
            chunks_count=c.get("chunks_count", 0),
            pages=c.get("pages", 0),
        )
        for c in courses
    ]


@router.get("/{course_id}", response_model=CourseDetail)
async def get_course(course_id: str, current_user: dict = Depends(get_current_user)):
    """Détail d'un cours spécifique."""
    course = await get_course_by_id(course_id, user_id=current_user["user_id"])
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    # Recovery: if stuck in "processing" (e.g. server restart killed the task)
    if course.get("status") == "processing":
        settings = get_settings()
        faiss_path = os.path.join(settings.faiss_index_dir, f"{course_id}.faiss")
        if os.path.exists(faiss_path):
            # Index already exists on disk — just update status
            await update_course_status(course_id, "ready")
            course["status"] = "ready"
            logger.info("Recovery: cours %s marqué 'ready' (index existant).", course_id)
        else:
            # Re-trigger indexation if not already running
            async with _indexing_lock:
                already_running = course_id in _indexing
                if not already_running:
                    _indexing.add(course_id)
            if not already_running:
                chunks_db = await get_chunks_by_course(course_id)
                if chunks_db:
                    texts = [c["text"] for c in chunks_db]
                    asyncio.create_task(_index_in_background(course_id, texts))
                    logger.info("Recovery: relance indexation pour %s (%d chunks).", course_id, len(texts))

    return CourseDetail(
        id=course["id"],
        name=course["name"],
        created_at=course["created_at"],
        chunks_count=course.get("chunks_count", 0),
        pages=course.get("pages", 0),
        chapters=course.get("chapters", []),
        status=course.get("status", "ready"),
    )


@router.delete("/{course_id}")
async def delete_course(course_id: str, current_user: dict = Depends(get_current_user)):
    """Supprime un cours et son index FAISS."""
    deleted = await delete_course_by_id(course_id, user_id=current_user["user_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Cours introuvable.")
    try:
        delete_index(course_id)
    except Exception:
        pass  # L'index peut ne pas exister
    return {"status": "deleted"}


@router.get("/{course_id}/status")
async def get_course_content_status(course_id: str, current_user: dict = Depends(get_current_user)):
    """Indique l'état de génération des contenus IA (fiche, quiz) pour un cours."""
    from backend.database.mongodb import get_cached_summary, get_cached_course_quiz
    course = await get_course_by_id(course_id, user_id=current_user["user_id"])
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")
    cached_summary = await get_cached_summary(course_id)
    cached_quiz = await get_cached_course_quiz(course_id)
    return {
        "course_id": course_id,
        "indexed": course.get("status") == "ready",
        "summary_ready": cached_summary is not None,
        "quiz_ready": cached_quiz is not None,
    }
