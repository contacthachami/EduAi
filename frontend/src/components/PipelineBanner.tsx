"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, GitBranch, Layers } from "lucide-react";
import type { PipelineMeta, PipelineStep } from "@/lib/api";

interface PipelineBannerProps {
  meta: PipelineMeta;
}

const FAMILY_LABELS: Record<PipelineStep["family"], string> = {
  NLP: "NLP",
  "Deep Learning": "Apprentissage",
  LLM: "Reformulation",
};

export default function PipelineBanner({ meta }: PipelineBannerProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mb-5 rounded-panel border border-border bg-bg-subtle">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
        aria-expanded={open}
      >
        <span className="flex min-w-0 items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-card bg-bg-card text-accent">
            <GitBranch size={17} strokeWidth={1.8} />
          </span>
          <span className="min-w-0">
            <span className="block text-sm font-semibold text-ink-primary">
              Méthode de synthèse
            </span>
            <span className="block truncate text-xs text-ink-secondary">
              Extraction, regroupement des passages et reformulation pédagogique.
            </span>
          </span>
        </span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.18 }}
          className="shrink-0 text-ink-muted"
        >
          <ChevronDown size={18} strokeWidth={1.8} />
        </motion.span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className="overflow-hidden border-t border-border"
          >
            <ol className="divide-y divide-border">
              {meta.steps.map((step, index) => (
                <li key={`${step.name}-${index}`} className="flex gap-3 px-4 py-3">
                  <span className="mt-0.5 font-mono text-xs text-ink-muted">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-semibold text-ink-primary">
                        {step.name}
                      </h3>
                      <span className="rounded-card border border-border bg-bg-card px-2 py-0.5 text-[11px] font-medium text-ink-secondary">
                        {FAMILY_LABELS[step.family]}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-ink-secondary">{step.detail}</p>
                    <p className="mt-1 inline-flex items-center gap-1 font-mono text-[11px] text-ink-muted">
                      <Layers size={12} strokeWidth={1.8} />
                      {step.model}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
