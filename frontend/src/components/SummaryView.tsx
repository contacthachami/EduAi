"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BookOpenText, ChevronDown, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import PipelineBanner from "@/components/PipelineBanner";
import {
  fetchSummary,
  type ChapterSummary,
  type PipelineMeta,
} from "@/lib/api";

interface SummaryViewProps {
  courseId: string;
}

const POLL_INTERVAL = 8_000;

function pageRange(pages: number[]) {
  if (!pages.length) return "Pages non précisées";
  const start = pages[0];
  const end = pages[pages.length - 1];
  return start === end ? `p. ${start}` : `p. ${start}-${end}`;
}

export default function SummaryView({ courseId }: SummaryViewProps) {
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [pipelineMeta, setPipelineMeta] = useState<PipelineMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openIndex, setOpenIndex] = useState<number | null>(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setGenerating(false);
    setError(null);
    stopPolling();

    fetchSummary(courseId)
      .then((response) => {
        if (cancelled) return;
        if (response.status === "ready") {
          setChapters(response.chapters);
          setPipelineMeta(response.pipeline_meta ?? null);
          setLoading(false);
        } else {
          setLoading(false);
          setGenerating(true);
          pollRef.current = setInterval(async () => {
            try {
              const poll = await fetchSummary(courseId);
              if (cancelled) return;
              if (poll.status === "ready") {
                setChapters(poll.chapters);
                setPipelineMeta(poll.pipeline_meta ?? null);
                setGenerating(false);
                stopPolling();
              }
            } catch {
              // Temporary backend delays are expected during generation.
            }
          }, POLL_INTERVAL);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Impossible de charger la synthèse.",
          );
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
      stopPolling();
    };
  }, [courseId, stopPolling]);

  if (loading) {
    return (
      <div className="panel flex flex-col items-center justify-center gap-3 px-5 py-16">
        <Loader2 size={24} strokeWidth={1.8} className="animate-spin text-accent" />
        <p className="text-sm text-ink-secondary">Chargement de la synthèse...</p>
      </div>
    );
  }

  if (generating) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="panel flex flex-col items-center justify-center gap-3 px-5 py-16 text-center"
      >
        <Loader2 size={24} strokeWidth={1.8} className="animate-spin text-accent" />
        <h2 className="text-base font-semibold text-ink-primary">
          Synthèse en préparation
        </h2>
        <p className="max-w-lg text-sm text-ink-secondary">
          La première génération peut prendre quelques minutes. La page se mettra
          à jour automatiquement dès que la synthèse sera prête.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div role="alert" className="status-message status-message-error">
        {error}
      </div>
    );
  }

  if (chapters.length === 0) {
    return (
      <div className="rounded-panel border border-dashed border-border-strong bg-bg-subtle px-5 py-12 text-center">
        <BookOpenText size={24} strokeWidth={1.8} className="mx-auto text-ink-muted" />
        <h2 className="mt-3 text-base font-semibold text-ink-primary">
          Aucune synthèse disponible
        </h2>
        <p className="mt-2 text-sm text-ink-secondary">
          Le cours est prêt, mais aucune synthèse n&apos;a encore été produite.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-5 rounded-panel border border-border bg-bg-subtle px-5 py-4">
        <p className="eyebrow">Synthèse pédagogique</p>
        <h2 className="mt-1 text-2xl font-semibold text-ink-primary">
          Chapitres et points clés
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-ink-secondary">
          Parcourez les sections du document, puis ouvrez un chapitre pour lire
          la synthèse et les notions importantes.
        </p>
      </div>

      {pipelineMeta && <PipelineBanner meta={pipelineMeta} />}

      <div className="panel overflow-hidden">
        <div className="divide-y divide-border">
          {chapters.map((chapter, index) => (
            <AccordionItem
              key={`${chapter.title}-${index}`}
              chapter={chapter}
              index={index}
              isOpen={openIndex === index}
              onToggle={() => setOpenIndex(openIndex === index ? null : index)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function AccordionItem({
  chapter,
  index,
  isOpen,
  onToggle,
}: {
  chapter: ChapterSummary;
  index: number;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const contentId = `chapter-summary-${index}`;
  const triggerA11yProps = {
    "aria-controls": contentId,
    "aria-expanded": isOpen ? "true" : "false",
  } as const;

  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut", delay: index * 0.025 }}
    >
      <button
        type="button"
        onClick={onToggle}
        {...triggerA11yProps}
        className="flex w-full flex-col gap-3 px-4 py-4 text-left transition hover:bg-bg-subtle sm:flex-row sm:items-center sm:justify-between sm:px-5"
      >
        <span className="flex min-w-0 items-start gap-3">
          <span className="mt-1 font-mono text-xs text-ink-muted">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span className="min-w-0">
            <span className="block break-words text-base font-semibold text-ink-primary">
              {chapter.title}
            </span>
            {chapter.key_concepts.length > 0 && (
              <span className="mt-1 block text-xs text-ink-muted">
                {chapter.key_concepts.slice(0, 3).join(", ")}
              </span>
            )}
          </span>
        </span>
        <span className="flex shrink-0 items-center gap-2 text-xs text-ink-muted">
          {pageRange(chapter.pages)}
          <motion.span
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.18 }}
          >
            <ChevronDown size={17} strokeWidth={1.8} />
          </motion.span>
        </span>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            id={contentId}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-5 sm:px-5 sm:pl-12">
              <SummaryContent text={chapter.pedagogic || chapter.summary} />

              {chapter.key_concepts.length > 0 && (
                <div className="mt-5 flex flex-wrap gap-2 border-t border-border pt-4">
                  {chapter.key_concepts.map((concept) => (
                    <span key={concept} className="tag">
                      {concept}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
}

function SummaryContent({ text }: { text?: string | null }) {
  if (!text) {
    return (
      <p className="text-sm italic text-ink-muted">
        Aucun contenu disponible pour ce chapitre.
      </p>
    );
  }

  const normalized = text
    .split("\n")
    .map((line) => line.replace(/^\s*•\s*/, "- "))
    .join("\n");

  return (
    <div className="text-sm leading-relaxed text-ink-secondary">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="my-2">{children}</p>,
          ul: ({ children }) => (
            <ul className="my-3 list-disc space-y-1.5 pl-5">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="my-3 list-decimal space-y-1.5 pl-5">{children}</ol>
          ),
          h1: () => null,
          h2: ({ children }) => (
            <h3 className="mt-5 border-b border-border pb-1 text-base font-semibold text-ink-primary first:mt-0">
              {children}
            </h3>
          ),
          h3: ({ children }) => (
            <h4 className="mt-4 text-sm font-semibold text-ink-primary">
              {children}
            </h4>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-ink-primary">{children}</strong>
          ),
          code: ({ children }) => (
            <code className="rounded bg-bg-secondary px-1 py-0.5 font-mono text-xs">
              {children}
            </code>
          ),
        }}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
