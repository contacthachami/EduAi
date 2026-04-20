"""Connexion MongoDB asynchrone avec Motor + helpers CRUD."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.config import get_settings
import logging

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Initialise la connexion MongoDB."""
    global _client, _db
    settings = get_settings()
    try:
        _client = AsyncIOMotorClient(settings.mongodb_url)
        _db = _client[settings.mongodb_db_name]
        # Test la connexion
        await _client.admin.command("ping")
        logger.info("Connexion MongoDB établie — base : %s", settings.mongodb_db_name)
    except Exception as e:
        logger.error("Erreur connexion MongoDB : %s", e)
        raise


async def close_db() -> None:
    """Ferme proprement la connexion MongoDB."""
    global _client
    if _client:
        _client.close()
        logger.info("Connexion MongoDB fermée.")


def get_db() -> AsyncIOMotorDatabase:
    """Retourne l'instance de la base de données."""
    if _db is None:
        raise RuntimeError("Base de données non initialisée. Appelez connect_db() d'abord.")
    return _db


# ── Helpers CRUD ────────────────────────────────────

async def insert_course(course_data: dict) -> str:
    db = get_db()
    result = await db.courses.insert_one(course_data)
    return str(result.inserted_id)


async def get_all_courses() -> list:
    db = get_db()
    cursor = db.courses.find({}, {"_id": 1, "name": 1, "created_at": 1, "chunks_count": 1, "pages": 1})
    courses = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        courses.append(doc)
    return courses


async def get_course_by_id(course_id: str) -> dict | None:
    from bson import ObjectId
    db = get_db()
    try:
        doc = await db.courses.find_one({"_id": ObjectId(course_id)})
    except Exception:
        return None
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


async def delete_course_by_id(course_id: str) -> bool:
    from bson import ObjectId
    db = get_db()
    try:
        result = await db.courses.delete_one({"_id": ObjectId(course_id)})
        # Supprimer aussi les chunks associés
        await db.chunks.delete_many({"course_id": course_id})
        # Supprimer les sessions QA
        await db.qa_sessions.delete_many({"course_id": course_id})
        # Supprimer les résumés en cache
        await db.summaries.delete_many({"course_id": course_id})
        return result.deleted_count > 0
    except Exception:
        return False


async def insert_chunks(chunks: list[dict]) -> None:
    db = get_db()
    if chunks:
        await db.chunks.insert_many(chunks)


async def get_chunks_by_course(course_id: str) -> list[dict]:
    db = get_db()
    cursor = db.chunks.find({"course_id": course_id})
    return await cursor.to_list(length=None)


async def save_qa_exchange(session_id: str, course_id: str, exchange: dict) -> None:
    db = get_db()
    await db.qa_sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {"course_id": course_id},
            "$push": {"exchanges": exchange},
        },
        upsert=True,
    )


async def get_qa_history(session_id: str) -> list[dict]:
    db = get_db()
    doc = await db.qa_sessions.find_one({"session_id": session_id})
    if doc:
        return doc.get("exchanges", [])
    return []


async def get_cached_summary(course_id: str) -> dict | None:
    """Récupère les résumés mis en cache pour un cours."""
    db = get_db()
    return await db.summaries.find_one({"course_id": course_id})


async def save_cached_summary(course_id: str, chapters: list[dict]) -> None:
    """Sauvegarde les résumés générés en cache."""
    from datetime import datetime, timezone
    db = get_db()
    await db.summaries.replace_one(
        {"course_id": course_id},
        {"course_id": course_id, "chapters": chapters, "created_at": datetime.now(timezone.utc)},
        upsert=True,
    )


async def delete_cached_summary(course_id: str) -> None:
    """Supprime le cache de résumés pour un cours."""
    db = get_db()
    await db.summaries.delete_many({"course_id": course_id})


async def update_course_status(course_id: str, status: str) -> None:
    """Met à jour le statut d'un cours (processing / ready)."""
    from bson import ObjectId
    db = get_db()
    await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": {"status": status}},
    )


async def save_quiz(quiz_data: dict) -> None:
    db = get_db()
    await db.quizzes.insert_one(quiz_data)


async def get_quiz(quiz_id: str) -> dict | None:
    db = get_db()
    return await db.quizzes.find_one({"quiz_id": quiz_id})
