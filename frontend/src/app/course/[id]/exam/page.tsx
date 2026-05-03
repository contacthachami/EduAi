"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { api } from "@/lib/auth";
import { Clock, Award, AlertTriangle, ArrowLeft } from "lucide-react";

interface ExamQuestion {
  id: string;
  question: string;
  options: string[];
  difficulty: string;
}

interface ExamResult {
  score: number;
  total: number;
  percentage: number;
  grade: string;
  passed: boolean;
  details: any[];
}

export default function ExamPage() {
  const params = useParams();
  const courseId = params.id as string;

  const [phase, setPhase] = useState<"config" | "exam" | "result">("config");
  const [numQuestions, setNumQuestions] = useState(15);
  const [timeLimit, setTimeLimit] = useState(20);
  const [questions, setQuestions] = useState<ExamQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [examId, setExamId] = useState("");
  const [timeLeft, setTimeLeft] = useState(0);
  const [result, setResult] = useState<ExamResult | null>(null);
  const [loading, setLoading] = useState(false);

  // Timer
  useEffect(() => {
    if (phase !== "exam" || timeLeft <= 0) return;
    const interval = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(interval);
          handleSubmit();
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [phase, timeLeft]);

  const startExam = async () => {
    setLoading(true);
    try {
      const res = await api.post("/api/exam/start", {
        course_id: courseId,
        num_questions: numQuestions,
        time_limit_minutes: timeLimit,
      });
      setQuestions(res.data.questions);
      setExamId(res.data.exam_id);
      setTimeLeft(timeLimit * 60);
      setAnswers({});
      setPhase("exam");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erreur");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    const answersArray = questions.map((q) => answers[q.id] ?? -1);
    const timeSpent = timeLimit * 60 - timeLeft;
    try {
      const res = await api.post("/api/exam/submit", {
        exam_id: examId,
        answers: answersArray,
        time_spent_seconds: timeSpent,
      });
      setResult(res.data);
      setPhase("result");
    } catch {
      alert("Erreur lors de la soumission.");
    }
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  // Config phase
  if (phase === "config") {
    return (
      <div className="min-h-screen bg-[#F6F3EF] flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md bg-white rounded-lg border border-[#DED8D1] p-8"
        >
          <Link
            href={`/course/${courseId}`}
            className="inline-flex items-center gap-1.5 text-sm text-[#5F5750] hover:text-[#B85B2A] transition mb-4"
          >
            <ArrowLeft className="w-4 h-4" /> Retour au cours
          </Link>
          <h1 className="font-serif text-2xl font-bold text-[#171412] mb-2">
            Mode Examen
          </h1>
          <p className="text-[#5F5750] text-sm mb-6">
            Conditions réelles : chronomètre, pas de retour en arrière possible.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#171412] mb-1">
                Nombre de questions
              </label>
              <input
                type="range"
                min={5}
                max={40}
                step={5}
                value={numQuestions}
                onChange={(e) => setNumQuestions(+e.target.value)}
                className="w-full accent-[#B85B2A]"
              />
              <span className="text-sm text-[#5F5750]">
                {numQuestions} questions
              </span>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#171412] mb-1">
                Durée limite
              </label>
              <input
                type="range"
                min={5}
                max={60}
                step={5}
                value={timeLimit}
                onChange={(e) => setTimeLimit(+e.target.value)}
                className="w-full accent-[#B85B2A]"
              />
              <span className="text-sm text-[#5F5750]">
                {timeLimit} minutes
              </span>
            </div>
          </div>

          <button
            onClick={startExam}
            disabled={loading}
            className="w-full mt-8 py-2.5 rounded-md bg-[#B85B2A] text-white font-medium hover:bg-[#9A4B22] transition disabled:opacity-50"
          >
            {loading ? "Préparation..." : "Commencer l'examen"}
          </button>
        </motion.div>
      </div>
    );
  }

  // Exam phase
  if (phase === "exam") {
    const answeredCount = Object.keys(answers).length;
    return (
      <div className="min-h-screen bg-[#F6F3EF] p-6">
        <div className="max-w-3xl mx-auto">
          {/* Timer bar */}
          <div className="sticky top-0 z-10 bg-white rounded-lg border border-[#DED8D1] p-3 mb-6 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-[#5F5750]">
              <Clock className="w-4 h-4" />
              <span className={timeLeft < 60 ? "text-red-600 font-bold" : ""}>
                {formatTime(timeLeft)}
              </span>
            </div>
            <span className="text-sm text-[#8D837A]">
              {answeredCount}/{questions.length} répondu
              {answeredCount > 1 ? "es" : ""}
            </span>
            <button
              onClick={handleSubmit}
              className="px-4 py-1.5 rounded bg-[#B85B2A] text-white text-sm font-medium hover:bg-[#9A4B22]"
            >
              Terminer
            </button>
          </div>

          {/* Questions */}
          <div className="space-y-6">
            {questions.map((q, i) => (
              <div
                key={q.id}
                className="bg-white rounded-lg border border-[#DED8D1] p-6"
              >
                <div className="flex items-start gap-3 mb-4">
                  <span className="text-sm font-bold text-[#B85B2A] bg-[#B85B2A]/10 px-2 py-0.5 rounded">
                    {i + 1}
                  </span>
                  <p className="text-[#171412] font-medium">{q.question}</p>
                </div>
                <div className="space-y-2 ml-8">
                  {q.options.map((opt, oi) => (
                    <label
                      key={oi}
                      className={`flex items-center gap-3 p-3 rounded-md border cursor-pointer transition ${
                        answers[q.id] === oi
                          ? "border-[#B85B2A] bg-[#B85B2A]/5"
                          : "border-[#DED8D1] hover:border-[#8D837A]"
                      }`}
                    >
                      <input
                        type="radio"
                        name={q.id}
                        checked={answers[q.id] === oi}
                        onChange={() => setAnswers({ ...answers, [q.id]: oi })}
                        className="accent-[#B85B2A]"
                      />
                      <span className="text-sm text-[#171412]">{opt}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Result phase
  if (phase === "result" && result) {
    const gradeColor = result.passed ? "#6B8F71" : "#C44D4D";
    return (
      <div className="min-h-screen bg-[#F6F3EF] flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md bg-white rounded-lg border border-[#DED8D1] p-8 text-center"
        >
          <div
            className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl font-bold text-white"
            style={{ background: gradeColor }}
          >
            {result.grade}
          </div>
          <h2 className="font-serif text-2xl font-bold text-[#171412]">
            {result.percentage}%
          </h2>
          <p className="text-[#5F5750] mt-1">
            {result.score}/{result.total} bonnes réponses
          </p>
          <p className="mt-2 text-sm font-medium" style={{ color: gradeColor }}>
            {result.passed
              ? "Examen réussi !"
              : "Examen non réussi — Continue à réviser."}
          </p>

          <div className="mt-8 flex gap-3 justify-center">
            <button
              onClick={() => setPhase("config")}
              className="px-4 py-2 rounded-md border border-[#DED8D1] text-sm text-[#5F5750] hover:border-[#B85B2A]"
            >
              Repasser
            </button>
            <Link
              href={`/course/${courseId}`}
              className="px-4 py-2 rounded-md bg-[#B85B2A] text-white text-sm font-medium hover:bg-[#9A4B22]"
            >
              Retour au cours
            </Link>
          </div>
        </motion.div>
      </div>
    );
  }

  return null;
}
