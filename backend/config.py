"""Configuration centralisée via pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Base de données
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "eduai_db"

    # Modèles HuggingFace
    hf_home: str = "./models_cache"
    transformers_cache: str = "./models_cache"
    hf_hub_offline: bool = False
    transformers_offline: bool = False
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    qa_model: str = "etalab-ia/camembert-base-squadFR-fquad-piaf"
    summarizer_model: str = "csebuetnlp/mT5_multilingual_XLSum"
    quiz_model: str = "valhalla/t5-base-qa-qg-hl"

    # Pipeline NLP
    chunk_size: int = 400
    chunk_overlap: int = 50
    top_k_retrieval: int = 3
    min_confidence_score: float = 0.25

    # Sécurité
    secret_key: str = "change-this-in-production"
    allowed_origins: str = "http://localhost:3000"

    # Limites
    max_pdf_size_mb: int = 50
    max_courses_per_user: int = 20

    # Chemins
    faiss_index_dir: str = "data/faiss_indexes"

    # ── LLM local (Ollama) ──
    enable_llm: bool = True               # active la reformulation/quiz/RAG par LLM
    # Backend LLM : "groq" (cloud rapide gratuit) ou "ollama" (local CPU)
    llm_backend: str = "groq"
    # ── Groq Cloud (rapide, gratuit) ──
    groq_api_key: str = ""                # Clé GROQ (gsk_...) ; voir https://console.groq.com/keys
    groq_model: str = "llama-3.3-70b-versatile"  # Llama 3.3 70B = qualité top
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_timeout_seconds: int = 60
    # ── Ollama (fallback local) ──
    # ollama_host: str = "http://localhost:11434"
    # ollama_model: str = "qwen2.5:7b-instruct"
    ollama_timeout_seconds: int = 2000    # par requête (CPU ≈ 0.7 tok/s sur 7B, marge confortable)
    ollama_num_ctx: int = 4096            # taille contexte (assez pour chapitre tronqué à 6000 c.)
    ollama_max_tokens_summary: int = 600  # plafond résumé narratif (2-3 paragraphes ≈ 400-500 tok + titre + concepts)
    ollama_max_tokens_quiz: int = 500     # plafond JSON QCM (3 questions ≈ 400 tok)
    ollama_max_tokens_qa: int = 500       # plafond réponse Q&A
    ollama_temperature_summary: float = 0.3  # un peu de souplesse pour fluidité narrative
    ollama_temperature_quiz: float = 0.4
    ollama_temperature_qa: float = 0.1
    ollama_max_chunk_chars: int = 6000    # tronque le texte du chapitre envoyé au LLM (résumé)
    ollama_max_chunk_chars_quiz: int = 2000  # très court pour le quiz (CPU 0.4 tok/s)
    llm_health_check_seconds: int = 5     # délai du check au démarrage

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
