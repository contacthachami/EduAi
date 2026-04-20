/**
 * Client HTTP typé pour l'API EduAI.
 */
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 600_000, // 10 min pour la première génération de résumés (32 chapitres sur CPU)
});

// ── Types ──────────────────────────────────────────

export interface CourseInfo {
  id: string;
  name: string;
  created_at: string;
  chunks_count: number;
  pages: number;
}

export interface CourseDetail extends CourseInfo {
  chapters: string[];
  status: "processing" | "ready" | "error";
}

export interface CourseUploadResponse {
  course_id: string;
  course_name: string;
  chunks_count: number;
  pages_count: number;
  status: string;
}

export interface SourceDocument {
  chunk_text: string;
  page: number;
  chapter: string | null;
  similarity_score: number;
}

export interface AnswerResponse {
  answer: string;
  confidence: number;
  sources: SourceDocument[];
  session_id: string;
}

export interface ChapterSummary {
  title: string;
  summary: string;
  pages: number[];
  key_concepts: string[];
}

export interface SummaryResponse {
  course_id: string;
  status: "ready" | "generating";
  chapters: ChapterSummary[];
}

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  source_chunk: string;
}

export interface QuizResponse {
  quiz_id: string;
  questions: QuizQuestion[];
}

export interface QuizResult {
  score: number;
  total: number;
  percentage: number;
  passed: boolean;
  details: Record<string, unknown>[];
}

// ── Endpoints ──────────────────────────────────────

export async function uploadCourse(
  file: File,
  courseName: string,
): Promise<CourseUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("course_name", courseName);
  const { data } = await api.post<CourseUploadResponse>(
    "/courses/upload",
    form,
  );
  return data;
}

export async function fetchCourses(): Promise<CourseInfo[]> {
  const { data } = await api.get<CourseInfo[]>("/courses");
  return data;
}

export async function fetchCourse(id: string): Promise<CourseDetail> {
  const { data } = await api.get<CourseDetail>(`/courses/${id}`);
  return data;
}

export async function deleteCourse(id: string): Promise<void> {
  await api.delete(`/courses/${id}`);
}

export async function askQuestion(
  courseId: string,
  question: string,
  sessionId?: string,
): Promise<AnswerResponse> {
  const { data } = await api.post<AnswerResponse>("/qa/ask", {
    course_id: courseId,
    question,
    session_id: sessionId,
  });
  return data;
}

export async function fetchSummary(courseId: string): Promise<SummaryResponse> {
  const { data } = await api.get<SummaryResponse>(`/summary/${courseId}`);
  return data;
}

export async function fetchQuiz(
  courseId: string,
  numQuestions: number = 10,
): Promise<QuizResponse> {
  const { data } = await api.get<QuizResponse>(`/quiz/${courseId}`, {
    params: { num_questions: numQuestions },
  });
  return data;
}

export async function submitQuiz(
  quizId: string,
  answers: number[],
): Promise<QuizResult> {
  const { data } = await api.post<QuizResult>("/quiz/submit", {
    quiz_id: quizId,
    answers,
  });
  return data;
}
