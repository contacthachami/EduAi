"""Extraction de texte PDF avec PyMuPDF (fitz).

Extrait le texte page par page, détecte les titres de chapitres
via la taille de police et le style gras.
"""

import fitz  # PyMuPDF
import logging
from typing import TypedDict

logger = logging.getLogger(__name__)


class PageBlock(TypedDict):
    page_num: int
    text: str
    is_title: bool
    chapter_name: str


def _detect_chapter_title(block: dict, page_median_size: float) -> bool:
    """Détecte si un bloc de texte est un titre de chapitre."""
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            size = span.get("size", 0)
            flags = span.get("flags", 0)
            is_bold = bool(flags & 2 ** 4)  # bit 4 = gras
            if size > page_median_size * 1.3 or (is_bold and size >= 14):
                return True
    return False


def _extract_block_text(block: dict) -> str:
    """Extrait le texte brut d'un bloc."""
    texts = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            texts.append(span.get("text", ""))
    return " ".join(texts).strip()


def _get_median_font_size(blocks: list[dict]) -> float:
    """Calcule la taille de police médiane d'une page."""
    sizes = []
    for block in blocks:
        if block.get("type") != 0:  # texte uniquement
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                sizes.append(span.get("size", 12))
    if not sizes:
        return 12.0
    sizes.sort()
    mid = len(sizes) // 2
    return sizes[mid]


def extract_pdf(file_bytes: bytes) -> list[PageBlock]:
    """Extrait le texte structuré d'un PDF.

    Args:
        file_bytes: Contenu binaire du fichier PDF.

    Returns:
        Liste de blocs avec page_num, texte, détection titre, nom chapitre.

    Raises:
        ValueError: Si le PDF est protégé ou ne contient pas de texte.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Impossible d'ouvrir le PDF : {e}")

    if doc.is_encrypted:
        doc.close()
        raise ValueError("PDF protégé par mot de passe, impossible de lire le contenu.")

    results: list[PageBlock] = []
    current_chapter = "Introduction"
    total_text_length = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict", sort=True)["blocks"]
        median_size = _get_median_font_size(blocks)

        page_text_parts: list[str] = []

        for block in blocks:
            if block.get("type") != 0:  # ignorer images
                continue

            text = _extract_block_text(block)
            if not text or len(text) < 3:
                continue

            is_title = _detect_chapter_title(block, median_size)

            if is_title and len(text) > 3:
                current_chapter = text.strip()
                results.append(PageBlock(
                    page_num=page_num + 1,
                    text=text,
                    is_title=True,
                    chapter_name=current_chapter,
                ))
            else:
                page_text_parts.append(text)

            total_text_length += len(text)

        # Regrouper le texte non-titre de la page
        if page_text_parts:
            combined = " ".join(page_text_parts)
            # Nettoyage : supprimer numéros de page isolés, en-têtes répétés
            combined = _clean_text(combined)
            if combined.strip():
                results.append(PageBlock(
                    page_num=page_num + 1,
                    text=combined,
                    is_title=False,
                    chapter_name=current_chapter,
                ))

    num_pages = len(doc)
    doc.close()

    if total_text_length < 20:
        raise ValueError("Aucun texte extractible trouvé dans le PDF. Vérifiez qu'il ne s'agit pas d'un PDF scanné (image).")

    logger.info("PDF extrait : %d pages, %d blocs, %d caractères", num_pages, len(results), total_text_length)
    return results


def _clean_text(text: str) -> str:
    """Nettoie le texte extrait (en-têtes répétés, numéros de page, etc.)."""
    import re
    # Supprimer les numéros de page isolés
    text = re.sub(r"^\s*\d{1,3}\s*$", "", text, flags=re.MULTILINE)
    # Supprimer les multiples espaces
    text = re.sub(r" {2,}", " ", text)
    # Supprimer les sauts de ligne multiples
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_total_pages(file_bytes: bytes) -> int:
    """Retourne le nombre de pages du PDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    count = len(doc)
    doc.close()
    return count
