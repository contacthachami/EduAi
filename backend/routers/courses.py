"""Router pour la gestion des cours (upload, liste, détail, suppression)."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.config import get_settings
from backend.models.schemas import CourseUploadResponse, CourseInfo, CourseDetail
from backend.database.mongodb import (
    insert_course, get_all_courses, get_course_by_id,
    delete_course_by_id, insert_chunks, get_chunks_by_course,
)
from backend.services.pdf_extractor import extract_pdf, get_total_pages
from backend.services.chunker import create_chunks
from backend.services.embedder import embed_texts
from backend.services.retriever import create_index, delete_index

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=CourseUploadResponse)
async def upload_course(
    file: UploadFile = File(...),
    course_name: str = Form(...),
):
    """Upload un PDF de cours → extraction → chunking → indexation FAISS."""
    settings = get_settings()

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

    # Sauvegarder le cours dans MongoDB
    course_data = {
        "name": course_name,
        "filename": file.filename,
        "created_at": datetime.now(timezone.utc),
        "chunks_count": len(chunks),
        "pages": total_pages,
        "chapters": chapters,
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

    # Générer les embeddings et indexer dans FAISS
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    create_index(course_id, embeddings)

    logger.info("Cours uploadé : '%s' — %d chunks, %d pages", course_name, len(chunks), total_pages)

    return CourseUploadResponse(
        course_id=course_id,
        course_name=course_name,
        chunks_count=len(chunks),
        pages_count=total_pages,
        status="indexé",
    )


@router.get("", response_model=list[CourseInfo])
async def list_courses():
    """Liste tous les cours disponibles."""
    courses = await get_all_courses()
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
async def get_course(course_id: str):
    """Détail d'un cours spécifique."""
    course = await get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")
    return CourseDetail(
        id=course["id"],
        name=course["name"],
        created_at=course["created_at"],
        chunks_count=course.get("chunks_count", 0),
        pages=course.get("pages", 0),
        chapters=course.get("chapters", []),
    )


@router.delete("/{course_id}")
async def delete_course(course_id: str):
    """Supprime un cours et son index FAISS."""
    deleted = await delete_course_by_id(course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cours introuvable.")
    try:
        delete_index(course_id)
    except Exception:
        pass  # L'index peut ne pas exister
    return {"status": "deleted"}
