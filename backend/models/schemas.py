"""Schémas Pydantic pour toute l'API EduAI."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ── Cours ──────────────────────────────────────────

class CourseUploadResponse(BaseModel):
    course_id: str
    course_name: str
    chunks_count: int
    pages_count: int
    status: str


class CourseInfo(BaseModel):
    id: str
    name: str
    created_at: datetime
    chunks_count: int
    pages: int


class CourseDetail(BaseModel):
    id: str
    name: str
    created_at: datetime
    chunks_count: int
    pages: int
    chapters: List[str]


# ── Questions / Réponses ───────────────────────────

class QuestionRequest(BaseModel):
    course_id: str
    question: str = Field(..., min_length=1)
    session_id: Optional[str] = None


class SourceDocument(BaseModel):
    chunk_text: str
    page: int
    chapter: Optional[str] = None
    similarity_score: float


class AnswerResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceDocument]
    session_id: str


class HistoryEntry(BaseModel):
    question: str
    answer: str
    timestamp: datetime
    sources: List[SourceDocument]


# ── Résumés ────────────────────────────────────────

class ChapterSummary(BaseModel):
    title: str
    summary: str
    pages: List[int]
    key_concepts: List[str]


class SummaryResponse(BaseModel):
    course_id: str
    chapters: List[ChapterSummary]


# ── Quiz ───────────────────────────────────────────

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    correct_index: int
    explanation: str
    source_chunk: str


class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[QuizQuestion]


class QuizSubmission(BaseModel):
    quiz_id: str
    answers: List[int]


class QuizResult(BaseModel):
    score: int
    total: int
    percentage: float
    passed: bool
    details: List[dict]


# ── Erreurs ────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
