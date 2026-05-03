"""Service de génération de mind maps via LLM."""

import json
import logging
from typing import List, Tuple

from backend.services.llm_client import get_client, LLMUnavailable

logger = logging.getLogger(__name__)

MINDMAP_PROMPT = """Tu es un expert en cartographie conceptuelle. À partir du contenu de cours suivant, génère une mind map structurée.

La mind map doit contenir :
- Des nœuds (nodes) : chaque concept important avec un id unique, un label court, et un type ("chapter", "concept", ou "detail")
- Des liens (edges) : les relations entre concepts avec un label optionnel décrivant la relation

Règles :
- Maximum 25 nœuds pour rester lisible
- Les chapitres sont les nœuds principaux (type: "chapter")
- Les concepts importants sont reliés à leur chapitre (type: "concept")
- Les détails précisent les concepts (type: "detail")
- Les labels des liens doivent être courts (1-3 mots) : "contient", "utilise", "définit", "exemple de", etc.

Chapitres détectés : {chapters}

Contenu du cours :
---
{content}
---

Réponds UNIQUEMENT en JSON valide avec cette structure :
{{"nodes": [{{"id": "n1", "label": "...", "type": "chapter|concept|detail", "chapter": "..."}}], "edges": [{{"source": "n1", "target": "n2", "label": "..."}}]}}"""


async def generate_mindmap(chunks: list[dict], chapters: list[str]) -> Tuple[List, List]:
    """Génère une mind map depuis les chunks d'un cours."""
    from backend.routers.mindmap import MindMapNode, MindMapEdge

    # Sélectionner le contenu (premiers chunks de chaque chapitre)
    content = _extract_content(chunks, max_chars=4000)
    chapters_str = ", ".join(chapters) if chapters else "Non spécifiés"

    prompt = MINDMAP_PROMPT.format(content=content, chapters=chapters_str)

    client = get_client()
    available = await client.is_available()
    if not available:
        # Fallback : mind map basique depuis les chapitres
        return _fallback_mindmap(chapters, chunks)

    raw = await client.generate_json(prompt)

    try:
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw
    except (json.JSONDecodeError, TypeError):
        logger.error("Échec parsing JSON mindmap: %s", str(raw)[:200])
        return _fallback_mindmap(chapters, chunks)

    # Parser les nœuds et edges
    nodes = []
    for n in data.get("nodes", []):
        if isinstance(n, dict) and "id" in n and "label" in n:
            nodes.append(MindMapNode(
                id=n["id"],
                label=n["label"][:50],
                type=n.get("type", "concept"),
                chapter=n.get("chapter"),
            ))

    edges = []
    node_ids = {n.id for n in nodes}
    for e in data.get("edges", []):
        if isinstance(e, dict) and e.get("source") in node_ids and e.get("target") in node_ids:
            edges.append(MindMapEdge(
                source=e["source"],
                target=e["target"],
                label=e.get("label"),
            ))

    if not nodes:
        return _fallback_mindmap(chapters, chunks)

    return nodes, edges


def _extract_content(chunks: list[dict], max_chars: int = 4000) -> str:
    """Extrait un résumé du contenu pour le prompt."""
    by_chapter = {}
    for c in chunks:
        ch = c.get("chapter", "Général")
        by_chapter.setdefault(ch, []).append(c.get("text", ""))

    parts = []
    total = 0
    for ch, texts in by_chapter.items():
        combined = " ".join(texts[:3])[:max_chars // max(1, len(by_chapter))]
        parts.append(f"[{ch}] {combined}")
        total += len(parts[-1])
        if total >= max_chars:
            break

    return "\n\n".join(parts)


def _fallback_mindmap(chapters: list[str], chunks: list[dict]):
    """Mind map basique sans LLM."""
    from backend.routers.mindmap import MindMapNode, MindMapEdge

    nodes = []
    edges = []

    # Nœud racine
    nodes.append(MindMapNode(id="root", label="Cours", type="chapter"))

    for i, ch in enumerate(chapters[:8]):
        node_id = f"ch{i}"
        nodes.append(MindMapNode(id=node_id, label=ch[:40], type="chapter", chapter=ch))
        edges.append(MindMapEdge(source="root", target=node_id, label="contient"))

        # Ajouter quelques concepts par chapitre
        chapter_chunks = [c for c in chunks if c.get("chapter") == ch]
        for j, chunk in enumerate(chapter_chunks[:2]):
            text = chunk.get("text", "")
            words = text.split()[:5]
            if words:
                concept_id = f"c{i}_{j}"
                nodes.append(MindMapNode(
                    id=concept_id, label=" ".join(words), type="concept", chapter=ch
                ))
                edges.append(MindMapEdge(source=node_id, target=concept_id))

    return nodes, edges
