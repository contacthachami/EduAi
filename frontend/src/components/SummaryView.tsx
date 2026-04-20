/**
 * SummaryView — Résumés par chapitre en accordéon.
 *
 * Style éditorial : lignes de séparation fines, pas d'ombres sur chaque item.
 * Concepts clés : tags avec fond accent-light.
 */
"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Loader2 } from "lucide-react";
import { fetchSummary, type ChapterSummary } from "@/lib/api";

interface SummaryViewProps {
  courseId: string;
}

export default function SummaryView({ courseId }: SummaryViewProps) {
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchSummary(courseId)
      .then((res) => {
        if (!cancelled) setChapters(res.chapters);
      })
      .catch((err) => {
        if (!cancelled)
          setError(
            err instanceof Error
              ? err.message
              : "Impossible de charger les résumés."
          );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [courseId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 gap-2 text-sm text-ink-secondary">
        <Loader2 size={16} strokeWidth={1.5} className="animate-spin text-accent" />
        Génération des résumés…
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
