/**
 * PipelineBanner — Affiche le pipeline NLP / Deep Learning / LLM utilisé par EduAI.
 *
 * Objectif pédagogique : montrer à l'utilisateur (et au jury) que le résumé
 * n'est pas un simple appel à un LLM externe, mais le résultat d'un véritable
 * pipeline combinant NLP classique, modèles de Deep Learning (BERT, FAISS)
 * et LLM en étape finale uniquement.
 */
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Cpu, Brain, Sparkles, Layers } from "lucide-react";
import type { PipelineMeta, PipelineStep } from "@/lib/api";

interface PipelineBannerProps {
  meta: PipelineMeta;
}

const FAMILY_STYLES: Record<
  PipelineStep["family"],
  { bg: string; text: string; ring: string; icon: typeof Brain }
> = {
  NLP: {
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    ring: "ring-emerald-200",
    icon: Layers,
  },
  "Deep Learning": {
    bg: "bg-indigo-50",
    text: "text-indigo-700",
    ring: "ring-indigo-200",
    icon: Brain,
  },
  LLM: {
    bg: "bg-amber-50",
    text: "text-amber-700",
    ring: "ring-amber-200",
    icon: Sparkles,
  },
};

export default function PipelineBanner({ meta }: PipelineBannerProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mb-5 rounded-lg border border-border bg-bg-secondary/40 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-3 px-4 py-2.5 text-left
                   hover:bg-bg-secondary/70 transition-colors"
        aria-expanded={open ? "true" : "false"}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <Cpu size={14} strokeWidth={1.75} className="text-accent shrink-0" />
          <span className="text-xs font-mono uppercase tracking-wider text-ink-secondary shrink-0">
            Pipeline
          </span>
          <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
            {meta.steps.map((step, i) => (
              <div key={i} className="flex items-center gap-1 shrink-0">
                <span
                  className={`text-[10px] font-medium px-1.5 py-0.5 rounded ring-1 ${FAMILY_STYLES[step.family].bg} ${FAMILY_STYLES[step.family].text} ${FAMILY_STYLES[step.family].ring}`}
                  title={step.detail}
                >
                  {step.name}
                </span>
                {i < meta.steps.length - 1 && (
                  <span className="text-ink-muted text-[10px]">→</span>
                )}
              </div>
            ))}
          </div>
        </div>
        <motion.div
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="shrink-0"
        >
          <ChevronDown size={14} strokeWidth={1.5} className="text-ink-muted" />
        </motion.div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden border-t border-border"
          >
            <ol className="divide-y divide-border/60">
              {meta.steps.map((step, i) => {
                const style = FAMILY_STYLES[step.family];
                const Icon = style.icon;
                return (
                  <li key={i} className="flex items-start gap-3 px-4 py-3">
                    <div
                      className={`flex items-center justify-center w-7 h-7 rounded-md shrink-0 ${style.bg} ${style.text}`}
                    >
                      <Icon size={14} strokeWidth={1.75} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline gap-2 flex-wrap">
                        <span className="text-xs font-mono text-ink-muted">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <h4 className="text-sm font-semibold text-ink-primary">
                          {step.name}
                        </h4>
                        <span
                          className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${style.bg} ${style.text}`}
                        >
                          {step.family}
                        </span>
                      </div>
                      <p className="text-xs text-ink-secondary mt-0.5">
                        {step.detail}
                      </p>
                      <p className="text-[11px] font-mono text-ink-muted mt-1">
                        {step.model}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
            <div className="px-4 py-2 bg-bg-secondary/60 border-t border-border text-[11px] text-ink-muted">
              Le LLM intervient uniquement à l'étape finale pour reformuler de
              façon pédagogique le résumé déjà produit par le pipeline NLP /
              Deep Learning.
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
