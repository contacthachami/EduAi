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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
