"""Résumé automatique par chapitre avec mT5.

Génère un résumé pour chaque chapitre du cours et extrait
les concepts clés via spaCy NER.
"""

import logging
import torch

from backend.config import get_settings

logger = logging.getLogger(__name__)

_summarizer = None
_nlp = None


def _get_summarizer():
    """Charge le modèle mT5 et son tokenizer (singleton)."""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    global _summarizer
    if _summarizer is None:
        settings = get_settings()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Chargement de mT5 summarizer sur %s…", device.upper())
        tokenizer = AutoTokenizer.from_pretrained(settings.summarizer_model)
        model = AutoModelForSeq2SeqLM.from_pretrained(settings.summarizer_model).to(device)
        model.eval()
        _summarizer = (model, tokenizer, device)
        logger.info("mT5 summarizer chargé avec succès.")
    return _summarizer


def _get_spacy():
    """Charge le modèle spaCy français (singleton)."""
    global _nlp
    if _nlp is None:
        import spacy
        try:
            _nlp = spacy.load("fr_core_news_lg")
        except OSError:
            logger.warning("Modèle spaCy fr_core_news_lg non trouvé, tentative avec fr_core_news_sm…")
            try:
                _nlp = spacy.load("fr_core_news_sm")
            except OSError:
                logger.error("Aucun modèle spaCy français installé.")
                _nlp = None
    return _nlp


def _extract_key_concepts(text: str, max_concepts: int = 8) -> list[str]:
    """Extrait les concepts clés d'un texte via NER + noms fréquents."""
    nlp = _get_spacy()
    if nlp is None:
        return []

    # Limiter la taille du texte pour spaCy
    doc = nlp(text[:5000])

    concepts = set()

    # Entités nommées pertinentes
    for ent in doc.ents:
        if ent.label_ in ("PERSON", "ORG", "MISC", "LOC", "EVENT"):
            concepts.add(ent.text.strip())

    # Noms propres et noms communs fréquents (lemmatisés)
    noun_freq: dict[str, int] = {}
    for token in doc:
        if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 3 and not token.is_stop:
            lemma = token.lemma_.lower()
            noun_freq[lemma] = noun_freq.get(lemma, 0) + 1

    # Ajouter les noms les plus fréquents
    sorted_nouns = sorted(noun_freq.items(), key=lambda x: x[1], reverse=True)
    for noun, _freq in sorted_nouns[:max_concepts]:
        concepts.add(noun.capitalize())

    return list(concepts)[:max_concepts]


def summarize_chapter(chapter_text: str, chapter_title: str, pages: list[int]) -> dict:
    """Génère un résumé pour un chapitre.

    Args:
        chapter_text: Texte complet du chapitre (chunks concaténés).
        chapter_title: Titre du chapitre.
        pages: Liste des numéros de pages du chapitre.

    Returns:
        Dict avec title, summary, pages, key_concepts.
    """
    summarizer = _get_summarizer()
    model, tokenizer, device = summarizer

    # Tronquer si trop long (mT5 a une limite de tokens)
    max_input_chars = 3000
    input_text = chapter_text[:max_input_chars]

    try:
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=150,
                min_length=40,
                num_beams=4,
                early_stopping=True,
            )
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        logger.error("Erreur mT5 résumé pour '%s' : %s", chapter_title, e)
        summary = "Résumé non disponible pour ce chapitre."

    key_concepts = _extract_key_concepts(chapter_text)

    return {
        "title": chapter_title,
        "summary": summary,
        "pages": pages,
        "key_concepts": key_concepts,
    }


def summarize_course(chunks: list[dict]) -> list[dict]:
    """Génère les résumés de tous les chapitres d'un cours.

    Args:
        chunks: Liste de chunks avec 'text', 'chapter', 'page'.

    Returns:
        Liste de résumés par chapitre.
    """
    # Regrouper les chunks par chapitre
    chapters: dict[str, dict] = {}
    for chunk in chunks:
        ch = chunk.get("chapter", "Sans titre")
        if ch not in chapters:
            chapters[ch] = {"text": "", "pages": set()}
        chapters[ch]["text"] += " " + chunk["text"]
        chapters[ch]["pages"].add(chunk["page"])

    summaries = []
    total = len(chapters)
    for i, (title, data) in enumerate(chapters.items(), 1):
        logger.info("Résumé chapitre %d/%d : %s", i, total, title)
        summary = summarize_chapter(
            chapter_text=data["text"].strip(),
            chapter_title=title,
            pages=sorted(data["pages"]),
        )
        summaries.append(summary)

    logger.info("Résumés générés : %d chapitres", len(summaries))
    return summaries
