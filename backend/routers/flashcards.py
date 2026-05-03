"""Router Flashcards — Génération + Révision espacée (SM-2)."""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.database.mongodb import get_db
from backend.services.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schémas ─────────────────────────────────────────

class Flashcard(BaseModel):
    id: str
    course_id: str
    front: str
    back: str
    difficulty: str = "moyen"  # facile, moyen, difficile
    # SM-2 fields
    interval: int = 1  # jours
    repetitions: int = 0
    ease_factor: float = 2.5
    next_review: Optional[datetime] = None


class FlashcardGenerateRequest(BaseModel):
    course_id: str
    count: int = Field(default=10, ge=3, le=30)


class FlashcardReviewRequest(BaseModel):
    flashcard_id: str
    quality: int = Field(..., ge=0, le=5)  # 0=oubli total, 5=parfait


class FlashcardDeckResponse(BaseModel):
    course_id: str
    course_name: str
    total: int
    due_today: int
    cards: List[Flashcard]


class ReviewSessionResponse(BaseModel):
    cards_due: List[Flashcard]
    total_due: int


# ── Endpoints ───────────────────────────────────────

@router.post("/generate", response_model=FlashcardDeckResponse)
async def generate_flashcards(
    req: FlashcardGenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Générer des flashcards depuis le contenu d'un cours via LLM."""
    from bson import ObjectId
    db = get_db()
    user_id = current_user["user_id"]

    # Vérifier que le cours existe et appartient à l'utilisateur
    course = await db.courses.find_one({"_id": ObjectId(req.course_id), "user_id": user_id})
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    # Récupérer les chunks du cours
    chunks = await db.chunks.find({"course_id": req.course_id}).to_list(length=None)
    if not chunks:
        raise HTTPException(status_code=400, detail="Aucun contenu indexé pour ce cours.")

    # Générer via LLM
    from backend.services.llm_flashcards import generate_flashcards_from_chunks
    cards_data = await generate_flashcards_from_chunks(chunks, req.count)

    # Sauvegarder en base
    now = datetime.now(timezone.utc)
    docs = []
    for card in cards_data:
        docs.append({
            "user_id": user_id,
            "course_id": req.course_id,
            "front": card["front"],
            "back": card["back"],
            "difficulty": card.get("difficulty", "moyen"),
            "interval": 1,
            "repetitions": 0,
            "ease_factor": 2.5,
            "next_review": now,
            "created_at": now,
        })

    if docs:
        await db.flashcards.insert_many(docs)

    # Retourner le deck
    total = await db.flashcards.count_documents({"user_id": user_id, "course_id": req.course_id})
    due = await db.flashcards.count_documents({
        "user_id": user_id, "course_id": req.course_id,
        "next_review": {"$lte": now},
    })

    return FlashcardDeckResponse(
        course_id=req.course_id,
        course_name=course["name"],
        total=total,
        due_today=due,
        cards=[_doc_to_flashcard(d) for d in docs],
    )


@router.get("/deck/{course_id}", response_model=FlashcardDeckResponse)
async def get_deck(course_id: str, current_user: dict = Depends(get_current_user)):
    """Récupérer le deck de flashcards d'un cours."""
    from bson import ObjectId
    db = get_db()
    user_id = current_user["user_id"]

    course = await db.courses.find_one({"_id": ObjectId(course_id), "user_id": user_id})
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    now = datetime.now(timezone.utc)
    all_cards = await db.flashcards.find(
        {"user_id": user_id, "course_id": course_id}
    ).to_list(length=None)

    due = [c for c in all_cards if _ensure_utc(c.get("next_review", now)) <= now]

    return FlashcardDeckResponse(
        course_id=course_id,
        course_name=course["name"],
        total=len(all_cards),
        due_today=len(due),
        cards=[_doc_to_flashcard(d) for d in all_cards],
    )


@router.get("/review/{course_id}", response_model=ReviewSessionResponse)
async def get_review_session(course_id: str, current_user: dict = Depends(get_current_user)):
    """Récupérer les cartes dues pour révision."""
    db = get_db()
    user_id = current_user["user_id"]
    now = datetime.now(timezone.utc)

    due_cards = await db.flashcards.find({
        "user_id": user_id,
        "course_id": course_id,
        "next_review": {"$lte": now},
    }).to_list(length=50)

    return ReviewSessionResponse(
        cards_due=[_doc_to_flashcard(d) for d in due_cards],
        total_due=len(due_cards),
    )


@router.post("/review")
async def submit_review(
    req: FlashcardReviewRequest,
    current_user: dict = Depends(get_current_user),
):
    """Soumettre le résultat d'une révision (algorithme SM-2)."""
    from bson import ObjectId
    db = get_db()
    user_id = current_user["user_id"]

    card = await db.flashcards.find_one({
        "_id": ObjectId(req.flashcard_id),
        "user_id": user_id,
    })
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard introuvable.")

    # Algorithme SM-2
    new_interval, new_reps, new_ef = _sm2(
        quality=req.quality,
        repetitions=card.get("repetitions", 0),
        ease_factor=card.get("ease_factor", 2.5),
        interval=card.get("interval", 1),
    )

    now = datetime.now(timezone.utc)
    next_review = now + timedelta(days=new_interval)

    await db.flashcards.update_one(
        {"_id": ObjectId(req.flashcard_id)},
        {"$set": {
            "interval": new_interval,
            "repetitions": new_reps,
            "ease_factor": new_ef,
            "next_review": next_review,
        }},
    )

    # Log la review pour analytics
    await db.flashcard_reviews.insert_one({
        "user_id": user_id,
        "course_id": card["course_id"],
        "flashcard_id": req.flashcard_id,
        "quality": req.quality,
        "reviewed_at": now,
    })

    return {
        "ok": True,
        "next_review": next_review.isoformat(),
        "interval_days": new_interval,
        "ease_factor": round(new_ef, 2),
    }


@router.delete("/deck/{course_id}")
async def delete_deck(course_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer toutes les flashcards d'un cours."""
    db = get_db()
    user_id = current_user["user_id"]
    result = await db.flashcards.delete_many({"user_id": user_id, "course_id": course_id})
    return {"deleted": result.deleted_count}


# ── SM-2 Algorithm ──────────────────────────────────

def _sm2(quality: int, repetitions: int, ease_factor: float, interval: int) -> tuple:
    """Algorithme SuperMemo 2 pour la répétition espacée.
    
    quality: 0-5 (0=oubli total, 5=parfait)
    Retourne: (new_interval, new_repetitions, new_ease_factor)
    """
    if quality < 3:
        # Reset : la carte est oubliée
        return 1, 0, max(1.3, ease_factor - 0.2)
    else:
        # Bonne réponse
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)

        new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ef = max(1.3, new_ef)

        return new_interval, repetitions + 1, new_ef


# ── Helpers ─────────────────────────────────────────

def _ensure_utc(dt) -> datetime:
    """Return a timezone-aware UTC datetime; naive datetimes from MongoDB are assumed UTC."""
    if dt is None:
        return datetime.now(timezone.utc)
    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _doc_to_flashcard(doc: dict) -> Flashcard:
    return Flashcard(
        id=str(doc["_id"]) if "_id" in doc else "",
        course_id=doc["course_id"],
        front=doc["front"],
        back=doc["back"],
        difficulty=doc.get("difficulty", "moyen"),
        interval=doc.get("interval", 1),
        repetitions=doc.get("repetitions", 0),
        ease_factor=doc.get("ease_factor", 2.5),
        next_review=_ensure_utc(doc.get("next_review")),  # normalize to UTC-aware
    )
