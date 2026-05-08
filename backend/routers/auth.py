"""Router d'authentification — inscription, connexion, profil, réinitialisation."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field

from backend.database.mongodb import get_db
from backend.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter()


# ── Schémas ─────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: Dict[str, Any]


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime
    plan: str
    courses_count: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=128)


# ── Endpoints ───────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(req: RegisterRequest):
    """Créer un nouveau compte étudiant."""
    db = get_db()

    # Vérifier unicité email
    existing = await db.users.find_one({"email": req.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà.",
        )

    user_doc = {
        "name": req.name.strip(),
        "email": req.email.lower(),
        "password_hash": hash_password(req.password),
        "plan": "free",
        "role": "user",
        "created_at": datetime.now(timezone.utc),
        "settings": {
            "daily_goal_minutes": 30,
            "reminder_enabled": False,
        },
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    token = create_access_token(user_id, user_doc["email"])
    return AuthResponse(
        token=token,
        user={
            "id": user_id,
            "name": user_doc["name"],
            "email": user_doc["email"],
            "plan": user_doc["plan"],
            "role": user_doc["role"],
        },
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Se connecter avec email + mot de passe."""
    db = get_db()
    user = await db.users.find_one({"email": req.email.lower()})

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    user_id = str(user["_id"])
    token = create_access_token(user_id, user["email"])

    return AuthResponse(
        token=token,
        user={
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
            "plan": user.get("plan", "free"),
            "role": user.get("role", "user"),
        },
    )


@router.get("/me", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Récupérer le profil de l'utilisateur connecté."""
    from bson import ObjectId

    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    courses_count = await db.courses.count_documents({"user_id": current_user["user_id"]})

    return UserProfile(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        role=user.get("role", "user"),
        created_at=user["created_at"],
        plan=user.get("plan", "free"),
        courses_count=courses_count,
    )


# ── Mot de passe oublié ─────────────────────────────

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Demander la réinitialisation du mot de passe.
    
    Génère un token de réinitialisation valable 1 heure.
    En production, ce token serait envoyé par email.
    """
    db = get_db()
    user = await db.users.find_one({"email": req.email.lower()})

    # Anti-énumération : toujours retourner un succès, même si l'email n'existe pas
    if not user:
        return {
            "message": "Si cet email est enregistré, un lien de réinitialisation a été généré.",
            "reset_link": None,
        }

    # Invalider les anciens tokens non utilisés
    await db.password_resets.update_many(
        {"email": req.email.lower(), "used": False},
        {"$set": {"used": True}},
    )

    token = secrets.token_urlsafe(32)
    await db.password_resets.insert_one({
        "user_id": str(user["_id"]),
        "email": req.email.lower(),
        "token": token,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used": False,
    })

    reset_link = f"/auth/reset-password?token={token}"
    return {
        "message": "Lien de réinitialisation généré.",
        "reset_link": reset_link,
    }


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """Réinitialiser le mot de passe avec un token valide."""
    db = get_db()

    reset_doc = await db.password_resets.find_one({
        "token": req.token,
        "used": False,
    })

    if not reset_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalide ou déjà utilisé.",
        )

    now = datetime.now(timezone.utc)
    if reset_doc["expires_at"].replace(tzinfo=timezone.utc) < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce lien a expiré. Veuillez en demander un nouveau.",
        )

    from bson import ObjectId
    await db.users.update_one(
        {"_id": ObjectId(reset_doc["user_id"])},
        {"$set": {"password_hash": hash_password(req.new_password)}},
    )
    await db.password_resets.update_one(
        {"_id": reset_doc["_id"]},
        {"$set": {"used": True}},
    )

    return {"message": "Mot de passe réinitialisé avec succès."}
