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
)
from backend.services.quiz_generator import generate_quiz

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{course_id}", response_model=QuizResponse)
async def get_course_quiz(
    course_id: str,
    num_questions: int = Query(default=10, ge=1, le=30),
):
    """Génère un quiz pour un cours donné."""
    # Vérifier que le cours existe
    course = await get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    # Récupérer les chunks
    chunks = await get_chunks_by_course(course_id)
    if not chunks:
        raise HTTPException(status_code=503, detail="Cours pas encore indexé.")

    # Générer le quiz dans un thread pour ne pas bloquer l'event loop
    questions = await asyncio.to_thread(generate_quiz, chunks, num_questions)
    if not questions:
        raise HTTPException(status_code=500, detail="Impossible de générer le quiz pour ce cours.")

    quiz_id = str(uuid.uuid4())

    # Sauvegarder le quiz en base
    await save_quiz({
        "quiz_id": quiz_id,
        "course_id": course_id,
        "questions": questions,
    })

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
