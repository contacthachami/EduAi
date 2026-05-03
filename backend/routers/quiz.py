"""Router pour la génération et soumission de quiz."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException, Query, Depends

from backend.models.schemas import (
    QuizResponse, QuizQuestion, QuizSubmission, QuizResult,
)
from backend.database.mongodb import (
    get_course_by_id, get_chunks_by_course, save_quiz, get_quiz,
    get_cached_course_quiz, save_cached_course_quiz, delete_cached_course_quiz,
)
from backend.services.llm_quiz import generate_quiz_llm
from backend.services.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_NUM_QUESTIONS = 10

# Track quiz pre-generations in-flight (course_id)
_generating_quiz: set[str] = set()
_quiz_lock = asyncio.Lock()


async def _generate_default_quiz(course_id: str, chunks: list, num_questions: int = DEFAULT_NUM_QUESTIONS) -> list[dict] | None:
    """Génère un quiz LLM uniquement (pas de fallback extractif T5/spaCy)
    et le met en cache. Retourne None si le LLM échoue : l'utilisateur
    pourra réessayer plutôt que de recevoir un quiz de mauvaise qualité.
    """
    questions = None
    try:
        questions = await generate_quiz_llm(chunks, num_questions=num_questions)
    except Exception:
        logger.exception("LLM quiz a planté pour %s", course_id)
        questions = None

    if not questions:
        logger.warning("Quiz LLM indisponible pour %s — pas de fallback extractif (qualité insuffisante)", course_id)
        return None

    quiz_id = str(uuid.uuid4())
    await save_quiz({"quiz_id": quiz_id, "course_id": course_id, "questions": questions})
    await save_cached_course_quiz(course_id, quiz_id, questions)
    logger.info("Quiz par défaut mis en cache pour %s (%d questions)", course_id, len(questions))
    return questions


async def pregenerate_quiz_in_background(course_id: str) -> None:
    """À appeler depuis le pipeline d'upload : pré-génère le quiz par défaut."""
    async with _quiz_lock:
        if course_id in _generating_quiz:
            return
        _generating_quiz.add(course_id)
    try:
        # Vérifier si déjà en cache
        cached = await get_cached_course_quiz(course_id)
        if cached:
            return
        chunks = await get_chunks_by_course(course_id)
        if not chunks:
            logger.warning("Pas de chunks pour pré-générer le quiz de %s", course_id)
            return
        await _generate_default_quiz(course_id, chunks)
    except Exception:
        logger.exception("Erreur pré-génération quiz pour %s", course_id)
    finally:
        async with _quiz_lock:
            _generating_quiz.discard(course_id)


@router.get("/{course_id}", response_model=QuizResponse)
async def get_course_quiz(
    course_id: str,
    num_questions: int = Query(default=DEFAULT_NUM_QUESTIONS, ge=1, le=30),
    regenerate: bool = Query(default=False, description="Forcer la régénération (ignore le cache)"),
    current_user: dict = Depends(get_current_user),
):
    """Renvoie un quiz pour le cours."""
    course = await get_course_by_id(course_id, user_id=current_user["user_id"])
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    use_cache = (num_questions == DEFAULT_NUM_QUESTIONS) and not regenerate

    if use_cache:
        cached = await get_cached_course_quiz(course_id)
        if cached:
            logger.info("Quiz servi depuis le cache pour %s", course_id)
            return QuizResponse(
                quiz_id=cached["quiz_id"],
                questions=[QuizQuestion(**q) for q in cached["questions"]],
            )

    # Si on régénère explicitement, on invalide d'abord le cache existant
    if regenerate:
        try:
            await delete_cached_course_quiz(course_id)
            logger.info("Cache quiz invalidé pour %s (régénération forcée)", course_id)
        except Exception:
            logger.exception("Impossible d'invalider le cache quiz pour %s", course_id)

    chunks = await get_chunks_by_course(course_id)
    if not chunks:
        raise HTTPException(status_code=503, detail="Cours pas encore indexé.")

    # Génération LLM uniquement (pas de fallback extractif T5/spaCy : qualité insuffisante)
    questions = None
    try:
        questions = await generate_quiz_llm(chunks, num_questions=num_questions)
    except Exception:
        logger.exception("LLM quiz a planté pour %s", course_id)
        questions = None

    if not questions:
        raise HTTPException(
            status_code=503,
            detail="Le générateur de quiz LLM est indisponible. Réessaie dans un instant.",
        )

    quiz_id = str(uuid.uuid4())
    await save_quiz({"quiz_id": quiz_id, "course_id": course_id, "questions": questions})

    # Si c'est la "taille standard", on met aussi en cache pour les prochains
    if num_questions == DEFAULT_NUM_QUESTIONS:
        await save_cached_course_quiz(course_id, quiz_id, questions)

    return QuizResponse(
        quiz_id=quiz_id,
        questions=[QuizQuestion(**q) for q in questions],
    )


@router.post("/submit", response_model=QuizResult)
async def submit_quiz(submission: QuizSubmission, current_user: dict = Depends(get_current_user)):
    """Soumet les réponses d'un quiz et calcule le score."""
    quiz_data = await get_quiz(submission.quiz_id)
    if not quiz_data:
        raise HTTPException(status_code=404, detail="Quiz introuvable.")

    questions = quiz_data["questions"]

    if len(submission.answers) != len(questions):
        raise HTTPException(
            status_code=400,
            detail=f"Nombre de réponses incorrect : {len(submission.answers)} reçues, {len(questions)} attendues.",
        )

    score = 0
    details = []

    for i, (question, user_answer) in enumerate(zip(questions, submission.answers)):
        is_correct = user_answer == question["correct_index"]
        if is_correct:
            score += 1

        details.append({
            "question_id": question["id"],
            "question": question["question"],
            "user_answer": user_answer,
            "correct_index": question["correct_index"],
            "correct": is_correct,
            "explanation": question["explanation"],
        })

    total = len(questions)
    percentage = round((score / total) * 100, 1) if total > 0 else 0

    return QuizResult(
        score=score,
        total=total,
        percentage=percentage,
        passed=percentage >= 60,
        details=details,
    )
