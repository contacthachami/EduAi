"use client";

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  CircleDashed,
  Loader2,
  MessageSquareText,
  NotebookTabs,
  PenLine,
} from "lucide-react";
import ChatInterface from "@/components/ChatInterface";
import QuizModule from "@/components/QuizModule";
import SummaryView from "@/components/SummaryView";
import { fetchCourse, type CourseDetail } from "@/lib/api";

type Tab = "chat" | "resume" | "quiz";

const TABS: { key: Tab; label: string; description: string; icon: typeof MessageSquareText }[] = [
  {
    key: "chat",
    label: "Questions",
    description: "Interroger le contenu du PDF",
    icon: MessageSquareText,
  },
  {
    key: "resume",
    label: "Synthèse",
    description: "Comprendre les chapitres",
    icon: NotebookTabs,
  },
  {
    key: "quiz",
    label: "Quiz",
    description: "S'entraîner à réviser",
    icon: PenLine,
  },
];

const INDEX_POLL_INTERVAL = 5_000;

export default function CoursePage() {
  const params = useParams();
  const courseId = params.id as string;
  const tabBaseId = useId();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const initial = await fetchCourse(courseId);
        if (cancelled) return;
        setCourse(initial);

        if (initial.status === "processing") {
          pollRef.current = setInterval(async () => {
            try {
              const updated = await fetchCourse(courseId);
              if (cancelled) return;
              setCourse(updated);
              if (updated.status !== "processing" && pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
              }
            } catch {
              // Keep the existing course state during transient polling errors.
            }
          }, INDEX_POLL_INTERVAL);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Cours introuvable.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();

    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [courseId]);

  const handleTabKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const currentIndex = TABS.findIndex((tab) => tab.key === activeTab);
    if (currentIndex < 0) return;

    let nextIndex = currentIndex;
    if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % TABS.length;
    if (event.key === "ArrowLeft") {
      nextIndex = (currentIndex - 1 + TABS.length) % TABS.length;
    }
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = TABS.length - 1;

    if (nextIndex !== currentIndex) {
      event.preventDefault();
      setActiveTab(TABS[nextIndex].key);
      window.setTimeout(() => {
        document.getElementById(`${tabBaseId}-${TABS[nextIndex].key}-tab`)?.focus();
      }, 0);
    }
  };

  const getTabA11yProps = (tab: Tab, selected: boolean) =>
    ({
      "aria-controls": `${tabBaseId}-${tab}-panel`,
      "aria-selected": selected ? "true" : "false",
      tabIndex: selected ? 0 : -1,
    }) as const;

  const getPanelA11yProps = (tab: Tab) =>
    ({
      "aria-labelledby": `${tabBaseId}-${tab}-tab`,
    }) as const;

  if (loading) {
    return (
      <div className="page-container py-10">
        <div className="status-message status-message-info flex items-center gap-2">
          <Loader2 size={16} strokeWidth={1.8} className="animate-spin text-accent" />
          <span>Chargement du cours...</span>
        </div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="page-container py-10">
        <div role="alert" className="status-message status-message-error flex gap-2">
          <AlertCircle size={16} strokeWidth={1.8} className="mt-0.5 shrink-0" />
          <span>{error || "Cours introuvable."}</span>
        </div>
        <Link href="/" className="btn-secondary mt-5">
          <ArrowLeft size={16} strokeWidth={1.8} />
          Retour aux cours
        </Link>
      </div>
    );
  }

  return (
    <div className="page-container py-8 sm:py-10">
      <Link href="/" className="btn-ghost -ml-3">
        <ArrowLeft size={16} strokeWidth={1.8} />
        Retour aux cours
      </Link>

      <motion.header
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="mt-4 rounded-panel border border-border bg-bg-subtle px-5 py-5 sm:px-7"
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0">
            <p className="eyebrow">Espace de travail</p>
            <h1 className="mt-2 break-words text-3xl font-bold text-ink-primary">
              {course.name}
            </h1>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-secondary">
              <span className="inline-flex items-center gap-1.5">
                <BookOpen size={15} strokeWidth={1.8} />
                {course.pages} pages
              </span>
              <span className="inline-flex items-center gap-1.5">
                <CircleDashed size={15} strokeWidth={1.8} />
                {course.chunks_count} segments
              </span>
            </div>
          </div>
          <span
            className={`inline-flex w-fit items-center rounded-card px-3 py-1.5 text-xs font-semibold ${
              course.status === "ready"
                ? "bg-success-light text-success"
                : course.status === "error"
                  ? "bg-error-light text-error"
                  : "bg-warning-light text-warning"
            }`}
          >
            {course.status === "ready"
              ? "Prêt à étudier"
              : course.status === "error"
                ? "Erreur d'indexation"
                : "Indexation en cours"}
          </span>
        </div>
      </motion.header>

      {course.status === "processing" && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="panel mt-6 p-6"
          role="status"
          aria-live="polite"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <Loader2 size={24} strokeWidth={1.8} className="shrink-0 animate-spin text-accent" />
            <div>
              <h2 className="text-base font-semibold text-ink-primary">
                Préparation du cours en cours
              </h2>
              <p className="mt-1 text-sm text-ink-secondary">
                EduAI extrait les passages et prépare la recherche dans le
                document. Cette page se mettra à jour automatiquement.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {course.status === "error" && (
        <div role="alert" className="status-message status-message-error mt-6 flex gap-2">
          <AlertCircle size={16} strokeWidth={1.8} className="mt-0.5 shrink-0" />
          <span>
            L&apos;indexation du cours a échoué. Ajoutez à nouveau le PDF ou
            vérifiez que le document contient du texte lisible.
          </span>
        </div>
      )}

      {course.status === "ready" && (
        <section className="mt-6">
          <div
            role="tablist"
            aria-label="Sections du cours"
            onKeyDown={handleTabKeyDown}
            className="grid gap-2 border-b border-border pb-3 sm:grid-cols-3"
          >
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const selected = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  id={`${tabBaseId}-${tab.key}-tab`}
                  type="button"
                  role="tab"
                  {...getTabA11yProps(tab.key, selected)}
                  onClick={() => setActiveTab(tab.key)}
                  className={`rounded-card border px-4 py-3 text-left transition duration-200 ${
                    selected
                      ? "border-accent bg-accent-soft text-ink-primary"
                      : "border-transparent text-ink-secondary hover:border-border hover:bg-bg-subtle"
                  }`}
                >
                  <span className="flex items-center gap-2 text-sm font-semibold">
                    <Icon size={16} strokeWidth={1.8} />
                    {tab.label}
                  </span>
                  <span className="mt-1 block text-xs text-ink-muted">
                    {tab.description}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="mt-5">
            <AnimatePresence mode="wait">
              {activeTab === "chat" && (
                <motion.div
                  key="chat"
                  id={`${tabBaseId}-chat-panel`}
                  role="tabpanel"
                  {...getPanelA11yProps("chat")}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.18 }}
                  className="panel overflow-hidden"
                >
                  <div className="h-[min(720px,calc(100vh-230px))] min-h-[540px]">
                    <ChatInterface courseId={courseId} courseName={course.name} />
                  </div>
                </motion.div>
              )}

              {activeTab === "resume" && (
                <motion.div
                  key="resume"
                  id={`${tabBaseId}-resume-panel`}
                  role="tabpanel"
                  {...getPanelA11yProps("resume")}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.18 }}
                >
                  <SummaryView courseId={courseId} />
                </motion.div>
              )}

              {activeTab === "quiz" && (
                <motion.div
                  key="quiz"
                  id={`${tabBaseId}-quiz-panel`}
                  role="tabpanel"
                  {...getPanelA11yProps("quiz")}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.18 }}
                  className="panel px-5 sm:px-7"
                >
                  <QuizModule courseId={courseId} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </section>
      )}
    </div>
  );
}
