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
    status: str = "ready"


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
    llm_used: bool = False  # True si la réponse a été générée par le LLM (sinon CamemBERT extractif)


class HistoryEntry(BaseModel):
    question: str
    answer: str
    timestamp: datetime
    sources: List[SourceDocument]


# ── Résumés ────────────────────────────────────────

class PipelineStep(BaseModel):
    """Détail d'une étape du pipeline NLP/DL EduAI (transparence pour l'utilisateur)."""
    name: str           # ex : "Embeddings sémantiques"
    family: str         # "NLP" | "Deep Learning" | "LLM"
    model: str          # ex : "paraphrase-multilingual-MiniLM-L12-v2"
    detail: str         # description courte de ce que fait l'étape


class PipelineMeta(BaseModel):
    """Métadonnées du pipeline appliqué à ce résumé — prouve l'usage NLP+DL en plus du LLM."""
    steps: List[PipelineStep] = []
    llm_backend: str = "groq"          # "groq" | "ollama" | "none"
    llm_model: Optional[str] = None    # ex : "llama-3.3-70b-versatile"


class ChapterSummary(BaseModel):
    title: str
    summary: str
    pages: List[int]
    key_concepts: List[str]
    pedagogic: Optional[str] = None  # fiche Markdown structurée (générée par LLM, optionnelle)
    llm_used: bool = False           # True si la fiche pédagogique a été produite par le LLM
    techniques: List[str] = []       # ex : ["spaCy NER", "BERT embeddings", "TextRank", "Llama 3.3 70B"]


class SummaryResponse(BaseModel):
    course_id: str
    status: str = "ready"  # "ready" | "generating"
    chapters: List[ChapterSummary] = []
    llm_enabled: bool = False        # True si au moins un chapitre a une fiche LLM
    pipeline_meta: Optional[PipelineMeta] = None


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
