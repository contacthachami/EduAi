"""Router Examen — Mode examen simulé avec timer et scoring."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.database.mongodb import get_db
from backend.services.auth import get_current_user

router = APIRouter()


# ── Schémas ─────────────────────────────────────────

class ExamConfig(BaseModel):
    course_id: str
    num_questions: int = Field(default=15, ge=5, le=40)
    time_limit_minutes: int = Field(default=20, ge=5, le=120)


class ExamQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    difficulty: str = "moyen"


class ExamResponse(BaseModel):
    exam_id: str
    course_name: str
    questions: List[ExamQuestion]
    time_limit_minutes: int
    total_questions: int


class ExamSubmission(BaseModel):
    exam_id: str
    answers: List[int]  # index de la réponse choisie pour chaque question
    time_spent_seconds: int = 0


class ExamQuestionResult(BaseModel):
    question: str
    your_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str


class ExamResult(BaseModel):
    exam_id: str
    score: int
    total: int
    percentage: float
    grade: str  # A, B, C, D, F
    passed: bool
    time_spent_seconds: int
    details: List[ExamQuestionResult]


class ExamHistoryEntry(BaseModel):
    exam_id: str
    course_name: str
    score: int
    total: int
    percentage: float
    grade: str
    passed: bool
    submitted_at: datetime


# ── Endpoints ───────────────────────────────────────

@router.post("/start", response_model=ExamResponse)
async def start_exam(config: ExamConfig, current_user: dict = Depends(get_current_user)):
    """Démarrer un examen simulé (mix de questions de tous les chapitres)."""
    from bson import ObjectId
    db = get_db()
    user_id = current_user["user_id"]

    course = await db.courses.find_one({"_id": ObjectId(config.course_id), "user_id": user_id})
    if not course:
        raise HTTPException(status_code=404, detail="Cours introuvable.")

    # Récupérer les chunks
    chunks = await db.chunks.find({"course_id": config.course_id}).to_list(length=None)
    if not chunks:
        raise HTTPException(status_code=400, detail="Aucun contenu indexé.")

    # Générer les questions d'examen via LLM
    from backend.services.llm_exam import generate_exam_questions
    questions_data = await generate_exam_questions(chunks, config.num_questions)

    # Sauvegarder l'examen
    now = datetime.now(timezone.utc)
    exam_doc = {
        "user_id": user_id,
        "course_id": config.course_id,
        "questions": questions_data,
        "time_limit_minutes": config.time_limit_minutes,
        "started_at": now,
        "status": "in_progress",
    }
    result = await db.exams.insert_one(exam_doc)
    exam_id = str(result.inserted_id)

    # Retourner sans les réponses correctes
    exam_questions = [
        ExamQuestion(
            id=i + 1,
            question=q["question"],
            options=q["options"],
            difficulty=q.get("difficulty", "moyen"),
        )
        for i, q in enumerate(questions_data)
    ]

    return ExamResponse(
        exam_id=exam_id,
        course_name=course["name"],
        questions=exam_questions,
        time_limit_minutes=config.time_limit_minutes,
        total_questions=len(exam_questions),
    )


@router.post("/submit", response_model=ExamResult)
async def submit_exam(submission: ExamSubmission, current_user: dict = Depends(get_current_user)):
    """Soumettre les réponses d'un examen et obtenir le résultat."""
    from bson import ObjectId
    db = get_db()
    user_id = current_user["user_id"]

    exam = await db.exams.find_one({
        "_id": ObjectId(submission.exam_id),
        "user_id": user_id,
    })
    if not exam:
        raise HTTPException(status_code=404, detail="Examen introuvable.")
    if exam.get("status") == "submitted":
        raise HTTPException(status_code=400, detail="Examen déjà soumis.")

    questions = exam["questions"]
    if len(submission.answers) != len(questions):
        raise HTTPException(
            status_code=400,
            detail=f"Nombre de réponses incorrect ({len(submission.answers)} vs {len(questions)}).",
        )

    # Corriger
    details = []
    score = 0
    for i, (q, answer_idx) in enumerate(zip(questions, submission.answers)):
        is_correct = answer_idx == q["correct_index"]
        if is_correct:
            score += 1
        details.append(ExamQuestionResult(
            question=q["question"],
            your_answer=q["options"][answer_idx] if 0 <= answer_idx < len(q["options"]) else "Non répondu",
            correct_answer=q["options"][q["correct_index"]],
            is_correct=is_correct,
            explanation=q.get("explanation", ""),
        ))

    total = len(questions)
    percentage = round((score / total) * 100, 1)
    grade = _compute_grade(percentage)
    passed = percentage >= 60

    # Sauvegarder le résultat
    now = datetime.now(timezone.utc)
    await db.exams.update_one(
        {"_id": ObjectId(submission.exam_id)},
        {"$set": {
            "status": "submitted",
            "score": score,
            "total": total,
            "percentage": percentage,
            "grade": grade,
            "passed": passed,
            "time_spent_seconds": submission.time_spent_seconds,
            "submitted_at": now,
        }},
    )

    # Sauvegarder aussi dans quiz_results pour les analytics
    course = await db.courses.find_one({"_id": ObjectId(exam["course_id"])})
    await db.quiz_results.insert_one({
        "user_id": user_id,
        "course_id": exam["course_id"],
        "type": "exam",
        "score": score,
        "total": total,
        "percentage": percentage,
        "submitted_at": now,
    })

    # Log activité
    today = now.strftime("%Y-%m-%d")
    await db.study_activity.update_one(
        {"user_id": user_id, "date": today},
        {"$set": {"user_id": user_id, "date": today, "active": True}},
        upsert=True,
    )

    return ExamResult(
        exam_id=submission.exam_id,
        score=score,
        total=total,
        percentage=percentage,
        grade=grade,
        passed=passed,
        time_spent_seconds=submission.time_spent_seconds,
        details=details,
    )


@router.get("/history", response_model=List[ExamHistoryEntry])
async def get_exam_history(current_user: dict = Depends(get_current_user)):
    """Historique des examens passés."""
    from bson import ObjectId
    db = get_db()
    user_id = current_user["user_id"]

    exams = await db.exams.find({
        "user_id": user_id,
        "status": "submitted",
    }).sort("submitted_at", -1).to_list(length=50)

    results = []
    for exam in exams:
        course = await db.courses.find_one({"_id": ObjectId(exam["course_id"])})
        results.append(ExamHistoryEntry(
            exam_id=str(exam["_id"]),
            course_name=course["name"] if course else "Cours supprimé",
            score=exam.get("score", 0),
            total=exam.get("total", 0),
            percentage=exam.get("percentage", 0),
            grade=exam.get("grade", "F"),
            passed=exam.get("passed", False),
            submitted_at=exam.get("submitted_at", exam["started_at"]),
        ))

    return results


# ── Helpers ─────────────────────────────────────────

def _compute_grade(percentage: float) -> str:
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    return "F"
