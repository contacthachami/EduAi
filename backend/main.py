"""Point d'entrée FastAPI — EduAI Backend.

Charge les modèles ML au démarrage, configure CORS,
enregistre les routers.
"""

import os

# ── Désactiver les requêtes réseau HuggingFace (modèles déjà en cache local) ──
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import logging
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

    # Pré-charger le modèle d'embeddings (le plus utilisé : upload, Q&A)
    import asyncio
    logger.info("Pré-chargement du modèle d'embeddings…")
    from backend.services.embedder import embed_query
    await asyncio.to_thread(embed_query, "warmup")
    logger.info("Modèle d'embeddings prêt.")

    # Vérifier la disponibilité du LLM (Ollama) — non bloquant
    if settings.enable_llm:
        try:
            from backend.services.llm_client import get_client
            available = await get_client().is_available(force=True)
            if available:
                logger.info("LLM Ollama disponible (modèle: %s)", settings.ollama_model)
            else:
                logger.warning(
                    "LLM Ollama INDISPONIBLE (host=%s, model=%s). "
                    "Le système fonctionnera en mode extractif (fallback).",
                    settings.ollama_host, settings.ollama_model,
                )
        except Exception:
            logger.exception("Erreur lors du health-check LLM (mode fallback activé).")
    else:
        logger.info("LLM désactivé via ENABLE_LLM=False. Mode extractif uniquement.")

    # ── Pré-régénération des fiches manquantes (cache v2) en arrière-plan ──
    # Garantit que les cours déjà uploadés ont une fiche prête pour la démo
    # sans bloquer le démarrage du serveur.
    async def _warm_existing_summaries():
        try:
            from backend.database.mongodb import get_db
            from backend.routers.summary import pregenerate_summary_in_background

            db = get_db()
            cursor = db.courses.find({}, {"_id": 1, "filename": 1})
            courses = await cursor.to_list(length=None)
            if not courses:
                return

            logger.info(
                "Vérification des fiches pour %d cours existant(s)…",
                len(courses),
            )
            for c in courses:
                cid = str(c["_id"])
                # pregenerate_summary_in_background no-op si cache v2 déjà présent
                # (get_cached_summary retourne None pour les anciens caches v1)
                asyncio.create_task(pregenerate_summary_in_background(cid))
        except Exception:
            logger.exception("Erreur lors du warm-up des fiches existantes")

    asyncio.create_task(_warm_existing_summaries())

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
