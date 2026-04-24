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
  llm_used?: boolean;
}

export interface ChapterSummary {
  title: string;
  summary: string;
  pages: number[];
  key_concepts: string[];
  /** Fiche pédagogique Markdown générée par le LLM (présente si llm_used=true). */
  pedagogic?: string | null;
  /** True si la fiche a été produite par le LLM (sinon fallback extractif). */
  llm_used?: boolean;
  /** Techniques NLP/DL/LLM appliquées à ce chapitre (pour badges UI). */
  techniques?: string[];
}

export interface PipelineStep {
  name: string;
  family: "NLP" | "Deep Learning" | "LLM";
  model: string;
  detail: string;
}

export interface PipelineMeta {
  steps: PipelineStep[];
  llm_backend: string;
  llm_model?: string | null;
}

export interface SummaryResponse {
  course_id: string;
  status: "ready" | "generating";
  chapters: ChapterSummary[];
  pipeline_meta?: PipelineMeta | null;
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

// ── Streaming SSE Q&A ──────────────────────────────

export interface StreamEvents {
  onSources?: (data: {
    sources: SourceDocument[];
    session_id: string;
    confidence?: number;
  }) => void;
  onToken?: (text: string) => void;
  onDone?: (data: { llm_used: boolean }) => void;
  onError?: (err: Error) => void;
}

/**
 * Stream une réponse Q&A via SSE. Retourne une fonction d'abort.
 */
export function askQuestionStream(
  courseId: string,
  question: string,
  sessionId: string | undefined,
  events: StreamEvents,
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const resp = await fetch("/api/qa/ask/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_id: courseId,
          question,
          session_id: sessionId,
        }),
        signal: controller.signal,
      });
      if (!resp.ok || !resp.body) {
        throw new Error(`HTTP ${resp.status}`);
      }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        // Découpe par double-newline = fin d'event SSE
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          if (!part.trim()) continue;
          let event = "message";
          let data = "";
          for (const line of part.split("\n")) {
            if (line.startsWith("event:")) event = line.slice(6).trim();
            else if (line.startsWith("data:")) data += line.slice(5).trim();
          }
          if (!data) continue;
          try {
            const parsed = JSON.parse(data);
            if (event === "sources") events.onSources?.(parsed);
            else if (event === "token") events.onToken?.(parsed.text ?? "");
            else if (event === "done") events.onDone?.(parsed);
          } catch {
            // ignore malformed
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      events.onError?.(err as Error);
    }
  })();

  return () => controller.abort();
}

// ── Status de génération des contenus ──────────────

export interface CourseContentStatus {
  course_id: string;
  indexed: boolean;
  summary_ready: boolean;
  quiz_ready: boolean;
}

export async function fetchCourseStatus(
  courseId: string,
): Promise<CourseContentStatus> {
  const { data } = await api.get<CourseContentStatus>(
    `/courses/${courseId}/status`,
  );
  return data;
}
