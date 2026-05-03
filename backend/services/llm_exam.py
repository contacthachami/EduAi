"""Service de génération de questions d'examen via LLM."""

import json
import logging
from typing import List

from backend.services.llm_client import get_client, LLMUnavailable

logger = logging.getLogger(__name__)

EXAM_PROMPT = """Tu es un examinateur universitaire rigoureux. Génère exactement {count} questions QCM d'examen à partir du contenu suivant.

Règles strictes :
- Questions variées couvrant l'ensemble du contenu (pas seulement le début)
- Mix de difficultés : 30% facile, 50% moyen, 20% difficile
- 4 options par question, UNE SEULE correcte
- Les distracteurs doivent être plausibles (pas de réponses évidentes)
- Les questions "difficile" doivent tester la compréhension profonde, pas la mémorisation
- Inclure des questions d'application et d'analyse (pas juste des définitions)
- Explications détaillées pour chaque réponse correcte

Format JSON strict :
{{"questions": [{{"question": "...", "options": ["A...", "B...", "C...", "D..."], "correct_index": 0, "explanation": "...", "difficulty": "facile|moyen|difficile"}}]}}

Contenu du cours :
---
{content}
---

Génère exactement {count} questions d'examen en JSON :
{{"questions": [...]}}"""


async def generate_exam_questions(chunks: list[dict], count: int = 15) -> List[dict]:
    """Génère des questions d'examen diversifiées depuis les chunks."""
    # Sélectionner du contenu de manière large
    content = _build_exam_content(chunks, max_chars=6000)

    prompt = EXAM_PROMPT.format(content=content, count=count)

    client = get_client()
    available = await client.is_available()
    if not available:
        raise LLMUnavailable("LLM indisponible pour la génération d'examen.")

    raw = await client.generate_json(prompt)

    try:
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw

        # Groq json_object mode returns a dict — unwrap the questions list
        if isinstance(data, list):
            questions = data
        elif isinstance(data, dict):
            for key in ("questions", "items", "exam", "data"):
                if key in data and isinstance(data[key], list):
                    questions = data[key]
                    break
            else:
                questions = next((v for v in data.values() if isinstance(v, list)), [])
        else:
            questions = []
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Échec parsing JSON exam: %s | raw=%s", exc, str(raw)[:200])
        raise LLMUnavailable("Impossible de générer les questions d'examen.")

    # Valider
    valid = []
    for q in questions:
        if (isinstance(q, dict) and "question" in q and "options" in q
                and "correct_index" in q and len(q.get("options", [])) >= 3):
            valid.append({
                "question": str(q["question"]).strip(),
                "options": [str(o).strip() for o in q["options"][:4]],
                "correct_index": int(q["correct_index"]),
                "explanation": str(q.get("explanation", "")).strip(),
                "difficulty": q.get("difficulty", "moyen"),
            })

    if len(valid) < 3:
        raise LLMUnavailable("Pas assez de questions valides générées.")

    return valid[:count]


def _build_exam_content(chunks: list[dict], max_chars: int = 6000) -> str:
    """Construit un contenu d'examen couvrant tous les chapitres."""
    by_chapter = {}
    for c in chunks:
        ch = c.get("chapter", "Général")
        by_chapter.setdefault(ch, []).append(c.get("text", ""))

    parts = []
    chars_per_chapter = max_chars // max(1, len(by_chapter))

    for ch, texts in by_chapter.items():
        combined = " ".join(texts)[:chars_per_chapter]
        parts.append(f"## {ch}\n{combined}")

    return "\n\n".join(parts)[:max_chars]
