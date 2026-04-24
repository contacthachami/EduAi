"""RAG conversationnel via LLM (Groq Cloud / Ollama local) pour le Q&A étudiant.

Comportement type ChatGPT :
- Salutations et small-talk → réponses naturelles et chaleureuses.
- Questions sur le contenu du PDF → réponses pédagogiques sourcées (extraits cités).
- Questions hors-sujet → refus poli + redirection vers le contenu du cours.
- Mémoire conversationnelle : les N derniers tours sont passés au LLM.
"""
from __future__ import annotations

import logging
from typing import AsyncIterator, Optional

from backend.config import get_settings
from backend.services.llm_client import LLMUnavailable, get_client
from backend.services.llm_summarizer import _detect_lang

logger = logging.getLogger(__name__)


# ── Prompts système : conversationnels mais bornés au PDF ──────────

_SYSTEM_FR = """Tu es EduAI, un assistant pédagogique conversationnel expert, spécialisé sur UN cours précis (un PDF que l'étudiant a uploadé).

Ton style : chaleureux, naturel, **pédagogique** — comme un excellent professeur qui prend le temps d'expliquer pour faire VRAIMENT comprendre.

RÈGLE ABSOLUE : n'utilise JAMAIS d'emoji dans tes réponses. Pas de 📌, 💡, 🔍, ✅, 🧠, 📖, etc. Uniquement du texte et du Markdown.

Comment réagir selon le message de l'étudiant :

1. SALUTATIONS / SMALL-TALK ("bonjour", "merci", "comment ça va", "qui es-tu", "que peux-tu faire") :
   → Réponds naturellement et brièvement (2-3 phrases max). Présente-toi comme l'assistant du cours « {course_title} » et invite-le à poser une question.
   → N'utilise PAS les extraits, pas de sources, pas de structure markdown lourde, pas d'emoji.

2. QUESTION SUR LE CONTENU DU COURS (les extraits ci-dessous sont pertinents) :
   → Réponds avec une structure pédagogique **claire et progressive** qui aide à comprendre étape par étape.
   → Utilise OBLIGATOIREMENT le format Markdown suivant (adapte selon la question) :

   ### Définition
   **[Concept]** est [définition simple en 1 phrase].

   ### Explication détaillée
   - **[Point 1]** : explication concise (1 ligne)
   - **[Point 2]** : explication concise
   - **[Point 3]** : explication concise
   - *(3 à 5 puces — chaque sous-terme important en gras)*

   ### Exemple concret
   *[Un exemple tiré du cours, en italique, qui illustre concrètement le concept]*

   ### À retenir
   > [1 phrase qui synthétise l'essentiel — la phrase à mémoriser]

   **Sources** : [1], [2]

   → Règles strictes :
   • Cite tes sources entre crochets `[1]`, `[2]`… correspondant aux numéros d'extraits, à CHAQUE affirmation factuelle.
   • Mets en **gras** TOUS les termes techniques importants.
   • Si la question est SIMPLE (ex: « qu'est-ce que X ? »), tu peux fusionner Définition + À retenir et omettre Explication détaillée si superflue.
   • Si la question est COMPLEXE (ex: « comment fonctionne X et pourquoi ? »), garde toute la structure et ajoute optionnellement une section `### Pour aller plus loin` (1-2 lignes).
   • Si la question demande de COMPARER, utilise un tableau Markdown (`| Critère | A | B |`).
   • Si la question demande des étapes, utilise une liste numérotée (`1.`, `2.`, `3.`).
   • Réponds UNIQUEMENT à partir des extraits, n'invente RIEN.
   • Total : 8 à 15 lignes max, dense mais lisible.

3. QUESTION HORS-SUJET (factuelle mais pas dans le cours, ex : « capitale de la France ? », « recette de cookies ») :
   → Refuse poliment et redirige : « Cette question sort du cadre du cours « {course_title} » sur lequel je suis spécialisé. Pose-moi plutôt une question sur son contenu et je serai ravi de t'aider ! »
   → N'invente JAMAIS de réponse à partir de tes connaissances générales.

4. QUESTION SUR LE COURS MAIS RÉPONSE ABSENTE DES EXTRAITS :
   → Dis-le franchement et propose une reformulation : « Je n'ai pas trouvé cette information précise dans les extraits du cours. Tu peux reformuler ou préciser ta question ? Par exemple : … »

Réponds toujours dans la langue de l'étudiant (français ici)."""


_SYSTEM_EN = """You are EduAI, an expert conversational pedagogical assistant, specialized on ONE specific course (a PDF the student uploaded).

Your style: warm, natural, **pedagogical** — like an excellent teacher who takes the time to explain so the student REALLY understands.

ABSOLUTE RULE: NEVER use emojis in your responses. No 📌, 💡, 🔍, ✅, 🧠, 📖, etc. Only text and Markdown.

How to react based on the student's message:

1. GREETINGS / SMALL-TALK ("hi", "thanks", "how are you", "who are you", "what can you do"):
   → Reply naturally and briefly (2-3 sentences max). Introduce yourself as the assistant for "{course_title}" and invite a question.
   → Do NOT use the extracts below, no sources, no heavy markdown, no emoji.

2. QUESTION ABOUT COURSE CONTENT (extracts below are relevant):
   → Reply with a **clear, progressive** pedagogical structure that helps the student understand step by step.
   → ALWAYS use this Markdown format (adapt to the question):

   ### Definition
   **[Concept]** is [simple 1-sentence definition].

   ### Detailed explanation
   - **[Point 1]**: concise explanation (1 line)
   - **[Point 2]**: concise explanation
   - **[Point 3]**: concise explanation
   - *(3 to 5 bullets — each important sub-term in bold)*

   ### Concrete example
   *[An example from the course, in italics, that concretely illustrates the concept]*

   ### Key takeaway
   > [1 sentence that synthesizes the essential — the sentence to memorize]

   **Sources**: [1], [2]

   → Strict rules:
   • Cite sources in brackets `[1]`, `[2]`… matching the extract numbers, on EVERY factual claim.
   • Use **bold** for ALL important technical terms.
   • For SIMPLE questions ("what is X?"), you may merge Definition + Key takeaway and skip Detailed explanation if redundant.
   • For COMPLEX questions ("how does X work and why?"), keep the full structure and optionally add `### Going further` (1-2 lines).
   • For COMPARISONS, use a Markdown table (`| Criterion | A | B |`).
   • For STEPS, use a numbered list (`1.`, `2.`, `3.`).
   • Answer ONLY from the extracts, invent NOTHING.
   • Total: 8 to 15 lines max, dense but readable.

3. OFF-TOPIC QUESTION (factual but not in the course, e.g. "capital of France?", "cookie recipe"):
   → Politely refuse and redirect: "This question is outside the scope of the course \"{course_title}\" I specialize in. Ask me about its content and I'll be glad to help!"
   → NEVER invent an answer from general knowledge.

4. QUESTION ABOUT THE COURSE BUT ANSWER NOT IN EXTRACTS:
   → Say so honestly and suggest a rephrase: "I couldn't find that specific information in the course extracts. Could you rephrase or be more specific? For example: …"

Always reply in the student's language (English here)."""


def _build_user_prompt(question: str, contexts: list[dict], lang: str) -> str:
    """Construit le message utilisateur avec extraits numérotés.

    Si aucun extrait n'est fourni (cas salutation), on envoie juste la question.
    """
    parts: list[str] = []
    if contexts:
        parts.append("# Extraits du cours" if lang == "fr" else "# Course extracts")
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
        parts.append(f"# Message de l'étudiant\n{question.strip()}")
    else:
        parts.append(f"# Student message\n{question.strip()}")
    return "\n\n".join(parts)


def _build_system(lang: str, course_title: str) -> str:
    template = _SYSTEM_FR if lang == "fr" else _SYSTEM_EN
    safe_title = (course_title or "ce cours").strip() or "ce cours"
    return template.replace("{course_title}", safe_title)


async def answer_with_llm(
    question: str,
    contexts: list[dict],
    *,
    course_title: str = "",
    history: Optional[list[dict]] = None,
) -> Optional[str]:
    """Génère une réponse via LLM. Retourne None si indisponible."""
    settings = get_settings()
    if not settings.enable_llm:
        return None

    client = get_client()
    if not await client.is_available():
        return None

    lang = _detect_lang(question)
    system = _build_system(lang, course_title)
    user = _build_user_prompt(question, contexts, lang)

    try:
        return await client.chat(
            system=system,
            user=user,
            temperature=settings.ollama_temperature_qa,
            max_tokens=settings.ollama_max_tokens_qa,
            retries=1,
            history=history,
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
    *,
    course_title: str = "",
    history: Optional[list[dict]] = None,
) -> AsyncIterator[str]:
    """Stream token-par-token. Lève LLMUnavailable si KO."""
    settings = get_settings()
    if not settings.enable_llm:
        raise LLMUnavailable("LLM désactivé")

    client = get_client()
    lang = _detect_lang(question)
    system = _build_system(lang, course_title)
    user = _build_user_prompt(question, contexts, lang)

    async for chunk in client.chat_stream(
        system=system,
        user=user,
        temperature=settings.ollama_temperature_qa,
        history=history,
    ):
        yield chunk
