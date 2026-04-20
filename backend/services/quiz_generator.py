"""Génération automatique de quiz à partir des chunks de cours.

Pipeline : sélection chunks denses → génération question T5 →
extraction réponse → génération distracteurs spaCy → mélange options.
"""

import logging
import random
import torch

from backend.config import get_settings

logger = logging.getLogger(__name__)

_qg_pipeline = None
_nlp = None


def _get_qg_pipeline():
    """Charge le modèle T5-QG et son tokenizer (singleton)."""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    global _qg_pipeline
    if _qg_pipeline is None:
        settings = get_settings()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Chargement de T5-QG sur %s…", device.upper())
        tokenizer = AutoTokenizer.from_pretrained(settings.quiz_model)
        model = AutoModelForSeq2SeqLM.from_pretrained(settings.quiz_model).to(device)
        model.eval()
        _qg_pipeline = (model, tokenizer, device)
        logger.info("T5-QG chargé avec succès.")
    return _qg_pipeline


def _get_spacy():
    """Charge spaCy français (singleton partagé)."""
    global _nlp
    if _nlp is None:
        import spacy
        try:
            _nlp = spacy.load("fr_core_news_lg")
        except OSError:
            try:
                _nlp = spacy.load("fr_core_news_sm")
            except OSError:
                _nlp = None
    return _nlp


def _select_dense_chunks(chunks: list[dict], num: int = 10) -> list[dict]:
    """Sélectionne les chunks les plus denses en concepts."""
    scored = []
    for chunk in chunks:
        text = chunk["text"]
        # Score basé sur la longueur et la diversité des mots
        words = set(text.lower().split())
        score = len(words) * (len(text) / max(len(text.split()), 1))
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [c for _, c in scored[:num]]
    random.shuffle(selected)
    return selected


def _generate_question(chunk_text: str) -> str | None:
    """Génère une question à partir d'un chunk avec T5."""
    model, tokenizer, device = _get_qg_pipeline()
    try:
        # Format attendu par valhalla/t5-base-qa-qg-hl
        input_text = f"generate question: {chunk_text}"
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(device)
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=100, num_beams=4, early_stopping=True)
        question = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        if question and len(question) > 10:
            return question
    except Exception as e:
        logger.warning("Erreur génération question : %s", e)
    return None


def _extract_answer_from_chunk(chunk_text: str) -> str | None:
    """Extrait une réponse candidate du chunk (phrase clé)."""
    nlp = _get_spacy()
    if nlp is None:
        # Fallback : prendre la première phrase significative
        sentences = chunk_text.split(".")
        for s in sentences:
            s = s.strip()
            if len(s) > 20:
                return s
        return None

    doc = nlp(chunk_text[:1000])

    # Chercher les entités comme réponses potentielles
    entities = [ent.text for ent in doc.ents if len(ent.text) > 2]
    if entities:
        return entities[0]

    # Fallback : premier nom propre ou groupe nominal
    for chunk in doc.noun_chunks:
        if len(chunk.text) > 3:
            return chunk.text

    return None


def _generate_distractors(correct_answer: str, chunk_text: str, all_chunks: list[dict], n: int = 3) -> list[str]:
    """Génère des distracteurs plausibles pour un QCM."""
    nlp = _get_spacy()
    distractors = set()

    if nlp:
        # Extraire des entités/noms des autres chunks comme distracteurs
        for other_chunk in all_chunks:
            if other_chunk["text"] == chunk_text:
                continue
            doc = nlp(other_chunk["text"][:500])
            for ent in doc.ents:
                candidate = ent.text.strip()
                if (
                    candidate.lower() != correct_answer.lower()
                    and len(candidate) > 2
                    and candidate not in distractors
                ):
                    distractors.add(candidate)
                    if len(distractors) >= n * 2:
                        break
            if len(distractors) >= n * 2:
                break

    # Fallback : extraire des mots/phrases des chunks
    if len(distractors) < n:
        for other_chunk in all_chunks:
            sentences = other_chunk["text"].split(".")
            for s in sentences:
                s = s.strip()
                if (
                    len(s) > 10
                    and s.lower() != correct_answer.lower()
                    and s not in distractors
                ):
                    distractors.add(s[:80])
                    if len(distractors) >= n * 2:
                        break

    distractor_list = list(distractors)
    random.shuffle(distractor_list)
    return distractor_list[:n]


def generate_quiz(chunks: list[dict], num_questions: int = 10) -> list[dict]:
    """Génère un quiz complet à partir des chunks d'un cours.

    Args:
        chunks: Liste de chunks du cours.
        num_questions: Nombre de questions souhaitées.

    Returns:
        Liste de questions de quiz formatées.
    """
    selected_chunks = _select_dense_chunks(chunks, num=num_questions * 2)
    questions = []
    question_id = 1

    for chunk in selected_chunks:
        if len(questions) >= num_questions:
            break

        # Étape 1 : Générer la question
        question_text = _generate_question(chunk["text"])
        if not question_text:
            continue

        # Étape 2 : Extraire la réponse correcte
        correct_answer = _extract_answer_from_chunk(chunk["text"])
        if not correct_answer:
            continue

        # Étape 3 : Générer les distracteurs
        distractors = _generate_distractors(correct_answer, chunk["text"], chunks)
        if len(distractors) < 3:
            continue

        # Étape 4 : Mélanger les options
        options = [correct_answer] + distractors[:3]
        random.shuffle(options)
        correct_index = options.index(correct_answer)

        # Étape 5 : Explication
        explanation = chunk["text"][:200].strip()
        if len(chunk["text"]) > 200:
            explanation += "…"

        questions.append({
            "id": question_id,
            "question": question_text,
            "options": options,
            "correct_index": correct_index,
            "explanation": f"Source : {explanation}",
            "source_chunk": chunk["text"][:300],
        })
        question_id += 1

    logger.info("Quiz généré : %d questions sur %d demandées", len(questions), num_questions)
    return questions
