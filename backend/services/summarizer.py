"""Résumé automatique par chapitre — approche extractive intelligente.

Nettoie le texte source, score les phrases par pertinence et qualité,
sélectionne les meilleures phrases, et extrait les concepts clés via spaCy.
"""

import logging
import re
import threading

logger = logging.getLogger(__name__)

_nlp = None
_nlp_lock = threading.Lock()


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


# ── Mots génériques à exclure des concepts clés ──────────────────────

_STOP_CONCEPTS = {
    # Noms français ultra-génériques
    "chose", "exemple", "type", "nombre", "message", "ressource",
    "résultat", "manière", "façon", "partie", "point", "moment",
    "lieu", "temps", "forme", "niveau", "ensemble", "figure",
    "page", "chapitre", "cours", "introduction", "conclusion",
    "slide", "section", "image", "tableau", "texte", "question",
    "réponse", "titre", "ligne", "mot", "lettre", "cas", "fait",
    "fois", "jour", "année", "début", "fin", "suite", "reste",
    "côté", "droit", "gauche", "haut", "bas", "tout", "rien",
    "autre", "même", "tel", "certain", "chaque", "plusieurs",
    "quelque", "aucun", "premier", "dernier", "nouveau", "ancien",
    "petit", "grand", "bon", "mauvais", "beau", "long", "court",
    "utilisation", "objectif", "définition", "notion", "pirate",
    "concept", "méthode", "problème", "solution", "donnée",
    "système", "processus", "structure", "modèle", "technique",
    "information", "contenu", "élément", "valeur", "fonction",
    "opération", "action", "effet", "condition", "état",
    "réseau", "attaque", "attack", "mémoire", "bande",
    # English generic
    "example", "type", "number", "result", "part", "point",
    "time", "level", "figure", "image", "table", "text",
}


# ── Nettoyage du texte source ─────────────────────────────────────────

def _clean_source_text(text: str) -> str:
    """Filtre le bruit : code, en-têtes, pieds de page, artefacts PDF,
    et élimine les lignes dupliquées / quasi-dupliquées typiques des PDF slides."""
    lines = text.split("\n")
    kept: list[str] = []
    seen_normalised: list[str] = []          # ordered for substring check

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Lignes de code
        if re.match(r"^(import |from |def |class |print\s*\(|write\s*\(|#\s|>>>|\.\.\.)", stripped):
            continue
        # En-têtes/pieds de page de cours (CSC XXXX, numéros de page isolés)
        if re.match(r"^(CSC\s+\d+|Page\s+\d+)", stripped, re.IGNORECASE):
            continue
        if re.match(r"^\d{1,3}$", stripped):
            continue
        # Lignes avec trop peu de texte alphabétique (formules, symboles)
        alpha = sum(1 for c in stripped if c.isalpha())
        if len(stripped) > 10 and alpha / len(stripped) < 0.35:
            continue
        # Lignes très courtes (< 10 chars)
        if len(stripped) < 10:
            continue

        # ── Déduplication des lignes proches ──
        norm = re.sub(r"\s+", " ", stripped.lower())
        is_dup = False
        replace_idx = -1
        for j, prev in enumerate(seen_normalised):
            # Exact substring containment (either direction)
            if norm in prev:
                is_dup = True
                break
            if prev in norm:
                replace_idx = j
                break
            # Word-overlap: progressive slide disclosure creates lines that
            # share most of their words (same ending, different start).
            n_words = set(norm.split())
            p_words = set(prev.split())
            overlap = len(n_words & p_words)
            smaller = min(len(n_words), len(p_words))
            if smaller >= 4 and overlap / smaller > 0.7:
                # Keep the longer line
                if len(norm) > len(prev):
                    replace_idx = j
                else:
                    is_dup = True
                break
        if is_dup:
            continue
        if replace_idx >= 0:
            seen_normalised[replace_idx] = norm
            kept[replace_idx] = stripped
            continue

        seen_normalised.append(norm)
        kept.append(stripped)

    return " ".join(kept)


# ── Découpage en phrases ──────────────────────────────────────────────

def _split_into_sentences(text: str) -> list[str]:
    """Découpe le texte nettoyé en phrases exploitables."""
    text = re.sub(r"\s+", " ", text).strip()
    raw = re.split(r"(?<=[.!?])\s+", text)
    sentences: list[str] = []
    for s in raw:
        s = s.strip()
        if len(s) < 25:
            continue
        alpha = sum(1 for c in s if c.isalpha())
        if alpha < len(s) * 0.4:
            continue
        sentences.append(s)
    return sentences


# ── Scoring des phrases ───────────────────────────────────────────────

def _score_sentences(
    sentences: list[str],
    chapter_title: str,
) -> list[tuple[float, int, str]]:
    """Attribue un score de pertinence à chaque phrase.

    Critères : position, longueur, diversité lexicale, bruit,
    pertinence au titre, présence de définitions.
    """
    title_words = {w.lower() for w in chapter_title.split() if len(w) > 2}
    total = len(sentences)
    scored: list[tuple[float, int, str]] = []

    for idx, sentence in enumerate(sentences):
        words = sentence.split()
        n_words = len(words)
        if n_words < 5:
            continue

        # Position : début du chapitre = plus informatif
        pos_ratio = idx / max(total, 1)
        if pos_ratio < 0.25:
            position_score = 1.0
        elif pos_ratio > 0.85:
            position_score = 0.85
        else:
            position_score = 0.65

        # Longueur : phrases complètes (10-35 mots)
        if n_words < 8:
            length_score = 0.5
        elif n_words <= 35:
            length_score = min(n_words / 18.0, 1.0)
        else:
            length_score = 0.7

        # Diversité lexicale
        unique_ratio = len(set(w.lower() for w in words)) / n_words

        # Pénalité bruit (symboles de code)
        special = sum(1 for c in sentence if c in "(){}[]=<>|&@#$%^*~`\\")
        noise = 1.0 if special < 3 else (0.5 if special < 6 else 0.2)

        # Bonus pertinence titre
        overlap = len({w.lower() for w in words} & title_words) if title_words else 0
        title_bonus = 1.0 + overlap * 0.15

        # Bonus définitions / explications
        definition = 1.0
        if re.search(
            r"\b(est un|est une|est le|est la|consiste à|permet de|désigne|"
            r"se définit|on appelle|on parle de|on distingue|il existe|"
            r"c['\u2019]est|signifie)\b",
            sentence,
            re.IGNORECASE,
        ):
            definition = 1.3

        # Pénalité listes à puces
        bullet = 0.85 if sentence[0] in "•●■▪→-*" else 1.0

        score = (
            position_score * length_score * unique_ratio
            * noise * title_bonus * definition * bullet
        )
        scored.append((score, idx, sentence))

    return scored


# ── Résumé extractif ──────────────────────────────────────────────────

def _extractive_summary(text: str, chapter_title: str = "", max_sentences: int = 6) -> str:
    """Génère un résumé extractif intelligent d'un chapitre."""
    cleaned = _clean_source_text(text)
    sentences = _split_into_sentences(cleaned)

    # Dédupliquer — fuzzy : si deux phrases partagent >60 % des mots, garder la plus longue
    unique: list[str] = []
    for s in sentences:
        s_words = set(s.lower().split())
        is_dup = False
        for i, existing in enumerate(unique):
            e_words = set(existing.lower().split())
            overlap = len(s_words & e_words)
            smaller = min(len(s_words), len(e_words))
            if smaller > 0 and overlap / smaller > 0.6:
                # Keep the longer / more complete sentence
                if len(s) > len(existing):
                    unique[i] = s
                is_dup = True
                break
        if not is_dup:
            unique.append(s)

    if not unique:
        return cleaned[:300] if cleaned else chapter_title

    scored = _score_sentences(unique, chapter_title)
    scored.sort(key=lambda x: x[0], reverse=True)

    # Sélectionner les meilleures phrases
    top = scored[:max_sentences]
    # Réordonner par position originale pour la cohérence
    top.sort(key=lambda x: x[1])

    parts: list[str] = []
    for _, _, sentence in top:
        s = re.sub(r"^[•●■▪→\-\*]\s*", "", sentence).strip()
        if s and s[-1] not in ".!?":
            s += "."
        parts.append(s)

    result = " ".join(parts)
    return result if len(result) > 30 else (cleaned[:300] if cleaned else chapter_title)


# ── Extraction des concepts clés ──────────────────────────────────────

def _extract_key_concepts(text: str, max_concepts: int = 6) -> list[str]:
    """Extrait les concepts clés pertinents via spaCy NER + noms fréquents."""
    nlp = _get_spacy()
    if nlp is None:
        return []

    doc = nlp(text[:5000])

    concept_scores: dict[str, float] = {}

    # Entités nommées (haute fiabilité)
    for ent in doc.ents:
        if ent.label_ not in ("PERSON", "ORG", "MISC", "LOC", "EVENT", "PRODUCT"):
            continue
        term = ent.text.strip()
        if (len(term) < 3 or len(term) > 40
                or not term[-1].isalnum()
                or re.search(r"[●■▪•→○\(\)\[\]]", term)
                or term.lower() in _STOP_CONCEPTS):
            continue
        concept_scores[term] = concept_scores.get(term, 0) + 2.0

    # Noms fréquents (lemmatisés, ≥ 2 occurrences)
    noun_freq: dict[str, tuple[str, int]] = {}
    for token in doc:
        if token.pos_ not in ("NOUN", "PROPN") or token.is_stop or len(token.text) < 4:
            continue
        lemma = token.lemma_.lower()
        if lemma in _STOP_CONCEPTS or not lemma.isalpha():
            continue
        display = token.text.strip().capitalize()
        if lemma not in noun_freq:
            noun_freq[lemma] = (display, 0)
        _, cnt = noun_freq[lemma]
        noun_freq[lemma] = (noun_freq[lemma][0], cnt + 1)

    for lemma, (display, count) in noun_freq.items():
        if count >= 2 and display not in concept_scores:
            concept_scores[display] = count * 0.5

    # Trier et filtrer
    sorted_concepts = sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)
    concepts: list[str] = []
    seen_lower: set[str] = set()
    for term, _ in sorted_concepts:
        lower = term.lower()
        if lower not in seen_lower and lower not in _STOP_CONCEPTS:
            seen_lower.add(lower)
            concepts.append(term)
            if len(concepts) >= max_concepts:
                break

    return concepts


# ── Résumé d'un chapitre ──────────────────────────────────────────────

def summarize_chapter(chapter_text: str, chapter_title: str, pages: list[int]) -> dict:
    """Génère un résumé extractif pour un chapitre.

    Args:
        chapter_text: Texte complet du chapitre.
        chapter_title: Titre du chapitre.
        pages: Numéros de pages du chapitre.

    Returns:
        Dict avec title, summary, pages, key_concepts.
    """
    summary = _extractive_summary(chapter_text, chapter_title)
    key_concepts = _extract_key_concepts(chapter_text)

    return {
        "title": chapter_title,
        "summary": summary,
        "pages": pages,
        "key_concepts": key_concepts,
    }


# ---------------------------------------------------------------------------
# Merge chapters — regroupe les petits chapitres en sections logiques
# ---------------------------------------------------------------------------

def _merge_chapters_for_summary(
    raw_chapters: list[dict],
    min_content_chars: int = 300,
    max_chapters: int = 12,
) -> list[dict]:
    """Fusionne les chapitres trop petits en sections logiques.

    Pour les PDFs de présentation, chaque slide crée un chapitre distinct.
    Cette fonction les regroupe en sections cohérentes.

    Chaque élément de raw_chapters: {"title": str, "text": str, "pages": set[int]}
    """
    if not raw_chapters:
        return []

    # Phase 1 : Fusionner en avant — les chapitres trop petits absorbent le suivant
    merged: list[dict] = []
    buffer: dict | None = None

    for ch in raw_chapters:
        if buffer is None:
            buffer = {
                "title": ch["title"],
                "text": ch["title"] + "\n" + ch["text"],
                "pages": set(ch["pages"]),
            }
        else:
            # Ajouter le texte de ce chapitre dans le buffer
            buffer["text"] += "\n\n" + ch["title"] + "\n" + ch["text"]
            buffer["pages"] |= set(ch["pages"])

        # Si le buffer a assez de contenu, on le sauve et on recommence
        content_len = len(buffer["text"].strip())
        if content_len >= min_content_chars:
            merged.append(buffer)
            buffer = None

    # Ne pas perdre le dernier buffer
    if buffer is not None:
        if merged:
            # Fusionner avec le dernier chapitre plutôt que d'avoir un reste trop petit
            merged[-1]["text"] += "\n\n" + buffer["text"]
            merged[-1]["pages"] |= buffer["pages"]
        else:
            merged.append(buffer)

    # Phase 2 : Si encore trop de chapitres, fusionner itérativement les plus petits
    while len(merged) > max_chapters:
        min_idx = min(range(len(merged)), key=lambda j: len(merged[j]["text"]))
        if min_idx < len(merged) - 1:
            merge_with = min_idx + 1
        else:
            merge_with = min_idx - 1
        a, b = min(min_idx, merge_with), max(min_idx, merge_with)
        merged[a]["text"] += "\n\n" + merged[b]["text"]
        merged[a]["pages"] |= merged[b]["pages"]
        merged.pop(b)

    logger.info(
        "Fusion chapitres : %d → %d sections",
        len(raw_chapters),
        len(merged),
    )
    return merged


def summarize_course(chunks: list[dict]) -> list[dict]:
    """Génère les résumés de tous les chapitres d'un cours.

    Args:
        chunks: Liste de chunks avec 'text', 'chapter', 'page'.

    Returns:
        Liste de résumés par chapitre.
    """
    # Étape 1 : Regrouper les chunks par chapitre (en préservant l'ordre)
    chapter_order: list[str] = []
    chapter_data: dict[str, dict] = {}
    for chunk in chunks:
        ch = chunk.get("chapter", "Sans titre")
        if ch not in chapter_data:
            chapter_order.append(ch)
            chapter_data[ch] = {"title": ch, "text": "", "pages": set()}
        chapter_data[ch]["text"] += "\n" + chunk["text"]
        chapter_data[ch]["pages"].add(chunk["page"])

    raw_chapters = [chapter_data[ch] for ch in chapter_order]

    # Étape 2 : Fusionner les petits chapitres en sections logiques
    merged = _merge_chapters_for_summary(raw_chapters)

    # Étape 3 : Générer les résumés
    summaries = []
    total = len(merged)
    for i, data in enumerate(merged, 1):
        logger.info("Résumé chapitre %d/%d : %s", i, total, data["title"])
        summary = summarize_chapter(
            chapter_text=data["text"].strip(),
            chapter_title=data["title"],
            pages=sorted(data["pages"]),
        )
        summaries.append(summary)

    logger.info("Résumés générés : %d chapitres", len(summaries))
    return summaries
