"""Router Mind Map — Génération de cartes conceptuelles."""

from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.database.mongodb import get_db
from backend.services.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schémas ─────────────────────────────────────────

class MindMapNode(BaseModel):
    id: str
    label: str
    type: str = "concept"  # concept, chapter, detail
    chapter: Optional[str] = None


class MindMapEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = None


class MindMapResponse(BaseModel):
    course_id: str
    course_name: str
    nodes: List[MindMapNode]
    edges: List[MindMapEdge]


# ── Endpoints ───────────────────────────────────────

@router.get("/{course_id}", response_model=MindMapResponse)
async def get_mindmap(course_id: str, current_user: dict = Depends(get_current_user)):
    """Générer ou récupérer la mind map d'un cours."""
    from bson import ObjectId
    db = get_db()
    user_id = current_user["user_id"]

    course = await db.courses.find_one({"_id": ObjectId(course_id), "user_id": user_id})
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    # Vérifier le cache
    cached = await db.mindmaps.find_one({"course_id": course_id, "user_id": user_id})
    if cached:
        return MindMapResponse(
            course_id=course_id,
            course_name=course["name"],
            nodes=[MindMapNode(**n) for n in cached["nodes"]],
            edges=[MindMapEdge(**e) for e in cached["edges"]],
        )

    # Générer via LLM
    chunks = await db.chunks.find({"course_id": course_id}).to_list(length=None)
    if not chunks:
        raise HTTPException(status_code=400, detail="Aucun contenu indexé.")

    from backend.services.llm_mindmap import generate_mindmap
    nodes, edges = await generate_mindmap(chunks, course.get("chapters", []))

    # Sauvegarder en cache
    await db.mindmaps.replace_one(
        {"course_id": course_id, "user_id": user_id},
        {
            "course_id": course_id,
            "user_id": user_id,
            "nodes": [n.dict() for n in nodes],
            "edges": [e.dict() for e in edges],
        },
        upsert=True,
    )

    return MindMapResponse(
        course_id=course_id,
        course_name=course["name"],
        nodes=nodes,
        edges=edges,
    )


@router.delete("/{course_id}")
async def regenerate_mindmap(course_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer le cache pour forcer la régénération."""
    db = get_db()
    await db.mindmaps.delete_one({"course_id": course_id, "user_id": current_user["user_id"]})
    return {"ok": True, "message": "Mind map supprimée, sera regénérée au prochain appel."}
