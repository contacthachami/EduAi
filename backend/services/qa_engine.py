"""Moteur de Question-Answering extractif avec CamemBERT-FQuAD.

Utilise AutoModelForQuestionAnswering pour extraire la réponse depuis
les chunks récupérés par FAISS.
"""

import logging
import torch

from backend.config import get_settings

logger = logging.getLogger(__name__)

_qa_pipeline = None


def _get_pipeline():
    """Charge le modèle QA et son tokenizer (singleton)."""
    from transformers import AutoModelForQuestionAnswering, AutoTokenizer
    global _qa_pipeline
    if _qa_pipeline is None:
        settings = get_settings()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Chargement de CamemBERT-QA sur %s…", device.upper())
        tokenizer = AutoTokenizer.from_pretrained(settings.qa_model)
        model = AutoModelForQuestionAnswering.from_pretrained(settings.qa_model).to(device)
        model.eval()
        _qa_pipeline = (model, tokenizer, device)
        logger.info("CamemBERT-QA chargé avec succès.")
    return _qa_pipeline


def answer_question(question: str, context_chunks: list[dict]) -> dict:
    """Répond à une question à partir des chunks de contexte.

    Args:
        question: La question posée par l'étudiant.
        context_chunks: Liste de dicts avec 'text', 'page', 'chapter', 'score'.

    Returns:
        Dict avec 'answer', 'confidence', 'sources'.
    """
    settings = get_settings()

    # Concaténer les chunks en contexte (limité à ~512 tokens ≈ 2000 chars)
    combined_context = ""
    used_chunks = []
    max_context_chars = 2000

    for chunk in context_chunks:
        text = chunk["text"]
        if len(combined_context) + len(text) > max_context_chars:
            # Tronquer pour respecter la limite BERT
            remaining = max_context_chars - len(combined_context)
            if remaining > 100:
                text = text[:remaining]
                combined_context += " " + text
                used_chunks.append(chunk)
            break
        combined_context += " " + text
        used_chunks.append(chunk)

    combined_context = combined_context.strip()

    if not combined_context:
        return {
            "answer": "Je n'ai pas trouvé de contexte pertinent dans ce cours.",
            "confidence": 0.0,
            "sources": [],
        }

    # Inférence CamemBERT
    try:
        model, tokenizer, device = _get_pipeline()
        inputs = tokenizer(
            question, combined_context,
            return_tensors="pt", truncation=True, max_length=512,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)

        start_logits = outputs.start_logits[0]
        end_logits = outputs.end_logits[0]

        start_probs = torch.softmax(start_logits, dim=-1)
        end_probs = torch.softmax(end_logits, dim=-1)

        start_idx = torch.argmax(start_probs).item()
        end_idx = torch.argmax(end_probs).item() + 1
        if end_idx <= start_idx:
            end_idx = start_idx + 1

        answer_tokens = inputs["input_ids"][0][start_idx:end_idx]
        answer = tokenizer.decode(answer_tokens, skip_special_tokens=True).strip()
        score = (start_probs[start_idx] * end_probs[end_idx - 1]).item()

        result = {"answer": answer, "score": score}
    except Exception as e:
        logger.error("Erreur CamemBERT : %s", e)
        return {
            "answer": "Une erreur est survenue lors de l'analyse. Veuillez reformuler votre question.",
            "confidence": 0.0,
            "sources": [],
        }

    answer = result.get("answer", "").strip()
    score = result.get("score", 0.0)

    # Seuil de confiance
    if score < settings.min_confidence_score:
        return {
            "answer": "Je n'ai pas trouvé cette information dans le cours. Essayez de reformuler votre question.",
            "confidence": score,
            "sources": [
                {
                    "chunk_text": c["text"][:200] + "…",
                    "page": c["page"],
                    "chapter": c.get("chapter"),
                    "similarity_score": c.get("score", 0.0),
                }
                for c in used_chunks
            ],
        }

    sources = [
        {
            "chunk_text": c["text"][:200] + "…",
            "page": c["page"],
            "chapter": c.get("chapter"),
            "similarity_score": c.get("score", 0.0),
        }
        for c in used_chunks
    ]

    return {
        "answer": answer,
        "confidence": score,
        "sources": sources,
    }
