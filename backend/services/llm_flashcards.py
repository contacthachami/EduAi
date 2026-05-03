"""Service de génération de flashcards via LLM."""

import json
import logging
from typing import List

from backend.services.llm_client import get_client, LLMUnavailable

logger = logging.getLogger(__name__)

FLASHCARD_PROMPT = """Tu es un expert en pédagogie. À partir du contenu de cours suivant, génère exactement {count} flashcards pour aider un étudiant à mémoriser les concepts clés.

Chaque flashcard doit avoir :
- "front" : une question claire et concise
- "back" : la réponse précise et complète (2-3 phrases max)
- "difficulty" : "facile", "moyen" ou "difficile"

IMPORTANT :
- Varie les types de questions (définitions, comparaisons, applications, processus)
- Couvre différentes parties du contenu
- Les réponses doivent être auto-suffisantes (compréhensibles sans le contexte)
- Réponds UNIQUEMENT en JSON valide avec exactement ce format : {{"flashcards": [...]}}

Contenu du cours :
---
{content}
---

Génère exactement {count} flashcards au format JSON :
{{"flashcards": [
  {{"front": "question 1 ?", "back": "réponse 1.", "difficulty": "moyen"}},
  {{"front": "question 2 ?", "back": "réponse 2.", "difficulty": "facile"}}
]}}"""


async def generate_flashcards_from_chunks(chunks: list[dict], count: int = 10) -> List[dict]:
    """Génère des flashcards depuis les chunks d'un cours."""
    # Sélectionner un échantillon représentatif des chunks
    selected = _select_representative_chunks(chunks, max_chars=5000)
    content = "\n\n".join(c["text"] for c in selected)

    prompt = FLASHCARD_PROMPT.format(content=content, count=count)

    client = get_client()
    available = await client.is_available()
    if not available:
        raise LLMUnavailable("LLM indisponible pour la génération de flashcards.")

    raw = await client.generate_json(prompt)

    # Parser le JSON et normaliser en liste
    try:
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw

        # Groq json_object mode always returns a dict — unwrap the list inside
        if isinstance(data, list):
            cards = data
        elif isinstance(data, dict):
            # Try common wrapper keys
            for key in ("flashcards", "cards", "items", "questions", "data"):
                if key in data and isinstance(data[key], list):
                    cards = data[key]
                    break
            else:
                # Take the first list value found
                cards = next((v for v in data.values() if isinstance(v, list)), [])
        else:
            cards = []
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Échec parsing JSON flashcards: %s | raw=%s", exc, str(raw)[:200])
        cards = _fallback_flashcards(chunks, count)

    # Valider et nettoyer
    valid_cards = []
    for card in cards[:count]:
        if isinstance(card, dict) and "front" in card and "back" in card:
            valid_cards.append({
                "front": str(card["front"]).strip(),
                "back": str(card["back"]).strip(),
                "difficulty": card.get("difficulty", "moyen"),
            })

    # Si pas assez de cartes, compléter avec le fallback
    if len(valid_cards) < count:
        fallback = _fallback_flashcards(chunks, count - len(valid_cards))
        valid_cards.extend(fallback)

    return valid_cards[:count]


def _select_representative_chunks(chunks: list[dict], max_chars: int = 5000) -> list[dict]:
    """Sélectionne des chunks variés en couvrant différents chapitres."""
    if not chunks:
        return []

    # Grouper par chapitre
    by_chapter = {}
    for c in chunks:
        ch = c.get("chapter", "Général")
        by_chapter.setdefault(ch, []).append(c)

    selected = []
    total_chars = 0
    chapters = list(by_chapter.keys())

    # Round-robin entre chapitres
    idx = 0
    while total_chars < max_chars and any(by_chapter.values()):
        ch = chapters[idx % len(chapters)]
        if by_chapter[ch]:
            chunk = by_chapter[ch].pop(0)
            text = chunk.get("text", "")
            if total_chars + len(text) <= max_chars:
                selected.append(chunk)
                total_chars += len(text)
        idx += 1
        if idx > len(chunks):
            break

    return selected


def _fallback_flashcards(chunks: list[dict], count: int) -> list[dict]:
    """Génération basique de flashcards sans LLM (fallback)."""
    cards = []
    for chunk in chunks[:count]:
        text = chunk.get("text", "").strip()
        if len(text) > 50:
            # Extraire la première phrase comme question
            sentences = text.split(".")
            if len(sentences) >= 2:
                cards.append({
                    "front": f"Que signifie : « {sentences[0].strip()[:100]} » ?",
                    "back": sentences[1].strip()[:200] if len(sentences) > 1 else text[:200],
                    "difficulty": "moyen",
                })
    return cards[:count]
