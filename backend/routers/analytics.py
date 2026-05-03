"""Router Analytics — Dashboard de progression étudiant."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from backend.database.mongodb import get_db
from backend.services.auth import get_current_user

router = APIRouter()


# ── Schémas ─────────────────────────────────────────

class StudyStreak(BaseModel):
    current: int
    longest: int
    today_done: bool


class CourseProgress(BaseModel):
    course_id: str
    course_name: str
    quiz_scores: List[float]
    avg_score: float
    questions_asked: int
    flashcards_reviewed: int
    mastery_percent: float


class WeeklyActivity(BaseModel):
    day: str
    questions: int
    quizzes: int
    flashcards: int


class DashboardResponse(BaseModel):
    total_courses: int
    total_questions_asked: int
    total_quizzes_taken: int
    total_flashcards_reviewed: int
    avg_quiz_score: float
    streak: StudyStreak
    weekly_activity: List[WeeklyActivity]
    courses_progress: List[CourseProgress]


# ── Endpoints ───────────────────────────────────────

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Récupérer le dashboard complet de progression."""
    db = get_db()
    user_id = current_user["user_id"]

    # Compter les cours
    total_courses = await db.courses.count_documents({"user_id": user_id})

    # Stats Q&A
    qa_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$project": {"count": {"$size": {"$ifNull": ["$exchanges", []]}}}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}},
    ]
    qa_result = await db.qa_sessions.aggregate(qa_pipeline).to_list(1)
    total_questions = qa_result[0]["total"] if qa_result else 0

    # Stats quiz
    quiz_results = await db.quiz_results.find({"user_id": user_id}).to_list(length=None)
    total_quizzes = len(quiz_results)
    avg_quiz_score = 0.0
    if quiz_results:
        avg_quiz_score = round(
            sum(r.get("percentage", 0) for r in quiz_results) / total_quizzes, 1
        )

    # Stats flashcards
    flashcard_reviews = await db.flashcard_reviews.count_documents({"user_id": user_id})

    # Streak
    streak = await _compute_streak(db, user_id)

    # Activité hebdomadaire
    weekly = await _compute_weekly_activity(db, user_id)

    # Progression par cours
    courses_progress = await _compute_courses_progress(db, user_id)

    return DashboardResponse(
        total_courses=total_courses,
        total_questions_asked=total_questions,
        total_quizzes_taken=total_quizzes,
        total_flashcards_reviewed=flashcard_reviews,
        avg_quiz_score=avg_quiz_score,
        streak=streak,
        weekly_activity=weekly,
        courses_progress=courses_progress,
    )


@router.post("/log-activity")
async def log_activity(current_user: dict = Depends(get_current_user)):
    """Enregistrer une activité d'étude (appelé automatiquement par le frontend)."""
    db = get_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await db.study_activity.update_one(
        {"user_id": current_user["user_id"], "date": today},
        {"$set": {"user_id": current_user["user_id"], "date": today, "active": True}},
        upsert=True,
    )
    return {"ok": True}


# ── Helpers privés ──────────────────────────────────

async def _compute_streak(db, user_id: str) -> StudyStreak:
    """Calculer le streak d'étude (jours consécutifs)."""
    activities = await db.study_activity.find(
        {"user_id": user_id, "active": True}
    ).sort("date", -1).to_list(length=365)

    if not activities:
        return StudyStreak(current=0, longest=0, today_done=False)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dates = {a["date"] for a in activities}
    today_done = today in dates

    # Current streak
    current = 0
    check_date = datetime.now(timezone.utc).date()
    if not today_done:
        check_date -= timedelta(days=1)

    while check_date.strftime("%Y-%m-%d") in dates:
        current += 1
        check_date -= timedelta(days=1)

    # Longest streak
    sorted_dates = sorted(dates)
    longest = 0
    temp = 1
    for i in range(1, len(sorted_dates)):
        d1 = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d").date()
        d2 = datetime.strptime(sorted_dates[i], "%Y-%m-%d").date()
        if (d2 - d1).days == 1:
            temp += 1
        else:
            longest = max(longest, temp)
            temp = 1
    longest = max(longest, temp)

    return StudyStreak(current=current, longest=longest, today_done=today_done)


async def _compute_weekly_activity(db, user_id: str) -> List[WeeklyActivity]:
    """Activité des 7 derniers jours."""
    days_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    result = []
    now = datetime.now(timezone.utc)

    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_name = days_fr[day.weekday()]

        # Questions du jour
        q_count = await db.qa_sessions.count_documents({
            "user_id": user_id,
            "last_activity": {"$gte": day_str, "$lt": (day + timedelta(days=1)).strftime("%Y-%m-%d")},
        })

        # Quiz du jour
        quiz_count = await db.quiz_results.count_documents({
            "user_id": user_id,
            "submitted_at": {
                "$gte": datetime.combine(day.date(), datetime.min.time()),
                "$lt": datetime.combine((day + timedelta(days=1)).date(), datetime.min.time()),
            },
        })

        # Flashcards du jour
        fc_count = await db.flashcard_reviews.count_documents({
            "user_id": user_id,
            "reviewed_at": {
                "$gte": datetime.combine(day.date(), datetime.min.time()),
                "$lt": datetime.combine((day + timedelta(days=1)).date(), datetime.min.time()),
            },
        })

        result.append(WeeklyActivity(
            day=day_name, questions=q_count, quizzes=quiz_count, flashcards=fc_count
        ))

    return result


async def _compute_courses_progress(db, user_id: str) -> List[CourseProgress]:
    """Progression détaillée par cours."""
    courses = await db.courses.find(
        {"user_id": user_id}, {"_id": 1, "name": 1}
    ).to_list(length=None)

    progress_list = []
    for course in courses:
        cid = str(course["_id"])

        # Quiz scores pour ce cours
        quizzes = await db.quiz_results.find(
            {"user_id": user_id, "course_id": cid}
        ).to_list(length=None)
        scores = [q.get("percentage", 0) for q in quizzes]
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0

        # Questions posées
        qa_sessions = await db.qa_sessions.find(
            {"user_id": user_id, "course_id": cid}
        ).to_list(length=None)
        q_count = sum(len(s.get("exchanges", [])) for s in qa_sessions)

        # Flashcards révisées
        fc_count = await db.flashcard_reviews.count_documents(
            {"user_id": user_id, "course_id": cid}
        )

        # Mastery : basé sur quiz avg + activité
        mastery = min(100, avg * 0.7 + min(q_count * 2, 20) + min(fc_count * 0.5, 10))

        progress_list.append(CourseProgress(
            course_id=cid,
            course_name=course["name"],
            quiz_scores=scores[-10:],  # 10 derniers
            avg_score=avg,
            questions_asked=q_count,
            flashcards_reviewed=fc_count,
            mastery_percent=round(mastery, 1),
        ))

    return progress_list
