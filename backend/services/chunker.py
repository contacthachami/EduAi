"""Découpage intelligent du texte en chunks avec overlap.

Respecte les limites de phrases via détection de ponctuation.
Conserve les métadonnées (page, chapitre, index).
"""

import re
import logging
from typing import TypedDict

logger = logging.getLogger(__name__)


class Chunk(TypedDict):
    text: str
    page: int
    chapter: str
    chunk_index: int


# Pattern de fin de phrase
_SENTENCE_END = re.compile(r"[.!?।]\s+")


def _split_sentences(text: str) -> list[str]:
    """Découpe un texte en phrases."""
    parts = _SENTENCE_END.split(text)
    sentences = []
    pos = 0
    for part in parts:
        end = pos + len(part)
        # Retrouver le séparateur
        match = _SENTENCE_END.search(text, end)
        if match:
            sentences.append(text[pos : match.end()])
            pos = match.end()
        else:
            sentences.append(text[pos:])
            break
    return [s.strip() for s in sentences if s.strip()]


def create_chunks(
    page_blocks: list[dict],
    chunk_size: int = 400,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """Découpe le texte extrait en chunks de taille contrôlée.

    Args:
        page_blocks: Résultat de pdf_extractor.extract_pdf()
        chunk_size: Nombre de mots cible par chunk.
        chunk_overlap: Nombre de mots d'overlap entre chunks consécutifs.

    Returns:
        Liste de chunks avec métadonnées.
    """
    # Regrouper le texte par chapitre en conservant les pages
    chapter_texts: list[dict] = []
    current_chapter = "Introduction"
    current_texts: list[str] = []
    current_pages: set[int] = set()

    for block in page_blocks:
        if block.get("is_title"):
            # Sauvegarder le chapitre précédent
            if current_texts:
                chapter_texts.append({
                    "chapter": current_chapter,
                    "text": " ".join(current_texts),
                    "pages": sorted(current_pages),
                })
            current_chapter = block["chapter_name"]
            current_texts = []
            current_pages = set()
        else:
            current_texts.append(block["text"])
            current_pages.add(block["page_num"])

    # Sauvegarder le dernier chapitre
    if current_texts:
        chapter_texts.append({
            "chapter": current_chapter,
            "text": " ".join(current_texts),
            "pages": sorted(current_pages),
        })

    # Découper chaque chapitre en chunks
    all_chunks: list[Chunk] = []
    chunk_index = 0

    for chapter_data in chapter_texts:
        words = chapter_data["text"].split()
        pages = chapter_data["pages"]
        chapter = chapter_data["chapter"]

        if not words:
            continue

        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text = " ".join(words[start:end])

            # Essayer de couper à la fin d'une phrase
            if end < len(words):
                last_period = chunk_text.rfind(".")
                last_question = chunk_text.rfind("?")
                last_exclaim = chunk_text.rfind("!")
                best_cut = max(last_period, last_question, last_exclaim)
                if best_cut > len(chunk_text) * 0.5:
                    chunk_text = chunk_text[: best_cut + 1]
                    # Recalculer le end réel
                    actual_words = len(chunk_text.split())
                    end = start + actual_words

            # Estimer la page dominante
            progress = start / max(len(words), 1)
            page_idx = min(int(progress * len(pages)), len(pages) - 1)
            page = pages[page_idx] if pages else 1

            all_chunks.append(Chunk(
                text=chunk_text.strip(),
                page=page,
                chapter=chapter,
                chunk_index=chunk_index,
            ))
            chunk_index += 1

            # Avancer avec overlap
            start = max(end - chunk_overlap, start + 1)

    logger.info("Chunking terminé : %d chunks créés", len(all_chunks))
    return all_chunks
