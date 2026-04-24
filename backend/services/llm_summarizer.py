"""Reformulation pédagogique des chapitres via LLM local (Ollama).

Pipeline hybride :
    1. summarizer.summarize_course() → fournit pour chaque chapitre :
         - bullets nettoyés (extractive)
         - concepts-clés
         - liste pages
    2. llm_summarizer.refine_chapter() → reformule en fiche de révision :
         Objectifs · Concepts clés · Exemples · Formules · À retenir · Pièges

Le LLM voit UNIQUEMENT le matériel extrait (pas le PDF brut) afin :
    - d'éviter le bruit (watermarks, ligatures, en-têtes)
    - de rester ancré dans le cours (anti-hallucination)
    - de tenir dans 8k tokens contexte
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

from backend.config import get_settings
from backend.services.llm_client import LLMUnavailable, get_client

logger = logging.getLogger(__name__)

# ── Détection langue (heuristique simple, évite dépendance) ────────

_FR_TOKENS = {"le", "la", "les", "des", "une", "un", "et", "est", "dans", "pour",
              "avec", "sur", "ce", "cette", "qui", "que", "aux", "du", "au"}
_EN_TOKENS = {"the", "and", "of", "to", "in", "for", "is", "with", "on", "this",
              "that", "are", "as", "be", "by", "an", "or", "from", "it"}


def _detect_lang(text: str) -> str:
    """Retourne 'fr' ou 'en' (FR par défaut)."""
    words = re.findall(r"[a-zA-ZÀ-ÿ]+", text.lower())
    if not words:
        return "fr"
    sample = words[:400]
    fr = sum(1 for w in sample if w in _FR_TOKENS)
    en = sum(1 for w in sample if w in _EN_TOKENS)
    return "en" if en > fr * 1.3 else "fr"


# ── Prompts ────────────────────────────────────────────────────────

_SYSTEM_FR = """Tu es un rédacteur pédagogique professionnel. Tu produis des résumés de chapitres de cours universitaires : clairs, denses, en prose continue, fidèles au contenu source.

RÈGLES IMPOSSIBLES À ENFREINDRE :
- Tu ÉCRIS UNIQUEMENT EN FRANÇAIS.
- Tu n'inventes RIEN qui ne soit pas dans les extraits fournis.
- AUCUN émoji, AUCUN icône, AUCUN symbole décoratif.
- AUCUNE liste à puces, AUCUN tiret en début de ligne. Uniquement des paragraphes en prose continue.
- AUCUN titre de section intermédiaire (pas de `## Introduction`, `## Définitions`, etc.).
- Style : phrases complètes, ton neutre encyclopédique, vocabulaire technique précis.
- Pas de préambule type "Voici le résumé". Commence DIRECTEMENT par la ligne `# Titre`."""

_SYSTEM_EN = """You are a professional academic writer. You produce university course chapter summaries: clear, dense, in continuous prose, faithful to the source material.

MANDATORY RULES:
- You write IN ENGLISH ONLY.
- Invent NOTHING outside the provided extracts.
- NO emojis, NO icons, NO decorative symbols.
- NO bullet lists, NO leading dashes. Only continuous prose paragraphs.
- NO intermediate section headings.
- Style: full sentences, neutral encyclopedic tone, precise technical vocabulary.
- No preamble. Start DIRECTLY with the line `# Title`."""

_USER_TEMPLATE_FR = """Tu vas résumer un chapitre d'un cours universitaire. Voici les extraits du chapitre tels qu'ils apparaissent dans le PDF source :

--- DÉBUT EXTRAITS ---
{bullets}
--- FIN EXTRAITS ---

Titre brut détecté (souvent incorrect, à reformuler) : {title}

Produis ta réponse en respectant EXACTEMENT ce gabarit Markdown, dans cet ordre, sans rien ajouter avant ou après :

# <Titre court et précis du chapitre, 4 à 8 mots, sans numérotation, sans le mot "Chapitre">

<Premier paragraphe : 3 à 5 phrases. Décris le SUJET principal du chapitre : de quoi traite-t-il, quel problème il aborde, dans quel contexte. Reste en prose continue.>

<Deuxième paragraphe : 4 à 6 phrases. Développe les NOTIONS, méthodes, algorithmes ou concepts présentés, avec leurs définitions essentielles et leurs relations. Cite les techniques nommées dans les extraits.>

<Troisième paragraphe (optionnel) : 2 à 4 phrases. Mentionne les exemples concrets, formules, ou applications pratiques présentés dans le chapitre.>

**Concepts-clés :** terme1, terme2, terme3, terme4, terme5

INSTRUCTIONS FINALES :
- Le titre doit refléter le VRAI sujet (ex : "Tokenisation et nettoyage de texte", "Algorithme de Lancaster Stemmer", "Réseaux LSTM et mémoire à long terme").
- Les paragraphes ne doivent PAS contenir de listes à puces ni de tirets en début de ligne.
- Les concepts-clés sont 4 à 6 termes techniques précis du chapitre (noms communs ou propres, pas de verbes).
- Pas d'émoji nulle part. Pas de markdown gras dans les paragraphes (sauf concepts-clés).
"""

_USER_TEMPLATE_EN = """You will summarize a chapter of a university course. Here are the extracts as they appear in the source PDF:

--- BEGIN EXTRACTS ---
{bullets}
--- END EXTRACTS ---

Raw detected title (often incorrect, to be rewritten): {title}

Produce your reply following EXACTLY this Markdown template, in this order, with nothing before or after:

# <Short precise chapter title, 4-8 words, no numbering, no "Chapter">

<First paragraph: 3-5 sentences. Describe the main SUBJECT of the chapter: what it covers, what problem it addresses, in what context. Continuous prose.>

<Second paragraph: 4-6 sentences. Develop the NOTIONS, methods, algorithms or concepts presented, with essential definitions and relationships. Cite techniques named in the extracts.>

<Third paragraph (optional): 2-4 sentences. Mention concrete examples, formulas, or practical applications presented in the chapter.>

**Key concepts:** term1, term2, term3, term4, term5

FINAL INSTRUCTIONS:
- The title must reflect the REAL subject.
- Paragraphs must NOT contain bullet lists or leading dashes.
- Key concepts are 4-6 precise technical terms from the chapter.
- No emoji anywhere. No bold within paragraphs (except key concepts line).
"""


# ── Fonction publique ──────────────────────────────────────────────

async def refine_chapter(
    title: str,
    bullets: str,
    key_concepts: list[str] | None = None,
    *,
    lang_hint: Optional[str] = None,
) -> Optional[dict]:
    """Reformule un chapitre en fiche pédagogique Markdown.

    Retourne un dict {title, body, key_concepts} si succès, None si indispo.
    - title : titre reformulé par le LLM (str)
    - body  : fiche Markdown complète (avec le `# Titre` en tête)
    - key_concepts : liste de termes techniques (list[str])
    Le caller doit fallback sur le résumé extractif si None.
    """
    settings = get_settings()
    if not settings.enable_llm:
        return None

    client = get_client()
    if not await client.is_available():
        return None

    # Tronque pour rester sous num_ctx
    truncated = bullets
    max_chars = settings.ollama_max_chunk_chars
    if len(truncated) > max_chars:
        truncated = truncated[:max_chars] + "\n[…tronqué…]"

    lang = lang_hint or _detect_lang(f"{title}\n{bullets}")
    system = _SYSTEM_FR if lang == "fr" else _SYSTEM_EN
    template = _USER_TEMPLATE_FR if lang == "fr" else _USER_TEMPLATE_EN

    user = template.format(
        title=title.strip() or ("Sans titre" if lang == "fr" else "Untitled"),
        bullets=truncated,
    )

    try:
        out = await client.chat(
            system=system,
            user=user,
            temperature=settings.ollama_temperature_summary,
            max_tokens=settings.ollama_max_tokens_summary,
            retries=1,
        )
        return _parse_llm_output(_post_clean(out), fallback_title=title)
    except LLMUnavailable as exc:
        logger.warning("LLM refine_chapter indisponible (%s) → fallback", exc)
        return None
    except Exception:
        logger.exception("Erreur inattendue refine_chapter")
        return None


# Regex pour extraire la ligne `# Titre` en tête de fiche
_TITLE_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
# Regex pour extraire la dernière ligne `**Concepts-clés :** ...` ou `**Key concepts:** ...`
# Tolérant : accents optionnels (le LLM oublie parfois), tiret optionnel, espaces variables.
_CONCEPTS_RE = re.compile(
    r"\*\*\s*(?:Concepts?[\s\-]*cl[ée]?s?|Key\s*concepts?)\s*:\s*\*\*\s*(.+?)\s*$",
    re.MULTILINE | re.IGNORECASE,
)

# Regex pour supprimer les emojis (tous les blocs Unicode émoji + symboles décoratifs)
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"  # symboles & pictogrammes
    "\U0001F600-\U0001F64F"  # émoticons
    "\U0001F680-\U0001F6FF"  # transport
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"  # symboles supplémentaires
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"  # divers symboles
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F1E0-\U0001F1FF"  # drapeaux
    "]+",
    flags=re.UNICODE,
)


def _parse_llm_output(md: str, *, fallback_title: str) -> dict:
    """Extrait le titre, le corps Markdown et les concepts-clés de la sortie LLM.

    Tolérant : si le LLM ne respecte pas le format, on fallback sur les valeurs
    extractives sans casser le pipeline.
    """
    body = md

    # 1) Extraire le titre (première ligne `# ...`)
    title = fallback_title.strip() or "Sans titre"
    m = _TITLE_RE.search(md)
    if m:
        candidate = m.group(1).strip().strip(":—-")
        # Nettoyage : retirer préfixes type "Chapitre N :", "Chapter N:"
        candidate = re.sub(
            r"^(?:chapitre|chapter)\s*\d*\s*[:\u2014\-]\s*",
            "",
            candidate,
            flags=re.IGNORECASE,
        ).strip()
        if candidate and len(candidate) <= 120:
            title = candidate
        # Retirer cette ligne du body (on reconstruira)
        body = (md[:m.start()] + md[m.end():]).lstrip("\n")

    # 2) Extraire les concepts-clés (dernière ligne)
    concepts: list[str] = []
    cm = _CONCEPTS_RE.search(body)
    if cm:
        raw = cm.group(1)
        # Split par virgule/point-virgule, nettoyer
        parts = re.split(r"[,;•\u2013\u2014]\s*", raw)
        for p in parts:
            term = p.strip().strip(".—-:·•").strip("*_`")
            if term and 2 <= len(term) <= 60:
                concepts.append(term)
        # Retirer cette ligne du body
        body = body[:cm.start()].rstrip() + "\n"

    # 3) Reconstruire le body avec le titre en tête (pour l'affichage Markdown)
    body = body.strip()

    return {
        "title": title,
        "body": body,
        "key_concepts": concepts[:6],
    }


def _post_clean(md: str) -> str:
    """Nettoyage : enlève fences, emojis, listes, normalise sauts de ligne.

    Le format demandé est narratif (paragraphes uniquement) ; on supprime
    défensivement tout ce que le LLM aurait pu glisser malgré les instructions.
    """
    s = md.strip()
    # Enlève fences markdown si présents
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s.rsplit("```", 1)[0]
    # Supprime tous les emojis
    s = _EMOJI_RE.sub("", s)
    # Convertit les éventuelles puces en début de ligne en phrases continues
    # (le modèle glisse parfois "- xxx" ou "• xxx")
    lines = []
    for line in s.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith(("- ", "* ", "• ", "– ", "— ")):
            # Retire la puce, garde le contenu en ligne courante
            lines.append(stripped[2:].strip())
        else:
            lines.append(line)
    s = "\n".join(lines)
    # Compacte plus de 2 sauts de ligne
    s = re.sub(r"\n{3,}", "\n\n", s)
    # Trim espaces multiples introduits par la suppression d'émojis
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()


# ── Helper sync pour les tests ─────────────────────────────────────

def refine_chapter_sync(title: str, bullets: str, key_concepts: list[str]) -> Optional[str]:
    """Wrapper synchrone (utile en script de test). N'utilisez pas dans le router async."""
    return asyncio.run(refine_chapter(title, bullets, key_concepts))
