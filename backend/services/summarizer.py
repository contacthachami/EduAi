"""Résumé automatique par chapitre avec mT5.

Génère un résumé pour chaque chapitre du cours et extrait
les concepts clés via spaCy NER.
"""

import logging
import threading
import torch

from backend.config import get_settings

import re

logger = logging.getLogger(__name__)

_summarizer = None
_nlp = None
_summarizer_lock = threading.Lock()
_nlp_lock = threading.Lock()


def _get_summarizer():
    """Charge le modèle mT5 et son tokenizer (singleton thread-safe)."""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    global _summarizer
    if _summarizer is None:
        with _summarizer_lock:
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
    """Charge le modèle spaCy français (singleton thread-safe)."""
    global _nlp
    if _nlp is None:
        with _nlp_lock:
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
            cleaned = ent.text.strip()
            # Filtrer les entrées garbled (symboles, trop courtes, truncated)
            if (len(cleaned) > 2
                    and not re.search(r"[●■▪•→○]", cleaned)
                    and cleaned[-1].isalnum()
                    and not cleaned.endswith("Introduc")  # truncated common pattern
                    and len(cleaned) < 50):  # reject overly long entity spans
                concepts.add(cleaned)

    # Noms propres et noms communs fréquents (lemmatisés)
    noun_freq: dict[str, int] = {}
    for token in doc:
        if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 3 and not token.is_stop:
            lemma = token.lemma_.lower()
            # Filtrer les lemmes non-alphabétiques
            if lemma.isalpha():
                noun_freq[lemma] = noun_freq.get(lemma, 0) + 1

    # Ajouter les noms les plus fréquents
    sorted_nouns = sorted(noun_freq.items(), key=lambda x: x[1], reverse=True)
    for noun, _freq in sorted_nouns[:max_concepts]:
        concepts.add(noun.capitalize())

    return list(concepts)[:max_concepts]


def _extractive_fallback(text: str, max_sentences: int = 3) -> str:
    """Résumé extractif simple : premières phrases significatives, dédupliquées."""
    # Séparer par points ET sauts de ligne pour mieux gérer les slides
    text_clean = text.replace("\n", ". ")
    sentences = [s.strip() for s in text_clean.split(".") if len(s.strip()) > 20]
    # Dédupliquer les phrases (texte de titre/headers souvent répété)
    seen = set()
    unique = []
    for s in sentences:
        normalized = s.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(s)
    result = ". ".join(unique[:max_sentences]) + "." if unique else text[:200]
    return result


def _clean_summary(text: str) -> str:
    """Nettoie le résumé : supprime caractères non-latins, espaces multiples."""
    # Garder uniquement Latin, chiffres, ponctuation courante, accents français
    text = re.sub(r"[^\u0000-\u024F\u1E00-\u1EFF0-9\s.,;:!?'\"()\-–—/\u2018\u2019\u201C\u201D\u2026]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_repetitive(text: str) -> bool:
    """Détecte les résumés dégénérés (boucles de répétition)."""
    words = text.lower().split()
    if len(words) < 6:
        return False
    unique_ratio = len(set(words)) / len(words)
    return unique_ratio < 0.45


def _is_relevant_summary(summary: str, source_text: str, threshold: float = 0.15) -> bool:
    """Vérifie que le résumé partage suffisamment de mots avec le texte source."""
    source_words = set(source_text.lower().split())
    summary_words = set(summary.lower().split())
    if not summary_words:
        return False
    overlap = len(source_words & summary_words) / len(summary_words)
    return overlap >= threshold


def summarize_chapter(chapter_text: str, chapter_title: str, pages: list[int]) -> dict:
    """Génère un résumé pour un chapitre.

    Args:
        chapter_text: Texte complet du chapitre (chunks concaténés).
        chapter_title: Titre du chapitre.
        pages: Liste des numéros de pages du chapitre.

    Returns:
        Dict avec title, summary, pages, key_concepts.
    """
    key_concepts = _extract_key_concepts(chapter_text)

    # Chapitres trop courts → résumé extractif pour éviter les hallucinations
    min_chars_for_abstractive = 500
    if len(chapter_text.strip()) < min_chars_for_abstractive:
        logger.info("Chapitre '%s' trop court (%d chars), résumé extractif.", chapter_title, len(chapter_text))
        fallback = _extractive_fallback(chapter_text)
        if _is_repetitive(fallback):
            fallback = chapter_title
        return {
            "title": chapter_title,
            "summary": fallback,
            "pages": pages,
            "key_concepts": key_concepts,
        }

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
                min_length=30,
                num_beams=4,
                length_penalty=1.5,
                no_repeat_ngram_size=3,
                early_stopping=True,
            )
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        summary = _clean_summary(summary)

        # Vérification qualité : répétition ou hors sujet → fallback extractif
        if _is_repetitive(summary) or not _is_relevant_summary(summary, chapter_text):
            logger.warning("Résumé de mauvaise qualité pour '%s', fallback extractif.", chapter_title)
            summary = _extractive_fallback(chapter_text)

    except Exception as e:
        logger.error("Erreur mT5 résumé pour '%s' : %s", chapter_title, e)
        summary = _extractive_fallback(chapter_text)

    # Dernière vérification : si le résumé final est toujours répétitif ou trop court, utiliser le titre
    if _is_repetitive(summary) or len(summary.strip()) < 30:
        summary = chapter_title

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
