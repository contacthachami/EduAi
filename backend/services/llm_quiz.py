"""Génération de QCM via LLM local (Ollama) — UNE SEULE requête.

Stratégie performante CPU :
- On échantillonne des passages diversifiés à travers les chapitres.
- On envoie tout en UN seul appel LLM avec demande JSON stricte.
- On valide chaque question (4 choix uniques, index 0-3, explication).
- Sur N=10 questions : ~600 tokens output ≈ 5 min sur CPU (vs 30 min en multi-appels).
- On shuffle les options après génération (les LLM ont un biais à mettre la bonne réponse en A).
"""
from __future__ import annotations

import logging
import random
from typing import Optional

from backend.config import get_settings
from backend.services.llm_client import LLMUnavailable, get_client
from backend.services.llm_summarizer import _detect_lang

logger = logging.getLogger(__name__)


_SYSTEM_FR = """Tu es un concepteur de QCM pédagogique EXPERT. Tu produis des questions à choix multiples FIDÈLES au cours fourni, en JSON strict.

OBJECTIF : que l'étudiant doive RÉFLÉCHIR pour trouver la bonne réponse. Pas de questions triviales.

RÈGLES STRICTES :
- Une seule bonne réponse par question.
- Les 4 options DOIVENT toutes être plausibles, de **longueur comparable** (±15 caractères entre la plus courte et la plus longue), du même type sémantique (toutes des dates, OU tous des noms, OU toutes des définitions, etc.).
- INTERDIT : qu'une seule option soit visiblement plus longue/détaillée que les autres (= indice évident de la bonne réponse).
- INTERDIT : distracteurs absurdes ou de type "Aucune des réponses" / "Toutes les réponses".
- Distracteurs = confusions PIÈGES : termes proches mais inexacts, dates voisines, valeurs numériques proches, concepts du même domaine du cours.
- Pour les questions difficiles : nuances subtiles, contre-exemples, cas-limite, applications du concept.
- Évite les questions à réponse trop évidente type "Quel est le titre de ce chapitre ?".
- L'explication justifie en 1-2 phrases en s'appuyant sur le cours et explique POURQUOI les autres options sont fausses.
- Mix de difficulté : ~20% facile (mémorisation directe), ~20% moyen (compréhension), ~60% DIFFICILE (application, distinction fine, raisonnement).
- Couvre PLUSIEURS chapitres, pas un seul.
- N'invente RIEN qui ne soit pas dans le contenu fourni.
- Tu réponds UNIQUEMENT en JSON valide, aucun texte avant ou après."""

_SYSTEM_EN = """You are an EXPERT MCQ designer. You produce multiple-choice questions FAITHFUL to the provided course, in strict JSON.

GOAL: the student must THINK to find the correct answer. No trivial questions.

STRICT RULES:
- One correct answer per question.
- All 4 options MUST be plausible, of **comparable length** (±15 chars between shortest and longest), and of the same semantic type (all dates, OR all names, OR all definitions, etc.).
- FORBIDDEN: one option visibly longer/more detailed than the others (= obvious giveaway).
- FORBIDDEN: absurd distractors or "None of the above" / "All of the above".
- Distractors = TRAP confusions: close-but-wrong terms, neighboring dates, similar numerical values, concepts from the same course domain.
- For hard questions: subtle nuances, counter-examples, edge cases, applications of the concept.
- Avoid trivially obvious questions like "What is the title of this chapter?".
- Explanation justifies in 1-2 sentences grounded in the course and says WHY the other options are wrong.
- Difficulty mix: ~20% easy (direct memorization), ~20% medium (comprehension), ~60% HARD (application, fine distinction, reasoning).
- Cover MULTIPLE chapters, not just one.
- Invent NOTHING beyond the provided content.
- Respond ONLY with valid JSON, no text before or after."""

_USER_TEMPLATE_FR = """# Cours (extraits par chapitre)

{content}

---

Produis EXACTEMENT {n} questions QCM au format JSON suivant.
IMPORTANT : les options sont de VRAIES réponses concrètes (PAS "Choix A"), de **longueur similaire entre elles**, et toutes plausibles dans le contexte du cours.

{{
  "questions": [
    {{
      "question": "Texte de la question, précis et non ambigu ?",
      "options": ["réponse plausible 1", "réponse plausible 2", "réponse plausible 3", "réponse plausible 4"],
      "correct_index": 0,
      "explanation": "Justification courte basée sur le cours + pourquoi les autres options sont incorrectes.",
      "difficulty": "difficile"
    }}
  ]
}}

Champs obligatoires : question, options (4 réponses concrètes de longueur similaire), correct_index (0-3), explanation, difficulty ("facile"|"moyen"|"difficile").
Mix de difficulté : 20% facile, 20% moyen, **60% difficile**.
Couvre des chapitres variés. Options = 20 à 80 caractères chacune. Explication = 80 à 200 caractères.
"""

_USER_TEMPLATE_EN = """# Course (extracts by chapter)

{content}

---

Produce EXACTLY {n} MCQ questions in this JSON format.
IMPORTANT: options must be REAL concrete answers (NOT "Choice A"), of **similar length to each other**, and all plausible in the course context.

{{
  "questions": [
    {{
      "question": "Precise, unambiguous question text?",
      "options": ["plausible answer 1", "plausible answer 2", "plausible answer 3", "plausible answer 4"],
      "correct_index": 0,
      "explanation": "Short justification grounded in the course + why the other options are incorrect.",
      "difficulty": "hard"
    }}
  ]
}}

Required fields: question, options (4 concrete answers of similar length), correct_index (0-3), explanation, difficulty ("easy"|"medium"|"hard").
Difficulty mix: 20% easy, 20% medium, **60% hard**.
Cover varied chapters. Options = 20 to 80 chars each. Explanation = 80 to 200 chars.
"""


async def generate_quiz_llm(chunks: list[dict], num_questions: int = 10) -> Optional[list[dict]]:
    """Génère N QCM en UN SEUL appel LLM. Retourne None si Ollama indisponible."""
    settings = get_settings()
    if not settings.enable_llm:
        return None

    client = get_client()
    if not await client.is_available():
        return None

    # Regroupe par chapitre, en gardant l'ordre d'apparition
    by_chap: dict[str, list[dict]] = {}
    chap_order: list[str] = []
    for ch in chunks:
        title = (ch.get("chapter") or "Chapitre").strip()
        if title not in by_chap:
            by_chap[title] = []
            chap_order.append(title)
        by_chap[title].append(ch)

    if not chap_order:
        return None

    # Échantillonne ~max_chunk_chars / n_chap caractères par chapitre
    max_total = settings.ollama_max_chunk_chars_quiz
    per_chap_budget = max(300, max_total // max(len(chap_order), 1))

    parts: list[str] = []
    used = 0
    for chap in chap_order:
        if used >= max_total:
            break
        chap_text = "\n".join(c.get("text", "") for c in by_chap[chap]).strip()
        if not chap_text:
            continue
        slice_len = min(per_chap_budget, max_total - used)
        excerpt = chap_text[:slice_len]
        parts.append(f"## {chap}\n{excerpt}")
        used += len(excerpt)

    content = "\n\n".join(parts)

    sample = " ".join(c.get("text", "")[:300] for c in chunks[:5])
    lang = _detect_lang(sample)
    system = _SYSTEM_FR if lang == "fr" else _SYSTEM_EN
    template = _USER_TEMPLATE_FR if lang == "fr" else _USER_TEMPLATE_EN
    user = template.format(content=content, n=num_questions)

    # Budget tokens : ~250 tokens/question pour français verbose + JSON syntax + safety margin
    max_tokens = max(settings.ollama_max_tokens_quiz, num_questions * 250)

    try:
        # IMPORTANT: pas de json_mode strict pour qwen2.5:3b (trop restrictif),
        # on parse en loose. Le prompt impose déjà le format JSON.
        raw = await client.chat(
            system=system,
            user=user,
            temperature=settings.ollama_temperature_quiz,
            max_tokens=max_tokens,
            json_mode=False,
            retries=3,
        )
        from backend.services.llm_client import _parse_json_loose
        try:
            data = _parse_json_loose(raw)
        except LLMUnavailable as exc:
            logger.warning("Quiz JSON non parsable: %s | brut=%r", exc, raw[:300])
            return None
    except LLMUnavailable as exc:
        logger.warning("LLM quiz indisponible (%s) → fallback", exc)
        return None
    except Exception:
        logger.exception("Erreur LLM quiz")
        return None

    questions = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(questions, list) or not questions:
        logger.warning("LLM quiz: format JSON inattendu")
        return None

    generic_source = (chunks[0].get("text", "") if chunks else "")[:600]

    cleaned: list[dict] = []
    seen_q: set[str] = set()
    qid = 1
    for q in questions:
        c = _validate_question(q, generic_source, qid)
        if not c:
            continue
        key = c["question"].lower().strip()
        if key in seen_q:
            continue
        seen_q.add(key)
        cleaned.append(c)
        qid += 1

    if not cleaned:
        return None
    return cleaned[:num_questions]


def _normalize_difficulty(raw: object) -> str:
    """Normalise la difficulté en {facile, moyen, difficile}. Défaut : moyen."""
    if not isinstance(raw, str):
        return "moyen"
    s = raw.strip().lower()
    mapping = {
        "facile": "facile", "easy": "facile", "f": "facile", "1": "facile",
        "moyen": "moyen", "moyenne": "moyen", "medium": "moyen", "med": "moyen", "m": "moyen", "2": "moyen",
        "difficile": "difficile", "hard": "difficile", "difficult": "difficile", "d": "difficile", "3": "difficile",
    }
    return mapping.get(s, "moyen")


def _validate_question(q: dict, source: str, qid: int) -> Optional[dict]:
    """Valide et normalise une question. Retourne None si invalide."""
    if not isinstance(q, dict):
        return None
    text = (q.get("question") or "").strip()
    options = q.get("options")
    correct = q.get("correct_index")
    explanation = (q.get("explanation") or "").strip()
    difficulty = _normalize_difficulty(q.get("difficulty"))

    if not text or len(text) < 5:
        return None
    if not isinstance(options, list) or len(options) != 4:
        return None
    options = [str(o).strip() for o in options]
    if any(not o for o in options):
        return None
    if len(set(o.lower() for o in options)) != 4:
        return None
    if isinstance(correct, str):
        cs = correct.strip().upper()
        if cs in {"A", "B", "C", "D"}:
            correct = ord(cs) - ord("A")
        elif cs.isdigit():
            n = int(cs)
            correct = n - 1 if n in (1, 2, 3, 4) else n
    if not isinstance(correct, int) or not 0 <= correct < 4:
        return None
    if not explanation:
        explanation = "(Justification non fournie)"

    # Anti-biais position : on shuffle les options et on recalcule l'index correct.
    correct_text = options[correct]
    shuffled = options[:]
    random.shuffle(shuffled)
    new_correct = shuffled.index(correct_text)

    return {
        "id": qid,
        "question": text,
        "options": shuffled,
        "correct_index": new_correct,
        "explanation": explanation,
        "source_chunk": source,
        "difficulty": difficulty,
    }
