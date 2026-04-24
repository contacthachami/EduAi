"""Router pour la génération et soumission de quiz."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import (
    QuizResponse, QuizQuestion, QuizSubmission, QuizResult,
)
from backend.database.mongodb import (
    get_course_by_id, get_chunks_by_course, save_quiz, get_quiz,
    get_cached_course_quiz, save_cached_course_quiz,
)
from backend.services.quiz_generator import generate_quiz
from backend.services.llm_quiz import generate_quiz_llm

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_NUM_QUESTIONS = 10

# Track quiz pre-generations in-flight (course_id)
_generating_quiz: set[str] = set()
_quiz_lock = asyncio.Lock()


async def _generate_default_quiz(course_id: str, chunks: list, num_questions: int = DEFAULT_NUM_QUESTIONS) -> list[dict] | None:
    """Génère un quiz LLM (avec fallback extractif) et le met en cache."""
    questions = None
    try:
        questions = await generate_quiz_llm(chunks, num_questions=num_questions)
    except Exception:
        logger.exception("LLM quiz a planté pour %s", course_id)
        questions = None

    if not questions:
        logger.info("Fallback quiz extractif pour %s", course_id)
        questions = await asyncio.to_thread(generate_quiz, chunks, num_questions)

    if not questions:
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
):
    """Renvoie un quiz pour le cours.

    - Si `num_questions == DEFAULT_NUM_QUESTIONS` et `regenerate=False` → sert le cache si dispo.
    - Sinon → génère à la volée (LLM puis fallback extractif).
    """
    course = await get_course_by_id(course_id)
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

    chunks = await get_chunks_by_course(course_id)
    if not chunks:
        raise HTTPException(status_code=503, detail="Cours pas encore indexé.")

    # Génération à la volée (peut prendre plusieurs minutes en LLM)
    questions = None
    try:
        questions = await generate_quiz_llm(chunks, num_questions=num_questions)
    except Exception:
        logger.exception("LLM quiz a planté pour %s", course_id)
        questions = None

    if not questions:
        logger.info("Fallback quiz extractif pour %s", course_id)
        questions = await asyncio.to_thread(generate_quiz, chunks, num_questions)

    if not questions:
        raise HTTPException(status_code=500, detail="Impossible de générer le quiz pour ce cours.")

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
async def submit_quiz(submission: QuizSubmission):
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
