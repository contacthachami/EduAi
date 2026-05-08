"""Router Admin — Gestion CRUD des comptes utilisateurs (admin uniquement)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field

from backend.database.mongodb import get_db
from backend.services.auth import hash_password, get_current_user

router = APIRouter()


# ── Garde admin ────────────────────────────────────────────────────────────────

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dépendance FastAPI : vérifie que l'utilisateur connecté est admin."""
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user or user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé à l'administrateur.",
        )
    return current_user


# ── Schémas ────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    plan: str
    created_at: datetime
    courses_count: int = 0


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="user")
    plan: str = Field(default="free")


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    role: Optional[str] = None
    plan: Optional[str] = None


# ── Helper ─────────────────────────────────────────────────────────────────────

async def _user_out(user: dict) -> UserOut:
    db = get_db()
    uid = str(user["_id"])
    courses_count = await db.courses.count_documents({"user_id": uid})
    return UserOut(
        id=uid,
        name=user.get("name", ""),
        email=user.get("email", ""),
        role=user.get("role", "user"),
        plan=user.get("plan", "free"),
        created_at=user.get("created_at", datetime.now(timezone.utc)),
        courses_count=courses_count,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserOut])
async def list_users(_: dict = Depends(require_admin)):
    """Lister tous les comptes (triés par date de création, plus récent en premier)."""
    db = get_db()
    cursor = db.users.find({}).sort("created_at", -1)
    users = await cursor.to_list(length=500)
    return [await _user_out(u) for u in users]


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(req: CreateUserRequest, _: dict = Depends(require_admin)):
    """Créer un nouveau compte utilisateur."""
    db = get_db()
    existing = await db.users.find_one({"email": req.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà.",
        )
    doc: Dict[str, Any] = {
        "name": req.name.strip(),
        "email": req.email.lower(),
        "password_hash": hash_password(req.password),
        "role": req.role if req.role in ("admin", "user") else "user",
        "plan": req.plan if req.plan in ("free", "pro") else "free",
        "created_at": datetime.now(timezone.utc),
        "settings": {"daily_goal_minutes": 30, "reminder_enabled": False},
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return await _user_out(doc)


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    req: UpdateUserRequest,
    _: dict = Depends(require_admin),
):
    """Modifier les informations d'un compte (nom, email, mot de passe, rôle)."""
    db = get_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=422, detail="user_id invalide.")

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    updates: Dict[str, Any] = {}
    if req.name is not None:
        updates["name"] = req.name.strip()
    if req.email is not None:
        lower = req.email.lower()
        conflict = await db.users.find_one({"email": lower, "_id": {"$ne": oid}})
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cet email est déjà utilisé par un autre compte.",
            )
        updates["email"] = lower
    if req.password is not None:
        updates["password_hash"] = hash_password(req.password)
    if req.role is not None and req.role in ("admin", "user"):
        updates["role"] = req.role
    if req.plan is not None and req.plan in ("free", "pro"):
        updates["plan"] = req.plan

    if updates:
        await db.users.update_one({"_id": oid}, {"$set": updates})

    updated = await db.users.find_one({"_id": oid})
    return await _user_out(updated)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    """Supprimer un compte et toutes ses données (cours, chunks, caches)."""
    db = get_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=422, detail="user_id invalide.")

    if admin["user_id"] == user_id:
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer votre propre compte admin.",
        )

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    # Suppression en cascade de toutes les données de l'utilisateur
    course_cursor = db.courses.find({"user_id": user_id}, {"_id": 1})
    courses = await course_cursor.to_list(length=None)
    course_ids = [str(c["_id"]) for c in courses]

    for cid in course_ids:
        await db.chunks.delete_many({"course_id": cid})
        await db.summaries.delete_many({"course_id": cid})
        await db.quiz_cache.delete_many({"course_id": cid})
        await db.flashcards.delete_many({"course_id": cid})
        await db.exam_sessions.delete_many({"course_id": cid})

    await db.courses.delete_many({"user_id": user_id})
    await db.password_resets.delete_many({"user_id": user_id})
    await db.users.delete_one({"_id": oid})


@router.get("/stats")
async def get_stats(_: dict = Depends(require_admin)):
    """Statistiques globales de la plateforme."""
    db = get_db()
    total_users = await db.users.count_documents({})
    total_courses = await db.courses.count_documents({})
    total_chunks = await db.chunks.count_documents({})
    admin_count = await db.users.count_documents({"role": "admin"})
    return {
        "total_users": total_users,
        "total_courses": total_courses,
        "total_chunks": total_chunks,
        "admin_count": admin_count,
    }
