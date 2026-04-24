/**
 * SummaryView — Résumés par chapitre en accordéon.
 *
 * Style éditorial : lignes de séparation fines, pas d'ombres sur chaque item.
 * Concepts clés : tags avec fond accent-light.
 * Résumés structurés en points clés (bullet points).
 */
"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Loader2, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { fetchSummary, type ChapterSummary } from "@/lib/api";

interface SummaryViewProps {
  courseId: string;
}

const POLL_INTERVAL = 8_000;

export default function SummaryView({ courseId }: SummaryViewProps) {
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const doFetch = useCallback(
    async (signal?: AbortSignal) => {
      const res = await fetchSummary(courseId);
      if (signal?.aborted) return null;
      return res;
    },
    [courseId],
  );

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setGenerating(false);
    stopPolling();

    doFetch()
      .then((res) => {
        if (cancelled || !res) return;
        if (res.status === "ready") {
          setChapters(res.chapters);
          setLoading(false);
        } else {
          // Generation started — switch to polling mode
          setLoading(false);
          setGenerating(true);
          pollRef.current = setInterval(async () => {
            try {
              const poll = await fetchSummary(courseId);
              if (cancelled) return;
              if (poll.status === "ready") {
                setChapters(poll.chapters);
                setGenerating(false);
                stopPolling();
              }
            } catch {
              // Ignore transient polling errors
            }
          }, POLL_INTERVAL);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Impossible de charger les résumés.",
          );
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
      stopPolling();
    };
  }, [courseId, doFetch, stopPolling]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Loader2
          size={24}
          strokeWidth={1.5}
          className="animate-spin text-accent"
        />
        <p className="text-sm text-ink-secondary">Chargement…</p>
      </div>
    );
  }

  if (generating) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Loader2
          size={24}
          strokeWidth={1.5}
          className="animate-spin text-accent"
        />
        <p className="text-sm text-ink-secondary">
          Génération des résumés en cours…
        </p>
        <p className="text-xs text-ink-muted">
          La première génération peut prendre plusieurs minutes. Cette page se
          met à jour automatiquement.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-sm text-error">{error}</p>
      </div>
    );
  }

  if (chapters.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-sm text-ink-muted">Aucun résumé disponible.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-3 px-1">
        <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-accent bg-accent-light/40 px-1.5 py-0.5 rounded">
          <Sparkles size={10} strokeWidth={2} />
          {chapters.some((c) => c.llm_used)
            ? "Résumé NLP + Deep Learning, reformulé par LLM"
            : "Résumé extractif (LLM indisponible)"}
        </span>
      </div>
      <div className="divide-y divide-border">
        {chapters.map((chapter, i) => (
          <AccordionItem
            key={i}
            chapter={chapter}
            isOpen={openIndex === i}
            onToggle={() => setOpenIndex(openIndex === i ? null : i)}
            index={i}
          />
        ))}
      </div>
    </div>
  );
}

function AccordionItem({
  chapter,
  isOpen,
  onToggle,
  index,
}: {
  chapter: ChapterSummary;
  isOpen: boolean;
  onToggle: () => void;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut", delay: index * 0.05 }}
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-4 px-1 text-left
                   hover:bg-accent-light/20 transition-colors duration-200"
      >
        <div className="flex items-baseline gap-3">
          <span className="text-xs font-mono text-ink-muted">
            {String(index + 1).padStart(2, "0")}
          </span>
          <h3 className="font-display text-base font-semibold text-ink-primary">
            {chapter.title}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-ink-muted">
            p. {chapter.pages[0]}–{chapter.pages[chapter.pages.length - 1]}
          </span>
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown
              size={16}
              strokeWidth={1.5}
              className="text-ink-muted"
            />
          </motion.div>
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="pb-5 px-1 pl-9">
              {/* Si le LLM a produit une fiche pédagogique, on l'affiche en priorité.
                  Sinon, fallback sur le résumé extractif (bullets). */}
              {chapter.pedagogic ? (
                <SummaryContent text={chapter.pedagogic} />
              ) : (
                <SummaryContent text={chapter.summary} />
              )}

              {chapter.key_concepts.length > 0 && (
                <div className="mt-4 pt-3 border-t border-border/50 flex flex-wrap gap-1.5">
                  {chapter.key_concepts.map((concept, i) => (
                    <span key={i} className="tag">
                      {concept}
                    </span>
                  ))}
                </div>
              )}

              {chapter.techniques && chapter.techniques.length > 0 && (
                <div className="mt-3 flex flex-wrap items-center gap-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-ink-muted">
                    Techniques
                  </span>
                  {chapter.techniques.map((t, i) => (
                    <span
                      key={i}
                      className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-bg-secondary text-ink-secondary ring-1 ring-border"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/** Renders structured summary text via Markdown (supports bullets, bold, italic, headers). */
function SummaryContent({ text }: { text: string }) {
  if (!text) {
    return (
      <p className="text-sm text-ink-muted italic">
        Aucun contenu de résumé pour ce chapitre.
      </p>
    );
  }

  // Convertit les bullets `• ` en `- ` pour ReactMarkdown
  const normalized = text
    .split("\n")
    .map((line) => line.replace(/^\s*•\s*/, "- "))
    .join("\n");

  return (
    <div className="text-sm text-ink-secondary leading-relaxed">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="my-2">{children}</p>,
          ul: ({ children }) => (
            <ul className="my-2 space-y-1.5 list-none">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="my-2 space-y-1.5 list-decimal list-inside">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="flex gap-2">
              <span className="text-accent shrink-0">•</span>
              <span>{children}</span>
            </li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-ink-primary">
              {children}
            </strong>
          ),
          em: ({ children }) => <em className="italic">{children}</em>,
          code: ({ children }) => (
            <code className="bg-bg-secondary px-1 rounded text-xs font-mono">
              {children}
            </code>
          ),
          // h1 = titre du chapitre (déjà affiché dans l'accordion header) → on le masque
          h1: () => null,
          // h2 = sections de la fiche (🎯 Objectifs, 📚 Concepts, etc.)
          h2: ({ children }) => (
            <h4 className="font-display text-sm font-semibold text-ink-primary mt-4 mb-2 pb-1 border-b border-border/40">
              {children}
            </h4>
          ),
          h3: ({ children }) => (
            <h5 className="font-display text-sm font-semibold text-ink-primary mt-3 mb-1">
              {children}
            </h5>
          ),
          h4: ({ children }) => (
            <h6 className="font-display text-sm font-medium text-ink-primary mt-2 mb-1">
              {children}
            </h6>
          ),
        }}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
