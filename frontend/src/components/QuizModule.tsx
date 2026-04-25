/**
 * QuizModule — Quiz interactif style apprentissage (feedback immédiat).
 *
 * Mode par défaut : "apprentissage" — l'étudiant voit immédiatement si
 * sa réponse est correcte, avec l'explication.
 *
 * Features :
 *  - Badge difficulté (facile/moyen/difficile) par question
 *  - Feedback immédiat (vert/rouge) + explication révélée
 *  - Skip une question
 *  - Timer (chrono total)
 *  - Régénération forcée du quiz (nouveau jeu de questions)
 *  - Résultats : explications visibles pour TOUTES les réponses (correctes ET fausses)
 */
"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Loader2,
  Check,
  X as XIcon,
  ArrowRight,
  RefreshCw,
  Clock,
  SkipForward,
} from "lucide-react";
import {
  fetchQuiz,
  submitQuiz,
  type QuizQuestion,
  type QuizResult,
} from "@/lib/api";

interface QuizModuleProps {
  courseId: string;
}

type QuizState = "idle" | "loading" | "active" | "submitted";

const DIFFICULTY_STYLES: Record<string, { label: string; cls: string }> = {
  facile: { label: "Facile", cls: "bg-success-light text-success" },
  moyen: { label: "Moyen", cls: "bg-amber-100 text-amber-700" },
  difficile: { label: "Difficile", cls: "bg-error-light text-error" },
};

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function QuizModule({ courseId }: QuizModuleProps) {
  const [state, setState] = useState<QuizState>("idle");
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [quizId, setQuizId] = useState("");
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  /** Choix verrouillé (révélé) pour la question courante. null = pas encore validé. */
  const [revealedChoice, setRevealedChoice] = useState<number | null>(null);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [numQuestions, setNumQuestions] = useState(5);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Timer chrono pendant la phase active
  useEffect(() => {
    if (state === "active") {
      const start = Date.now() - elapsed * 1000;
      timerRef.current = setInterval(() => {
        setElapsed(Math.floor((Date.now() - start) / 1000));
      }, 1000);
      return () => {
        if (timerRef.current) clearInterval(timerRef.current);
      };
    }
    if (timerRef.current) clearInterval(timerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  const startQuiz = async (regenerate = false) => {
    setState("loading");
    setError(null);
    setElapsed(0);
    try {
      const res = await fetchQuiz(courseId, numQuestions, regenerate);
      setQuestions(res.questions);
      setQuizId(res.quiz_id);
      setAnswers(new Array(res.questions.length).fill(null));
      setCurrentQ(0);
      setRevealedChoice(null);
      setResult(null);
      setState("active");
    } catch (err) {
      // Message friendly selon le type d'erreur
      let msg = "Impossible de générer le quiz.";
      if (typeof err === "object" && err !== null) {
        const e = err as {
          response?: { status?: number; data?: { detail?: string } };
          code?: string;
        };
        const status = e.response?.status;
        const detail = e.response?.data?.detail;
        if (status === 503) {
          msg = detail
            ? `Service temporairement indisponible : ${detail} Réessayez dans un instant.`
            : "Le service de génération est momentanément indisponible. Réessayez dans quelques secondes.";
        } else if (status === 404) {
          msg = "Cours introuvable.";
        } else if (e.code === "ECONNABORTED") {
          msg = "La génération a pris trop de temps. Réessayez.";
        } else if (err instanceof Error) {
          msg = err.message;
        }
      }
      setError(msg);
      setState("idle");
    }
  };

  /** Verrouille la réponse choisie et révèle le feedback. */
  const lockAnswer = (optionIndex: number) => {
    if (revealedChoice !== null) return;
    setRevealedChoice(optionIndex);
    setAnswers((prev) => {
      const next = [...prev];
      next[currentQ] = optionIndex;
      return next;
    });
  };

  const goToNext = () => {
    setRevealedChoice(null);
    if (currentQ < questions.length - 1) {
      setCurrentQ((prev) => prev + 1);
    }
  };

  const skipQuestion = () => {
    // Marque comme non répondue (-1) et avance
    setAnswers((prev) => {
      const next = [...prev];
      next[currentQ] = -1;
      return next;
    });
    setRevealedChoice(null);
    if (currentQ < questions.length - 1) {
      setCurrentQ((prev) => prev + 1);
    }
  };

  const handleSubmit = async () => {
    setState("loading");
    try {
      // Pour le backend, on envoie -1 pour les questions skippées (ne match aucun index 0-3)
      const payload = answers.map((a) => (a === null || a === -1 ? -1 : a));
      const res = await submitQuiz(quizId, payload);
      setResult(res);
      setState("submitted");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erreur lors de la soumission.",
      );
      setState("active");
    }
  };

  if (state === "idle") {
    return (
      <div className="mx-auto max-w-2xl py-12 text-center sm:py-16">
        <p className="eyebrow">Entraînement</p>
        <h3 className="mt-2 text-2xl font-semibold text-ink-primary">
          Quiz de révision
        </h3>
        <p className="mx-auto mt-2 max-w-lg text-sm text-ink-secondary">
          Choisissez le nombre de questions, puis lancez un quiz basé sur le
          contenu du document.
        </p>

        <div className="mt-7 inline-flex items-center gap-3 rounded-card border border-border bg-bg-subtle px-3 py-2">
          <label htmlFor="quiz-question-count" className="text-sm text-ink-secondary">
            Nombre de questions :
          </label>
          <select
            id="quiz-question-count"
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            aria-label="Nombre de questions"
            title="Nombre de questions"
            className="rounded-card border border-border bg-bg-card px-3 py-1.5 text-sm text-ink-primary focus:border-accent"
          >
            {[5, 10, 15, 20].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-7 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <button onClick={() => startQuiz(false)} className="btn-primary">
            Commencer le quiz
          </button>
          <button
            onClick={() => startQuiz(true)}
            className="btn-secondary"
            title="Générer une nouvelle série de questions"
          >
            <RefreshCw size={15} strokeWidth={1.8} />
            Nouvelle série
          </button>
        </div>

        {error && (
          <div
            role="alert"
            className="status-message status-message-error mx-auto mt-6 flex max-w-md items-start gap-2 text-left"
          >
            <XIcon
              size={14}
              strokeWidth={2}
              className="mt-0.5 shrink-0"
            />
            <div className="flex-1">
              <p className="text-xs leading-relaxed">{error}</p>
              <button
                onClick={() => startQuiz(false)}
                className="mt-2 inline-flex items-center gap-1 text-xs font-medium underline underline-offset-2"
              >
                <RefreshCw size={11} strokeWidth={1.8} />
                Réessayer
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (state === "loading") {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex flex-col items-center justify-center gap-3 py-16 text-sm text-ink-secondary"
      >
        <Loader2
          size={20}
          strokeWidth={1.8}
          className="animate-spin text-accent"
        />
        <span>Préparation du quiz...</span>
        <span className="text-xs text-ink-muted">
          Cela peut prendre quelques instants.
        </span>
      </div>
    );
  }

  // ── Submitted ──
  if (state === "submitted" && result) {
    return (
      <QuizResults
        result={result}
        questions={questions}
        elapsed={elapsed}
        onRetry={() => {
          setState("idle");
          setElapsed(0);
        }}
        onRegenerate={() => startQuiz(true)}
      />
    );
  }

  // ── Active ──
  const question = questions[currentQ];
  const progress = ((currentQ + 1) / questions.length) * 100;
  const answeredCount = answers.filter((a) => a !== null && a !== -1).length;
  const isLast = currentQ === questions.length - 1;
  const revealed = revealedChoice !== null;
  const isCorrect = revealed && revealedChoice === question.correct_index;
  const diffStyle = question.difficulty
    ? (DIFFICULTY_STYLES[question.difficulty.toLowerCase()] ?? null)
    : null;

  return (
    <div className="py-6">
      {/* Top bar : progression + chrono */}
      <div className="mb-6">
        <div className="flex justify-between items-center text-xs text-ink-muted mb-2">
          <span>
            Question {currentQ + 1} sur {questions.length}
          </span>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1">
              <Clock size={11} strokeWidth={1.5} />
              {formatTime(elapsed)}
            </span>
            <span>{answeredCount} répondues</span>
          </div>
        </div>
        <div className="h-px bg-border w-full relative">
          <motion.div
            className="h-px bg-accent absolute top-0 left-0"
            initial={false}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Question */}
      <motion.div
        key={currentQ}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        <div className="flex items-start gap-3 mb-2 flex-wrap">
          <span className="font-display text-2xl font-semibold text-ink-muted leading-none mt-0.5">
            {String(currentQ + 1).padStart(2, "0")}
          </span>
          <h3 className="font-display text-lg font-semibold text-ink-primary leading-snug flex-1 min-w-0">
            {question.question}
          </h3>
          {diffStyle && (
            <span
              className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded ${diffStyle.cls}`}
            >
              {diffStyle.label}
            </span>
          )}
        </div>

        {/* Options */}
        <div className="space-y-2 mb-6 mt-5">
          {question.options.map((option, i) => {
            const isPicked = revealedChoice === i;
            const isCorrectOption = i === question.correct_index;

            let stateCls =
              "border-border bg-transparent text-ink-secondary hover:border-accent hover:text-ink-primary";
            if (revealed) {
              if (isCorrectOption) {
                stateCls = "border-success bg-success-light text-ink-primary";
              } else if (isPicked) {
                stateCls = "border-error bg-error-light text-ink-primary";
              } else {
                stateCls =
                  "border-border bg-transparent text-ink-muted opacity-60";
              }
            } else if (isPicked) {
              stateCls = "border-accent bg-accent-light text-ink-primary";
            }

            return (
              <button
                key={i}
                onClick={() => lockAnswer(i)}
                disabled={revealed}
                className={`
                  w-full text-left px-4 py-3 text-sm border rounded-card
                  transition-all duration-200 flex items-center gap-3
                  ${stateCls}
                  ${revealed ? "cursor-default" : "cursor-pointer"}
                `}
              >
                <span className="font-mono text-xs text-ink-muted shrink-0">
                  {String.fromCharCode(65 + i)}.
                </span>
                <span className="flex-1">{option}</span>
                {revealed && isCorrectOption && (
                  <Check
                    size={16}
                    strokeWidth={2}
                    className="text-success shrink-0"
                  />
                )}
                {revealed && isPicked && !isCorrectOption && (
                  <XIcon
                    size={16}
                    strokeWidth={2}
                    className="text-error shrink-0"
                  />
                )}
              </button>
            );
          })}
        </div>

        {/* Feedback immédiat (révélé) */}
        <AnimatePresence>
          {revealed && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className={`mb-6 p-4 rounded-card border ${
                isCorrect
                  ? "border-success/20 bg-success-light"
                  : "border-error/20 bg-error-light"
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                {isCorrect ? (
                  <>
                    <Check
                      size={14}
                      strokeWidth={2}
                      className="text-success"
                    />
                    <span className="text-sm font-semibold text-success">
                      Bonne réponse !
                    </span>
                  </>
                ) : (
                  <>
                    <XIcon size={14} strokeWidth={2} className="text-error" />
                    <span className="text-sm font-semibold text-error">
                      Pas tout à fait. La bonne réponse est{" "}
                      <span className="font-mono">
                        {String.fromCharCode(65 + question.correct_index)}
                      </span>
                      .
                    </span>
                  </>
                )}
              </div>
              <p
                className="text-xs leading-relaxed text-ink-secondary"
              >
                {question.explanation}
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Navigation */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        {!revealed ? (
          <button
            onClick={skipQuestion}
            className="btn-ghost text-sm flex items-center gap-1 text-ink-muted"
            title="Passer cette question"
          >
            <SkipForward size={14} strokeWidth={1.5} />
            Passer
          </button>
        ) : (
          <div />
        )}

        {!isLast ? (
          <button
            onClick={goToNext}
            disabled={!revealed}
            className="btn-primary text-sm flex items-center gap-1 disabled:opacity-40"
          >
            Suivante
            <ArrowRight size={14} strokeWidth={1.5} />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!revealed}
            className="btn-primary text-sm disabled:opacity-40"
          >
            Voir mes résultats
          </button>
        )}
      </div>
    </div>
  );
}

function QuizResults({
  result,
  questions,
  elapsed,
  onRetry,
  onRegenerate,
}: {
  result: QuizResult;
  questions: QuizQuestion[];
  elapsed: number;
  onRetry: () => void;
  onRegenerate: () => void;
}) {
  const label =
    result.percentage >= 80
      ? "Excellent !"
      : result.percentage >= 60
        ? "Bien joué."
        : "À revoir.";

  return (
    <div className="py-8">
      {/* Score */}
      <div className="text-center mb-10">
        <p className="font-display text-5xl font-bold text-ink-primary">
          {result.score}/{result.total}
        </p>
        <p className="text-sm text-ink-secondary mt-2">{label}</p>
        <p className="text-xs text-ink-muted mt-1">
          {result.percentage}% de bonnes réponses · Temps :{" "}
          {formatTime(elapsed)}
        </p>
      </div>

      {/* Détails — explications visibles pour TOUTES les questions */}
      <div className="space-y-3">
        {result.details.map((d: Record<string, unknown>, i: number) => {
          const q = questions[i];
          const correct = d.correct as boolean;
          const userAnswer = d.user_answer as number;
          const correctIndex = d.correct_index as number;
          const skipped = userAnswer === -1 || userAnswer === null;
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.04 }}
              className={`p-3 rounded-card border ${
                correct
                  ? "border-success/20 bg-success-light/70"
                  : skipped
                    ? "border-amber-200 bg-amber-50/40"
                    : "border-error/20 bg-error-light/70"
              }`}
            >
              <div className="flex items-start gap-2">
                {correct ? (
                  <Check
                    size={16}
                    strokeWidth={1.5}
                    className="text-success mt-0.5 shrink-0"
                  />
                ) : skipped ? (
                  <SkipForward
                    size={16}
                    strokeWidth={1.5}
                    className="text-amber-600 mt-0.5 shrink-0"
                  />
                ) : (
                  <XIcon
                    size={16}
                    strokeWidth={1.5}
                    className="text-error mt-0.5 shrink-0"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-ink-primary font-medium">
                    {i + 1}. {d.question as string}
                  </p>
                  {q && (
                    <div className="mt-2 space-y-0.5 text-xs">
                      {!correct && !skipped && (
                        <p className="text-error">
                          <span className="font-mono">
                            {String.fromCharCode(65 + userAnswer)}
                          </span>{" "}
                          (votre réponse) — {q.options[userAnswer]}
                        </p>
                      )}
                      {skipped && (
                        <p className="text-amber-700">Question passée.</p>
                      )}
                      <p className="text-success">
                        <span className="font-mono">
                          {String.fromCharCode(65 + correctIndex)}
                        </span>{" "}
                        (bonne réponse) — {q.options[correctIndex]}
                      </p>
                    </div>
                  )}
                  <p className="text-xs text-ink-secondary mt-2 leading-relaxed">
                    <span className="font-medium">Explication :</span>{" "}
                    {d.explanation as string}
                  </p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-center gap-4 mt-8">
        <button onClick={onRetry} className="btn-ghost text-sm">
          Refaire ce quiz
        </button>
        <button
          onClick={onRegenerate}
          className="btn-primary text-sm flex items-center gap-1.5"
        >
          <RefreshCw size={14} strokeWidth={1.8} />
          Nouveau quiz
        </button>
      </div>
    </div>
  );
}
