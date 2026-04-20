/**
 * QuizModule — Quiz interactif style examen académique.
 *
 * Questions numérotées en Playfair Display.
 * Barre de progression : ligne fine.
 * Score en grand chiffre, pas de confetti.
 */
"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Loader2, Check, X as XIcon, ArrowRight } from "lucide-react";
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

export default function QuizModule({ courseId }: QuizModuleProps) {
  const [state, setState] = useState<QuizState>("idle");
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [quizId, setQuizId] = useState("");
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [numQuestions, setNumQuestions] = useState(5);

  const startQuiz = async () => {
    setState("loading");
    setError(null);
    try {
      const res = await fetchQuiz(courseId, numQuestions);
      setQuestions(res.questions);
      setQuizId(res.quiz_id);
      setAnswers(new Array(res.questions.length).fill(null));
      setCurrentQ(0);
      setResult(null);
      setState("active");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Impossible de générer le quiz."
      );
      setState("idle");
    }
  };

  const selectOption = (optionIndex: number) => {
    setAnswers((prev) => {
      const next = [...prev];
      next[currentQ] = optionIndex;
      return next;
    });
  };

  const nextQuestion = () => {
    if (currentQ < questions.length - 1) {
      setCurrentQ((prev) => prev + 1);
    }
  };

  const prevQuestion = () => {
    if (currentQ > 0) {
      setCurrentQ((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    const filled = answers.filter((a) => a !== null) as number[];
    if (filled.length < questions.length) return;

    setState("loading");
    try {
      const res = await submitQuiz(quizId, filled);
      setResult(res);
      setState("submitted");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erreur lors de la soumission."
      );
      setState("active");
    }
  };

  // ── Idle ──
  if (state === "idle") {
    return (
      <div className="text-center py-16">
        <h3 className="font-display text-lg font-semibold text-ink-primary">
          Quiz de révision
        </h3>
        <p className="text-sm text-ink-secondary mt-2 mb-6">
          Testez vos connaissances sur le contenu du cours.
        </p>

        <div className="inline-flex items-center gap-3 mb-6">
          <label className="text-sm text-ink-secondary">Nombre de questions :</label>
          <select
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            className="px-3 py-1.5 text-sm border border-border rounded-card bg-bg-card
                       text-ink-primary focus:outline-none focus:border-accent"
          >
            {[5, 10, 15, 20].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <div>
          <button onClick={startQuiz} className="btn-primary">
            Commencer le quiz
          </button>
        </div>

        {error && <p className="text-sm text-error mt-4">{error}</p>}
      </div>
    );
  }

  // ── Loading ──
  if (state === "loading") {
    return (
      <div className="flex items-center justify-center py-16 gap-2 text-sm text-ink-secondary">
        <Loader2 size={16} strokeWidth={1.5} className="animate-spin text-accent" />
        Génération du quiz…
      </div>
    );
  }

  // ── Submitted ──
  if (state === "submitted" && result) {
    return <QuizResults result={result} onRetry={() => setState("idle")} />;
  }

  // ── Active ──
  const question = questions[currentQ];
  const progress = ((currentQ + 1) / questions.length) * 100;
  const allAnswered = answers.every((a) => a !== null);

  return (
    <div className="py-6">
      {/* Barre de progression */}
      <div className="mb-8">
        <div className="flex justify-between text-xs text-ink-muted mb-2">
          <span>Question {currentQ + 1} sur {questions.length}</span>
          <span>{answers.filter((a) => a !== null).length} répondues</span>
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
        <div className="flex items-baseline gap-3 mb-6">
          <span className="font-display text-2xl font-semibold text-ink-muted">
            {String(currentQ + 1).padStart(2, "0")}
          </span>
          <h3 className="font-display text-lg font-semibold text-ink-primary leading-snug">
            {question.question}
          </h3>
        </div>

        {/* Options */}
        <div className="space-y-2 mb-8">
          {question.options.map((option, i) => {
            const isSelected = answers[currentQ] === i;
            return (
              <button
                key={i}
                onClick={() => selectOption(i)}
                className={`
                  w-full text-left px-4 py-3 text-sm border rounded-card
                  transition-all duration-200
                  ${isSelected
                    ? "border-accent bg-accent-light text-ink-primary"
                    : "border-border bg-transparent text-ink-secondary hover:border-accent hover:text-ink-primary"
                  }
                `}
              >
                <span className="font-mono text-xs text-ink-muted mr-3">
                  {String.fromCharCode(65 + i)}.
                </span>
                {option}
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={prevQuestion}
          disabled={currentQ === 0}
          className="btn-ghost text-sm disabled:opacity-30"
        >
          Précédente
        </button>

        {currentQ < questions.length - 1 ? (
          <button
            onClick={nextQuestion}
            disabled={answers[currentQ] === null}
            className="btn-ghost text-sm flex items-center gap-1 disabled:opacity-30"
          >
            Suivante
            <ArrowRight size={14} strokeWidth={1.5} />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!allAnswered}
            className="btn-primary text-sm disabled:opacity-40"
          >
            Soumettre
          </button>
        )}
      </div>
    </div>
  );
}

function QuizResults({
  result,
  onRetry,
}: {
  result: QuizResult;
  onRetry: () => void;
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
        <p className="text-xs text-ink-muted mt-1">{result.percentage}% de bonnes réponses</p>
      </div>

      {/* Détails */}
      <div className="divide-y divide-border">
        {result.details.map((d: Record<string, unknown>, i: number) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.05 }}
            className="py-3 flex items-start gap-3"
          >
            {d.correct ? (
              <Check size={16} strokeWidth={1.5} className="text-success mt-0.5 flex-shrink-0" />
            ) : (
              <XIcon size={16} strokeWidth={1.5} className="text-error mt-0.5 flex-shrink-0" />
            )}
            <div>
              <p className="text-sm text-ink-primary">{d.question as string}</p>
              {!d.correct && (
                <p className="text-xs text-ink-muted mt-1">
                  {d.explanation as string}
                </p>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Recommencer */}
      <div className="text-center mt-8">
        <button onClick={onRetry} className="btn-ghost text-sm">
          Recommencer un quiz
        </button>
      </div>
    </div>
  );
}
