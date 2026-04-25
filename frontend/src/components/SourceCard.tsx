"use client";

import { BookOpenText } from "lucide-react";
import type { SourceDocument } from "@/lib/api";

interface SourceCardProps {
  source: SourceDocument;
  index: number;
}

export default function SourceCard({ source, index }: SourceCardProps) {
  const relevance = Math.round(source.similarity_score * 100);

  return (
    <div className="rounded-card border border-border bg-bg-card px-3 py-2">
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] text-ink-muted">
          {String(index + 1).padStart(2, "0")}
        </span>
        <BookOpenText size={13} strokeWidth={1.8} className="text-accent" />
        <span className="min-w-0 flex-1 truncate text-xs font-medium text-ink-secondary">
          Page {source.page}
          {source.chapter ? ` - ${source.chapter}` : ""}
        </span>
        <span className="caption">{relevance}%</span>
      </div>
      <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-ink-muted">
        {source.chunk_text}
      </p>
    </div>
  );
}
