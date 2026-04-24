/**
 * ChatInterface — Interface de chat Q&A.
 *
 * Messages utilisateur à droite (fond accent-light).
 * Réponses IA à gauche (fond bg-secondary).
 * Sources en footnotes académiques sous chaque réponse.
 * Curseur clignotant pendant la génération.
 *
 * UX :
 *  - Empty state avec questions suggérées cliquables
 *  - Textarea auto-resize
 *  - Bouton Stop pendant la génération
 *  - Bouton Copier sur chaque réponse
 *  - Bouton Réessayer en cas d'erreur
 *  - Indicateur "EduAI réfléchit…" tant qu'aucun token n'est arrivé
 *  - Scroll instantané pendant le streaming, smooth après
 *  - Focus auto sur l'input à l'ouverture
 *  - Hint clavier (Shift+Enter)
 */
"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Send,
  RotateCcw,
  Sparkles,
  Square,
  Copy,
  Check,
  AlertCircle,
  RefreshCw,
  Lightbulb,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChat, type ChatMessage } from "@/hooks/useChat";
import SourceCard from "./SourceCard";

interface ChatInterfaceProps {
  courseId: string;
  courseName: string;
}

const SUGGESTED_QUESTIONS = [
  "Résume ce cours en 5 points clés",
  "Quels sont les concepts principaux abordés ?",
  "Donne-moi un exemple concret tiré du cours",
  "Explique le point le plus important comme à un débutant",
];

export default function ChatInterface({
  courseId,
  courseName,
}: ChatInterfaceProps) {
  const { messages, isLoading, sendMessage, stop, retry, clearMessages } =
    useChat(courseId);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const isStreaming = messages.some((m) => m.isStreaming);

  // Auto-resize de la textarea (max 160px)
  useEffect(() => {
    const ta = inputRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [input]);

  // Focus auto à l'ouverture
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Scroll : instantané pendant le streaming (évite le saccade), smooth sinon
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({
      top: el.scrollHeight,
      behavior: isStreaming ? "auto" : "smooth",
    });
  }, [messages, isStreaming]);

  const handleSend = useCallback(
    (text?: string) => {
      const q = (text ?? input).trim();
      if (!q || isLoading) return;
      sendMessage(q);
      setInput("");
      // Reset hauteur textarea
      if (inputRef.current) inputRef.current.style.height = "auto";
      inputRef.current?.focus();
    },
    [input, isLoading, sendMessage],
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* En-tête */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-accent font-medium">
            EduAI
          </span>
          <p className="text-xs text-ink-muted mt-0.5">
            Posez une question sur « {courseName} »
          </p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="btn-ghost flex items-center gap-1.5 text-xs"
            title="Nouvelle conversation"
          >
            <RotateCcw size={14} strokeWidth={1.5} />
            Effacer
          </button>
        )}
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-5 py-4 space-y-4"
      >
        {messages.length === 0 && (
          <EmptyState courseName={courseName} onPick={(q) => handleSend(q)} />
        )}

        {messages.map((msg, i) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            index={i}
            onRetry={retry}
            canRetry={!isLoading}
          />
        ))}
      </div>

      {/* Zone de saisie */}
      <div className="border-t border-border px-5 py-3">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Votre question…"
            rows={1}
            className="flex-1 resize-none px-4 py-2.5 text-sm border border-border rounded-card
                       bg-bg-card text-ink-primary placeholder-ink-muted
                       focus:outline-none focus:border-accent transition-colors"
            style={{ maxHeight: "160px" }}
          />
          {isLoading ? (
            <button
              onClick={stop}
              className="btn-primary px-3 py-2.5 flex-shrink-0 bg-red-500 hover:bg-red-600"
              aria-label="Arrêter la génération"
              title="Arrêter"
            >
              <Square size={16} strokeWidth={2} fill="currentColor" />
            </button>
          ) : (
            <button
              onClick={() => handleSend()}
              disabled={!input.trim()}
              className="btn-primary px-3 py-2.5 disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
              aria-label="Envoyer"
              title="Envoyer (Entrée)"
            >
              <Send size={16} strokeWidth={1.5} />
            </button>
          )}
        </div>
        <p className="text-[10px] text-ink-muted mt-1.5 text-right select-none">
          Entrée pour envoyer · Shift+Entrée pour nouvelle ligne
        </p>
      </div>
    </div>
  );
}

// ── Empty state avec suggestions ───────────────────

function EmptyState({
  courseName,
  onPick,
}: {
  courseName: string;
  onPick: (q: string) => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="w-12 h-12 rounded-full bg-accent-light/40 flex items-center justify-center mb-4">
        <Sparkles size={20} strokeWidth={1.5} className="text-accent" />
      </div>
      <p className="text-sm text-ink-primary font-medium text-center">
        Discute avec EduAI à propos de « {courseName} »
      </p>
      <p className="text-xs text-ink-muted mt-1 text-center max-w-md">
        Les réponses sont basées uniquement sur le contenu du PDF que tu as
        uploadé.
      </p>

      <div className="mt-6 w-full max-w-lg space-y-2">
        <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-ink-muted mb-1">
          <Lightbulb size={11} strokeWidth={1.5} />
          Suggestions
        </div>
        {SUGGESTED_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onPick(q)}
            className="w-full text-left px-3 py-2 text-sm text-ink-secondary
                       border border-border rounded-card bg-bg-card
                       hover:border-accent hover:text-ink-primary hover:bg-accent-light/20
                       transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Bulle de message ───────────────────────────────

function MessageBubble({
  message,
  index,
  onRetry,
  canRetry,
}: {
  message: ChatMessage;
  index: number;
  onRetry: () => void;
  canRetry: boolean;
}) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // ignore (navigateur sans support clipboard)
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut", delay: index * 0.02 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[85%] ${
          isUser
            ? "bg-accent-light text-ink-primary rounded-card px-4 py-3"
            : "bg-bg-secondary text-ink-primary rounded-card px-4 py-3"
        }`}
      >
        {!isUser && (
          <span className="text-[10px] font-mono uppercase tracking-widest text-accent font-medium block mb-1">
            EduAI
          </span>
        )}

        {/* État ERREUR */}
        {message.error ? (
          <div className="space-y-2">
            <div className="flex items-start gap-2 text-sm text-red-600">
              <AlertCircle
                size={14}
                strokeWidth={1.5}
                className="mt-0.5 flex-shrink-0"
              />
              <span>{message.error}</span>
            </div>
            <button
              onClick={onRetry}
              disabled={!canRetry}
              className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded
                         border border-border hover:border-accent hover:text-accent
                         transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <RefreshCw size={12} strokeWidth={1.5} />
              Réessayer
            </button>
          </div>
        ) : message.isLoading ? (
          /* État CHARGEMENT (avant 1er token) */
          <div className="flex items-center gap-2 text-sm text-ink-secondary">
            <ThinkingDots />
            <span>EduAI réfléchit…</span>
          </div>
        ) : (
          <>
            <div className="text-sm leading-relaxed">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => (
                    <p className="my-1.5 first:mt-0 last:mb-0 whitespace-pre-wrap">
                      {children}
                    </p>
                  ),
                  h1: ({ children }) => (
                    <h3 className="font-display text-base font-semibold text-ink-primary mt-3 mb-1.5 first:mt-0">
                      {children}
                    </h3>
                  ),
                  h2: ({ children }) => (
                    <h3 className="font-display text-base font-semibold text-ink-primary mt-3 mb-1.5 first:mt-0">
                      {children}
                    </h3>
                  ),
                  h3: ({ children }) => (
                    <h3 className="font-display text-sm font-semibold text-ink-primary mt-3 mb-1 first:mt-0 flex items-center gap-1.5">
                      {children}
                    </h3>
                  ),
                  h4: ({ children }) => (
                    <h4 className="font-display text-sm font-semibold text-ink-primary mt-2 mb-1 first:mt-0">
                      {children}
                    </h4>
                  ),
                  ul: ({ children }) => (
                    <ul className="my-2 space-y-1 list-none">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="my-2 space-y-1 list-decimal list-inside">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="flex gap-2">
                      <span className="text-accent shrink-0">•</span>
                      <span>{children}</span>
                    </li>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="my-2 pl-3 border-l-2 border-accent bg-accent-light/30 py-2 px-3 rounded-r text-ink-primary italic">
                      {children}
                    </blockquote>
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
                  table: ({ children }) => (
                    <div className="my-3 overflow-x-auto">
                      <table className="text-xs border-collapse border border-border w-full">
                        {children}
                      </table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border border-border px-2 py-1 bg-bg-secondary text-left font-semibold">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="border border-border px-2 py-1">
                      {children}
                    </td>
                  ),
                  hr: () => <hr className="my-3 border-border" />,
                }}
              >
                {message.content || ""}
              </ReactMarkdown>
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 bg-accent ml-0.5 animate-pulse align-middle" />
              )}
            </div>

            {/* Badge IA + Confiance + Copier (assistant uniquement, hors streaming) */}
            {!isUser && !message.isStreaming && message.content && (
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                {message.llmUsed && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-accent bg-accent-light/40 px-1.5 py-0.5 rounded">
                    <Sparkles size={10} strokeWidth={2} />
                    Généré par IA
                  </span>
                )}
                {message.confidence !== undefined && message.confidence > 0 && (
                  <span className="text-xs text-ink-muted">
                    Confiance : {Math.round(message.confidence * 100)}%
                  </span>
                )}
                <button
                  onClick={handleCopy}
                  className="ml-auto inline-flex items-center gap-1 text-[11px] text-ink-muted hover:text-accent transition-colors"
                  title="Copier la réponse"
                >
                  {copied ? (
                    <>
                      <Check size={11} strokeWidth={2} />
                      Copié
                    </>
                  ) : (
                    <>
                      <Copy size={11} strokeWidth={1.5} />
                      Copier
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Sources en footnotes */}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-2 border-t border-border/50 space-y-1">
                {message.sources.map((src, i) => (
                  <SourceCard key={i} source={src} index={i} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}

// ── Petits "dots" animés ───────────────────────────

function ThinkingDots() {
  return (
    <span className="inline-flex gap-1">
      <span
        className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce"
        style={{ animationDelay: "0ms" }}
      />
      <span
        className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce"
        style={{ animationDelay: "150ms" }}
      />
      <span
        className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce"
        style={{ animationDelay: "300ms" }}
      />
    </span>
  );
}
