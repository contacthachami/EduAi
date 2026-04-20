"""Index FAISS pour la recherche vectorielle.

Un index par cours, sauvegardé sur disque. Cache mémoire des index chargés.
Utilise IndexFlatIP (Inner Product = cosine similarity sur vecteurs normalisés).
"""

import os
import logging
import numpy as np

from backend.config import get_settings

logger = logging.getLogger(__name__)

# Cache mémoire des index FAISS chargés
_index_cache: dict = {}


def create_index(course_id: str, embeddings: np.ndarray) -> None:
    """Crée un index FAISS pour un cours et le sauvegarde sur disque."""
    import faiss
    settings = get_settings()
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # Sauvegarder sur disque
    os.makedirs(settings.faiss_index_dir, exist_ok=True)
    path = os.path.join(settings.faiss_index_dir, f"{course_id}.faiss")
    faiss.write_index(index, path)

    # Mettre en cache
    _index_cache[course_id] = index
    logger.info("Index FAISS créé : %s — %d vecteurs, dim %d", course_id, embeddings.shape[0], dim)


def _load_index(course_id: str):
    """Charge un index FAISS depuis le disque ou le cache."""
    import faiss
    if course_id in _index_cache:
        return _index_cache[course_id]

    settings = get_settings()
    path = os.path.join(settings.faiss_index_dir, f"{course_id}.faiss")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Index FAISS introuvable pour le cours {course_id}")

    index = faiss.read_index(path)
    _index_cache[course_id] = index
    logger.info("Index FAISS chargé depuis le disque : %s", course_id)
    return index


def search(course_id: str, query_vector: np.ndarray, k: int = 3) -> list[dict]:
    """Recherche les k chunks les plus similaires.

    Args:
        course_id: Identifiant du cours.
        query_vector: Vecteur de la question (1, dim).
        k: Nombre de résultats souhaités.

    Returns:
        Liste de dicts avec 'index' et 'score'.
    """
    index = _load_index(course_id)

    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)

    scores, indices = index.search(query_vector, k)

    results = []
    for i in range(k):
        idx = int(indices[0][i])
        score = float(scores[0][i])
        if idx >= 0:  # FAISS retourne -1 si pas assez de résultats
            results.append({"index": idx, "score": score})

    logger.info("Recherche FAISS : %d résultats, meilleur score=%.4f", len(results), results[0]["score"] if results else 0)
    return results


def delete_index(course_id: str) -> None:
    """Supprime l'index FAISS d'un cours."""
    settings = get_settings()
    path = os.path.join(settings.faiss_index_dir, f"{course_id}.faiss")
    if os.path.exists(path):
        os.remove(path)
    _index_cache.pop(course_id, None)
    logger.info("Index FAISS supprimé : %s", course_id)
