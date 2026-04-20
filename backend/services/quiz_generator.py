"""Génération automatique de quiz à partir des chunks de cours.

Pipeline : sélection chunks denses → génération question T5 →
extraction réponse → génération distracteurs spaCy → mélange options.
"""

import logging
import random
import threading
import torch

from backend.config import get_settings

logger = logging.getLogger(__name__)

_qg_pipeline = None
_nlp = None
_qg_lock = threading.Lock()
_nlp_lock = threading.Lock()


def _get_qg_pipeline():
    """Charge le modèle T5-QG et son tokenizer (singleton thread-safe)."""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    global _qg_pipeline
    if _qg_pipeline is None:
        with _qg_lock:
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
    """Charge spaCy français (singleton thread-safe)."""
    global _nlp
    if _nlp is None:
        with _nlp_lock:
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


def _generate_question(chunk_text: str, answer: str) -> str | None:
    """Génère une question conditionnée sur la réponse avec T5 (answer-aware QG)."""
    model, tokenizer, device = _get_qg_pipeline()
    try:
        # Format answer-aware : mettre en évidence la réponse dans le contexte
        highlighted = chunk_text.replace(answer, f"<hl> {answer} <hl>", 1)
        input_text = f"generate question: {highlighted}"
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(device)
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=100, num_beams=4, early_stopping=True)
        question = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        if question and len(question) > 10:
            # S'assurer que c'est bien une question
            if not question.endswith("?"):
                question += " ?"
            return question
    except Exception as e:
        logger.warning("Erreur génération question : %s", e)
    return None


def _extract_answer_from_chunk(chunk_text: str) -> str | None:
    """Extrait une réponse candidate du chunk en utilisant d'abord le modèle T5,
    puis fallback sur NER spaCy."""
    # Essayer d'abord avec le modèle T5 (tâche "answer:")
    model, tokenizer, device = _get_qg_pipeline()
    try:
        input_text = f"extract answer: {chunk_text}"
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(device)
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=50, num_beams=2, early_stopping=True)
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        # Vérifier que la réponse est présente dans le texte source
        if answer and len(answer) > 2 and answer.lower() in chunk_text.lower():
            return answer
    except Exception:
        pass

    # Fallback : spaCy NER
    nlp = _get_spacy()
    if nlp is None:
        sentences = chunk_text.split(".")
        for s in sentences:
            s = s.strip()
            if len(s) > 20:
                return s
        return None

    doc = nlp(chunk_text[:1000])

    # Préférer les entités techniques/organisationnelles (plus adaptées aux quiz)
    entities = [ent.text for ent in doc.ents if len(ent.text) > 2 and ent.label_ in ("ORG", "MISC", "LOC", "EVENT")]
    if not entities:
        entities = [ent.text for ent in doc.ents if len(ent.text) > 2]
    if entities:
        return entities[0]

    # Fallback : groupe nominal le plus long (plus informatif)
    noun_chunks_list = sorted(doc.noun_chunks, key=lambda nc: len(nc.text), reverse=True)
    for nc in noun_chunks_list:
        if len(nc.text) > 3:
            return nc.text

    return None


def _generate_distractors(correct_answer: str, chunk_text: str, all_chunks: list[dict], n: int = 3) -> list[str]:
    """Génère des distracteurs plausibles pour un QCM.

    Stratégie : chercher des entités/noms de même catégorie que la réponse correcte
    dans d'autres chunks pour des distracteurs plus cohérents.
    """
    nlp = _get_spacy()
    distractors = set()
    correct_lower = correct_answer.lower().strip()

    # Identifier la catégorie de la réponse correcte
    target_labels = set()
    if nlp:
        doc_answer = nlp(correct_answer)
        for ent in doc_answer.ents:
            target_labels.add(ent.label_)
        # Si pas d'entité détectée, regarder dans le chunk source
        if not target_labels:
            doc_src = nlp(chunk_text[:500])
            for ent in doc_src.ents:
                if ent.text.lower().strip() == correct_lower:
                    target_labels.add(ent.label_)

    if nlp:
        # Phase 1 : entités de même catégorie dans d'autres chunks
        for other_chunk in all_chunks:
            if other_chunk["text"] == chunk_text:
                continue
            doc = nlp(other_chunk["text"][:500])
            for ent in doc.ents:
                candidate = ent.text.strip()
                if (
                    candidate.lower() != correct_lower
                    and len(candidate) > 2
                    and candidate not in distractors
                    and (not target_labels or ent.label_ in target_labels)
                ):
                    distractors.add(candidate)
                    if len(distractors) >= n:
                        break
            if len(distractors) >= n:
                break

        # Phase 2 : toutes les entités si pas assez
        if len(distractors) < n:
            for other_chunk in all_chunks:
                if other_chunk["text"] == chunk_text:
                    continue
                doc = nlp(other_chunk["text"][:500])
                for ent in doc.ents:
                    candidate = ent.text.strip()
                    if (
                        candidate.lower() != correct_lower
                        and len(candidate) > 2
                        and candidate not in distractors
                    ):
                        distractors.add(candidate)
                        if len(distractors) >= n:
                            break
                if len(distractors) >= n:
                    break

    # Phase 3 : groupes nominaux si toujours pas assez
    if len(distractors) < n and nlp:
        for other_chunk in all_chunks:
            if other_chunk["text"] == chunk_text:
                continue
            doc = nlp(other_chunk["text"][:500])
            for nc in doc.noun_chunks:
                candidate = nc.text.strip()
                if (
                    candidate.lower() != correct_lower
                    and len(candidate) > 3
                    and candidate not in distractors
                ):
                    distractors.add(candidate)
                    if len(distractors) >= n:
                        break
            if len(distractors) >= n:
                break

    # Phase 4 : fallback segments de phrases
    if len(distractors) < n:
        for other_chunk in all_chunks:
            sentences = other_chunk["text"].split(".")
            for s in sentences:
                s = s.strip()
                if (
                    len(s) > 10
                    and s.lower() != correct_lower
                    and s not in distractors
                ):
                    distractors.add(s[:80])
                    if len(distractors) >= n:
                        break
            if len(distractors) >= n:
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

        # Étape 1 : Extraire la réponse correcte D'ABORD
        correct_answer = _extract_answer_from_chunk(chunk["text"])
        if not correct_answer:
            continue

        # Étape 2 : Générer la question conditionnée sur la réponse
        question_text = _generate_question(chunk["text"], correct_answer)
        if not question_text:
            continue

        # Étape 3 : Vérifier qu'on n'a pas déjà une question similaire
        if any(q["question"].lower() == question_text.lower() for q in questions):
            continue

        # Étape 4 : Générer les distracteurs
        distractors = _generate_distractors(correct_answer, chunk["text"], chunks)
        if len(distractors) < 3:
            continue

        # Étape 5 : Dédupliquer les options
        options_set = {correct_answer.lower().strip()}
        unique_distractors = []
        for d in distractors:
            if d.lower().strip() not in options_set:
                options_set.add(d.lower().strip())
                unique_distractors.append(d)
            if len(unique_distractors) >= 3:
                break
        if len(unique_distractors) < 3:
            continue

        # Étape 6 : Mélanger les options
        options = [correct_answer] + unique_distractors[:3]
        random.shuffle(options)
        correct_index = options.index(correct_answer)

        # Étape 7 : Explication
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
