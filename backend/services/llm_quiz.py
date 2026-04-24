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


_SYSTEM_FR = """Tu es un concepteur de QCM pédagogique expert. Tu produis des questions à choix multiples FIDÈLES au cours fourni, en JSON strict.

RÈGLES :
- Une seule bonne réponse par question.
- Les 4 choix doivent être PLAUSIBLES, courts (<= 80 caractères), distincts.
- Les distracteurs sont basés sur des confusions réalistes (pas du n'importe quoi).
- L'explication justifie en 1-2 phrases en s'appuyant sur le cours.
- Mix de difficultés : ~40% facile (mémorisation), ~40% moyen (compréhension), ~20% difficile (application/distinction).
- Couvre PLUSIEURS chapitres, pas un seul.
- N'invente RIEN qui ne soit pas dans le contenu fourni.
- Tu réponds UNIQUEMENT en JSON valide, aucun texte avant ou après."""

_SYSTEM_EN = """You are an expert MCQ designer. You produce multiple-choice questions FAITHFUL to the provided course, in strict JSON.

RULES:
- One correct answer per question.
- The 4 choices must be PLAUSIBLE, short (<= 80 chars), distinct.
- Distractors are realistic confusions (not gibberish).
- Explanation justifies in 1-2 sentences, grounded in the course.
- Difficulty mix: ~40% easy, ~40% medium, ~20% hard.
- Cover MULTIPLE chapters, not just one.
- Invent NOTHING beyond the provided content.
- Respond ONLY with valid JSON, no text before or after."""

_USER_TEMPLATE_FR = """# Cours (extraits par chapitre)

{content}

---

Produis EXACTEMENT {n} questions QCM au format JSON suivant.
IMPORTANT : les options sont de VRAIES réponses courtes (PAS "Choix A", "Choix B" etc.).

{{
  "questions": [
    {{
      "question": "Texte de la question ?",
      "options": ["réponse 1", "réponse 2", "réponse 3", "réponse 4"],
      "correct_index": 0,
      "explanation": "Justification courte basée sur le cours.",
      "difficulty": "facile"
    }}
  ]
}}

Champs obligatoires : question, options (exactement 4 réponses concrètes), correct_index (0-3), explanation, difficulty ("facile"|"moyen"|"difficile").
Couvre des chapitres variés. Sois CONCIS : options <= 60 caractères, explication <= 150 caractères.
"""

_USER_TEMPLATE_EN = """# Course (extracts by chapter)

{content}

---

Produce EXACTLY {n} MCQ questions in this JSON format.
IMPORTANT: options must be REAL short answers (NOT "Choice A", "Choice B" etc.).

{{
  "questions": [
    {{
      "question": "Question text?",
      "options": ["answer 1", "answer 2", "answer 3", "answer 4"],
      "correct_index": 0,
      "explanation": "Short justification grounded in the course.",
      "difficulty": "easy"
    }}
  ]
}}

Required fields: question, options (exactly 4 concrete answers), correct_index (0-3), explanation, difficulty ("easy"|"medium"|"hard").
Cover varied chapters. Be CONCISE: options <= 60 chars, explanation <= 150 chars.
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
            retries=1,
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


def _validate_question(q: dict, source: str, qid: int) -> Optional[dict]:
    """Valide et normalise une question. Retourne None si invalide."""
    if not isinstance(q, dict):
        return None
    text = (q.get("question") or "").strip()
    options = q.get("options")
    correct = q.get("correct_index")
    explanation = (q.get("explanation") or "").strip()

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
    }
