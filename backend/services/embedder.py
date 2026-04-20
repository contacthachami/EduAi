"""Embeddings multilingues avec sentence-transformers.

Pattern singleton : le modèle est chargé une seule fois.
"""

import logging
import numpy as np
import torch

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Charge le modèle d'embeddings (singleton)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from backend.config import get_settings

        settings = get_settings()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Chargement du modèle d'embeddings sur %s…", device)
        _model = SentenceTransformer(settings.embedding_model, device=device)
        logger.info("Modèle d'embeddings chargé — dimension : %d", _model.get_embedding_dimension())
    return _model


def embed_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Encode une liste de textes en vecteurs normalisés.

    Args:
        texts: Liste de textes à encoder.
        batch_size: Taille du batch pour l'encodage.

    Returns:
        Matrice numpy (n_texts, 384) de vecteurs normalisés.
    """
    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    logger.info("Encodage terminé : %d textes → vecteurs %s", len(texts), embeddings.shape)
    return np.array(embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    """Encode une seule requête en vecteur normalisé.

    Args:
        query: Texte de la question.

    Returns:
        Vecteur numpy (384,) normalisé.
    """
    model = _get_model()
    embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )
    return np.array(embedding, dtype=np.float32)


def get_embedding_dimension() -> int:
    """Retourne la dimension des vecteurs d'embeddings."""
    model = _get_model()
    return model.get_sentence_embedding_dimension()
