/**
 * Page cours — Onglets : Chat · Résumé · Quiz
 *
 * Layout 60/40 asymétrique quand le contenu le permet.
 * Transitions d'opacité simples entre tabs.
 */
"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2 } from "lucide-react";
import { fetchCourse, type CourseDetail } from "@/lib/api";
import ChatInterface from "@/components/ChatInterface";
import SummaryView from "@/components/SummaryView";
import QuizModule from "@/components/QuizModule";

type Tab = "chat" | "resume" | "quiz";

const TABS: { key: Tab; label: string }[] = [
  { key: "chat", label: "Questions" },
  { key: "resume", label: "Résumé" },
  { key: "quiz", label: "Quiz" },
];

const INDEX_POLL_INTERVAL = 5_000;

export default function CoursePage() {
  const params = useParams();
  const courseId = params.id as string;

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    fetchCourse(courseId)
      .then((c) => {
        setCourse(c);
        if (c.status === "processing") {
          pollRef.current = setInterval(async () => {
            try {
              const updated = await fetchCourse(courseId);
              setCourse(updated);
              if (updated.status !== "processing") {
                clearInterval(pollRef.current!);
                pollRef.current = null;
              }
            } catch {
              /* ignore poll errors */
            }
          }, INDEX_POLL_INTERVAL);
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Cours introuvable.");
      })
      .finally(() => setLoading(false));

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [courseId]);

  if (loading) {
    return (
      <div className="page-container py-16 flex items-center gap-2 text-sm text-ink-secondary">
        <Loader2
          size={16}
          strokeWidth={1.5}
          className="animate-spin text-accent"
        />
        Chargement du cours…
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="page-container py-16">
        <p className="text-sm text-error">{error || "Cours introuvable."}</p>
        <a
          href="/"
          className="text-sm text-accent mt-4 inline-block hover:text-accent-hover"
        >
          ← Retour aux cours
        </a>
      </div>
    );
  }

  return (
    <div className="page-container py-8">
      {/* En-tête du cours */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        <a
          href="/"
          className="text-xs text-ink-muted hover:text-accent transition-colors"
        >
          ← Retour aux cours
        </a>
        <h1 className="font-display text-2xl font-bold text-ink-primary mt-4">
          {course.name}
        </h1>
        <p className="text-xs text-ink-muted mt-1">{course.pages} pages</p>
      </motion.div>

      {/* Indexation en cours */}
      {course.status === "processing" && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 card px-6 py-8 text-center"
        >
          <Loader2
            size={24}
            strokeWidth={1.5}
            className="animate-spin text-accent mx-auto mb-3"
          />
          <p className="text-sm font-medium text-accent">
            Indexation du cours en cours…
          </p>
          <p className="text-xs text-ink-muted mt-1">
            Les embeddings sont générés en arrière-plan. Cette page se met à
            jour automatiquement.
          </p>
        </motion.div>
      )}

      {/* Onglets (seulement quand le cours est prêt) */}
      {course.status === "ready" && (
        <>
          <div className="mt-8 border-b border-border">
            <div className="flex gap-6">
              {TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`
                    pb-2.5 text-sm font-medium transition-colors duration-200 relative
                    ${
                      activeTab === tab.key
                        ? "text-ink-primary"
                        : "text-ink-muted hover:text-ink-secondary"
                    }
                  `}
                >
                  {tab.label}
                  {activeTab === tab.key && (
                    <motion.div
                      layoutId="tab-indicator"
                      className="absolute bottom-0 left-0 right-0 h-px bg-accent"
                      transition={{ duration: 0.2 }}
                    />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Contenu de l'onglet */}
          <div className="mt-6">
            <AnimatePresence mode="wait">
              {activeTab === "chat" && (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="card overflow-hidden"
                  style={{ height: "calc(100vh - 280px)", minHeight: "500px" }}
                >
                  <ChatInterface courseId={courseId} courseName={course.name} />
                </motion.div>
              )}

              {activeTab === "resume" && (
                <motion.div
                  key="resume"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <SummaryView courseId={courseId} />
                </motion.div>
              )}

              {activeTab === "quiz" && (
                <motion.div
                  key="quiz"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="card px-6"
                >
                  <QuizModule courseId={courseId} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </>
      )}
    </div>
  );
}
