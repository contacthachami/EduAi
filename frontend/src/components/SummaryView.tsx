/**
 * SummaryView — Résumés par chapitre en accordéon.
 *
 * Style éditorial : lignes de séparation fines, pas d'ombres sur chaque item.
 * Concepts clés : tags avec fond accent-light.
 */
"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Loader2 } from "lucide-react";
import { fetchSummary, type ChapterSummary } from "@/lib/api";

interface SummaryViewProps {
  courseId: string;
}

const POLL_INTERVAL = 8_000; // 8 seconds between polls

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

  const doFetch = useCallback(async (signal?: AbortSignal) => {
    const res = await fetchSummary(courseId);
    if (signal?.aborted) return null;
    return res;
  }, [courseId]);

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
              : "Impossible de charger les résumés."
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
        <Loader2 size={24} strokeWidth={1.5} className="animate-spin text-accent" />
        <p className="text-sm text-ink-secondary">Chargement…</p>
      </div>
    );
  }

  if (generating) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Loader2 size={24} strokeWidth={1.5} className="animate-spin text-accent" />
        <p className="text-sm text-ink-secondary">Génération des résumés en cours…</p>
        <p className="text-xs text-ink-muted">
          La première génération peut prendre plusieurs minutes. Cette page se met à jour automatiquement.
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
          <span className="text-xs font-mono text-ink-muted">{String(index + 1).padStart(2, "0")}</span>
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
            <ChevronDown size={16} strokeWidth={1.5} className="text-ink-muted" />
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
              <p className="text-sm text-ink-secondary leading-relaxed">
                {chapter.summary}
              </p>

              {chapter.key_concepts.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {chapter.key_concepts.map((concept, i) => (
                    <span key={i} className="tag">
                      {concept}
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
