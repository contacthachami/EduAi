/**
 * SourceCard — Carte de référence académique (style footnote).
 */
"use client";

import { BookOpen } from "lucide-react";
import type { SourceDocument } from "@/lib/api";

interface SourceCardProps {
  source: SourceDocument;
  index: number;
}

export default function SourceCard({ source, index }: SourceCardProps) {
  const confidence = Math.round(source.similarity_score * 100);

  return (
    <div className="flex items-start gap-2 py-1.5">
      <span className="footnote mt-0.5 select-none">
        <sup>{index + 1}</sup>
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <BookOpen
            size={12}
            strokeWidth={1.5}
            className="text-ink-muted flex-shrink-0"
          />
          <span className="text-xs font-medium text-ink-secondary">
            Page {source.page}
            {source.chapter && ` — ${source.chapter}`}
          </span>
          <span className="text-xs text-ink-muted ml-auto">{confidence}%</span>
        </div>
        <p className="text-xs text-ink-muted mt-0.5 line-clamp-2 leading-relaxed">
          {source.chunk_text}
        </p>
      </div>
    </div>
  );
}
