"""Point d'entrée FastAPI — EduAI Backend.

Charge les modèles ML au démarrage, configure CORS,
enregistre les routers.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database.mongodb import connect_db, close_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Événements de démarrage et d'arrêt de l'application."""
    settings = get_settings()

    # Configurer le cache des modèles
    os.environ["HF_HOME"] = settings.hf_home
    os.environ["TRANSFORMERS_CACHE"] = settings.transformers_cache

    # Connexion MongoDB
    await connect_db()
    logger.info("MongoDB connecté.")

    # Les modèles ML sont chargés paresseusement (lazy) lors du premier appel API.
    # Évite les téléchargements bloquants au démarrage (~3 GB de modèles).
    logger.info("Démarrage en mode dev — modèles ML chargés à la demande.")

    yield

    # Nettoyage
    await close_db()
    logger.info("Application arrêtée proprement.")


app = FastAPI(
    title="EduAI — Assistant Pédagogique Intelligent",
    description="API REST pour l'assistant pédagogique basé sur RAG. "
                "Upload un PDF de cours, pose des questions, génère des résumés et des quiz.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrer les routers
from backend.routers import courses, qa, summary, quiz  # noqa: E402

app.include_router(courses.router, prefix="/api/courses", tags=["Cours"])
app.include_router(qa.router, prefix="/api/qa", tags=["Questions-Réponses"])
app.include_router(summary.router, prefix="/api/summary", tags=["Résumés"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])


@app.get("/", tags=["Santé"])
async def root():
    return {"status": "ok", "message": "EduAI API est en ligne."}


@app.get("/health", tags=["Santé"])
async def health_check():
    return {"status": "healthy"}
