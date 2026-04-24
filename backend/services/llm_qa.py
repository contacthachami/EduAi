"""RAG conversationnel via LLM local (Ollama) — pour le Q&A étudiant.

Pipeline :
1. Embedding de la question (sentence-transformers, déjà chargé)
2. Recherche FAISS top-5 dans les chunks du cours
3. Construction d'un prompt avec contexte numéroté + citations
4. Appel LLM (mode strict "réponds uniquement à partir des extraits")
5. Retour avec sources (page, chapitre, score, extrait)

Si aucun chunk n'est pertinent → message "info introuvable" sans appeler le LLM.
"""
from __future__ import annotations

import logging
from typing import AsyncIterator, Optional

from backend.config import get_settings
from backend.services.llm_client import LLMUnavailable, get_client
from backend.services.llm_summarizer import _detect_lang

logger = logging.getLogger(__name__)


_SYSTEM_FR = """Tu es un assistant pédagogique pour un étudiant. Tu réponds aux questions UNIQUEMENT à partir des extraits de cours fournis.

RÈGLES STRICTES :
- N'utilise QUE les extraits ci-dessous. N'invoque pas tes connaissances générales.
- Si la réponse n'est pas dans les extraits, réponds exactement : "Cette information n'est pas couverte dans le cours fourni."
- Cite tes sources entre crochets : [1], [2]… correspondant aux numéros d'extraits.
- Sois clair, pédagogique, structuré (listes si utile). 3 à 8 phrases maximum.
- Réponds dans la même langue que la question."""

_SYSTEM_EN = """You are a pedagogical assistant for a student. You answer questions ONLY from the provided course extracts.

STRICT RULES:
- Use ONLY the extracts below. Do not invoke your general knowledge.
- If the answer is not in the extracts, reply exactly: "This information is not covered in the provided course."
- Cite sources in brackets: [1], [2]… matching the extract numbers.
- Be clear, pedagogical, structured (lists if useful). 3 to 8 sentences max.
- Reply in the same language as the question."""


def _build_user_prompt(question: str, contexts: list[dict], lang: str) -> str:
    parts = []
    if lang == "fr":
        parts.append("# Extraits du cours")
    else:
        parts.append("# Course extracts")
    for i, c in enumerate(contexts, start=1):
        page = c.get("page", "?")
        chap = (c.get("chapter") or "").strip()
        header = f"[{i}] (p.{page}" + (f" — {chap}" if chap else "") + ")"
        text = c.get("text", "").strip().replace("\n", " ")
        if len(text) > 1500:
            text = text[:1500] + "…"
        parts.append(f"{header}\n{text}")
    parts.append("---")
    if lang == "fr":
        parts.append(f"# Question de l'étudiant\n{question.strip()}\n\n# Réponse")
    else:
        parts.append(f"# Student question\n{question.strip()}\n\n# Answer")
    return "\n\n".join(parts)


async def answer_with_llm(
    question: str,
    contexts: list[dict],
) -> Optional[str]:
    """Génère une réponse via LLM. Retourne None si indisponible."""
    settings = get_settings()
    if not settings.enable_llm or not contexts:
        return None

    client = get_client()
    if not await client.is_available():
        return None

    lang = _detect_lang(question)
    system = _SYSTEM_FR if lang == "fr" else _SYSTEM_EN
    user = _build_user_prompt(question, contexts, lang)

    try:
        return await client.chat(
            system=system,
            user=user,
            temperature=settings.ollama_temperature_qa,
            max_tokens=settings.ollama_max_tokens_qa,
            retries=1,
        )
    except LLMUnavailable as exc:
        logger.warning("LLM Q&A indisponible (%s) → fallback extractif", exc)
        return None
    except Exception:
        logger.exception("Erreur LLM Q&A")
        return None


async def stream_answer_with_llm(
    question: str,
    contexts: list[dict],
) -> AsyncIterator[str]:
    """Stream token-by-token. Yield des fragments. Lève LLMUnavailable si KO."""
    settings = get_settings()
    if not settings.enable_llm or not contexts:
        raise LLMUnavailable("LLM désactivé ou pas de contexte")

    client = get_client()
    lang = _detect_lang(question)
    system = _SYSTEM_FR if lang == "fr" else _SYSTEM_EN
    user = _build_user_prompt(question, contexts, lang)

    async for chunk in client.chat_stream(
        system=system,
        user=user,
        temperature=settings.ollama_temperature_qa,
    ):
        yield chunk
