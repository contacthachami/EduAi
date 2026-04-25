"use client";

import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  Check,
  Copy,
  Lightbulb,
  Loader2,
  MessageSquareText,
  RefreshCw,
  RotateCcw,
  Send,
  Square,
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
  "Résumez ce cours en cinq points clés",
  "Quels sont les concepts essentiels à maîtriser ?",
  "Donnez un exemple concret tiré du document",
  "Expliquez ce chapitre comme à un débutant",
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
  const isStreaming = messages.some((message) => message.isStreaming);

  useEffect(() => {
    const textarea = inputRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }, [input]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const element = scrollRef.current;
    if (!element) return;
    element.scrollTo({
      top: element.scrollHeight,
      behavior: isStreaming ? "auto" : "smooth",
    });
  }, [messages, isStreaming]);

  const handleSend = useCallback(
    (text?: string) => {
      const question = (text ?? input).trim();
      if (!question || isLoading) return;
      sendMessage(question);
      setInput("");
      if (inputRef.current) inputRef.current.style.height = "auto";
      inputRef.current?.focus();
    },
    [input, isLoading, sendMessage],
  );

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-full flex-col bg-bg-card">
      <div className="flex flex-col gap-3 border-b border-border bg-bg-subtle px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
        <div className="min-w-0">
          <p className="eyebrow">Questions</p>
          <p className="mt-1 truncate text-sm text-ink-secondary">
            Posez une question sur « {courseName} »
          </p>
        </div>
        {messages.length > 0 && (
          <button type="button" onClick={clearMessages} className="btn-secondary">
            <RotateCcw size={15} strokeWidth={1.8} />
            Nouvelle conversation
          </button>
        )}
      </div>

      <div
        ref={scrollRef}
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        className="flex-1 overflow-y-auto px-4 py-5 sm:px-5"
      >
        {messages.length === 0 ? (
          <EmptyState courseName={courseName} onPick={(question) => handleSend(question)} />
        ) : (
          <div className="space-y-5">
            {messages.map((message, index) => (
              <MessageBubble
                key={message.id}
                message={message}
                index={index}
                onRetry={retry}
                canRetry={!isLoading}
              />
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-border bg-bg-subtle px-4 py-4 sm:px-5">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Votre question..."
            rows={1}
            aria-label="Votre question sur le cours"
            className="field min-h-11 flex-1 resize-none"
            style={{ maxHeight: "160px" }}
            disabled={isLoading}
          />
          {isLoading ? (
            <button
              type="button"
              onClick={stop}
              className="btn-primary min-h-11 px-3.5 bg-error hover:bg-error"
              aria-label="Arrêter la génération"
              title="Arrêter"
            >
              <Square size={16} strokeWidth={2} fill="currentColor" />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => handleSend()}
              disabled={!input.trim()}
              className="btn-primary min-h-11 px-3.5"
              aria-label="Envoyer la question"
              title="Envoyer"
            >
              <Send size={17} strokeWidth={1.8} />
            </button>
          )}
        </div>
        <p className="mt-2 text-right text-[11px] text-ink-muted">
          Entrée pour envoyer, Maj + Entrée pour une nouvelle ligne
        </p>
      </div>
    </div>
  );
}

function EmptyState({
  courseName,
  onPick,
}: {
  courseName: string;
  onPick: (question: string) => void;
}) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center justify-center py-10 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-card border border-border bg-bg-subtle text-accent">
        <MessageSquareText size={22} strokeWidth={1.8} />
      </div>
      <h2 className="mt-4 text-lg font-semibold text-ink-primary">
        Interrogez votre cours
      </h2>
      <p className="mt-2 max-w-lg text-sm text-ink-secondary">
        Les réponses s&apos;appuient sur le contenu du PDF « {courseName} ». Posez
        une question précise ou utilisez une suggestion pour commencer.
      </p>

      <div className="mt-7 w-full max-w-xl">
        <div className="mb-2 flex items-center gap-2 text-left text-xs font-medium uppercase text-ink-muted">
          <Lightbulb size={14} strokeWidth={1.8} />
          Suggestions
        </div>
        <div className="grid gap-2">
          {SUGGESTED_QUESTIONS.map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => onPick(question)}
              className="rounded-card border border-border bg-bg-card px-3.5 py-3 text-left text-sm text-ink-secondary transition duration-200 hover:border-accent hover:bg-accent-soft hover:text-ink-primary"
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

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
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard can be unavailable in restricted browsers.
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut", delay: index * 0.015 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <article
        className={`max-w-[88%] rounded-panel border px-4 py-3 text-sm shadow-sm ${
          isUser
            ? "border-accent/20 bg-accent-soft text-ink-primary"
            : "border-border bg-bg-subtle text-ink-primary"
        }`}
      >
        {!isUser && (
          <p className="mb-2 font-mono text-[11px] font-medium uppercase text-accent">
            EduAI
          </p>
        )}

        {message.error ? (
          <div className="space-y-3">
            <div className="flex items-start gap-2 text-error">
              <AlertCircle size={16} strokeWidth={1.8} className="mt-0.5 shrink-0" />
              <span>{message.error}</span>
            </div>
            <button
              type="button"
              onClick={onRetry}
              disabled={!canRetry}
              className="btn-secondary min-h-9 px-3 py-1.5 text-xs"
            >
              <RefreshCw size={13} strokeWidth={1.8} />
              Réessayer
            </button>
          </div>
        ) : message.isLoading ? (
          <div className="flex items-center gap-2 text-ink-secondary" role="status">
            <Loader2 size={15} strokeWidth={1.8} className="animate-spin text-accent" />
            <span>Recherche dans le cours...</span>
          </div>
        ) : (
          <>
            <div className="prose-chat">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => (
                    <p className="my-2 first:mt-0 last:mb-0 whitespace-pre-wrap">
                      {children}
                    </p>
                  ),
                  h1: ({ children }) => (
                    <h3 className="mt-4 text-base font-semibold text-ink-primary first:mt-0">
                      {children}
                    </h3>
                  ),
                  h2: ({ children }) => (
                    <h3 className="mt-4 text-base font-semibold text-ink-primary first:mt-0">
                      {children}
                    </h3>
                  ),
                  h3: ({ children }) => (
                    <h4 className="mt-3 text-sm font-semibold text-ink-primary first:mt-0">
                      {children}
                    </h4>
                  ),
                  ul: ({ children }) => (
                    <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="my-3 border-l-2 border-accent bg-bg-card py-2 pl-3 text-ink-secondary">
                      {children}
                    </blockquote>
                  ),
                  code: ({ children }) => (
                    <code className="rounded bg-bg-card px-1 py-0.5 font-mono text-xs">
                      {children}
                    </code>
                  ),
                  table: ({ children }) => (
                    <div className="my-3 overflow-x-auto">
                      <table className="w-full border-collapse border border-border text-xs">
                        {children}
                      </table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border border-border bg-bg-card px-2 py-1 text-left font-semibold">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="border border-border px-2 py-1">{children}</td>
                  ),
                }}
              >
                {message.content || ""}
              </ReactMarkdown>
              {message.isStreaming && (
                <span className="ml-1 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-accent align-middle" />
              )}
            </div>

            {!isUser && !message.isStreaming && message.content && (
              <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border/70 pt-2">
                {message.confidence !== undefined && message.confidence > 0 && (
                  <span className="caption">
                    Pertinence : {Math.round(message.confidence * 100)}%
                  </span>
                )}
                <button
                  type="button"
                  onClick={handleCopy}
                  className="ml-auto inline-flex min-h-8 items-center gap-1.5 rounded-card px-2 text-xs text-ink-muted transition hover:bg-bg-card hover:text-accent"
                  title="Copier la réponse"
                >
                  {copied ? (
                    <>
                      <Check size={13} strokeWidth={1.8} />
                      Copié
                    </>
                  ) : (
                    <>
                      <Copy size={13} strokeWidth={1.8} />
                      Copier
                    </>
                  )}
                </button>
              </div>
            )}

            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 space-y-2 border-t border-border/70 pt-3">
                <p className="caption font-medium uppercase">Sources utilisées</p>
                {message.sources.map((source, sourceIndex) => (
                  <SourceCard key={sourceIndex} source={source} index={sourceIndex} />
                ))}
              </div>
            )}
          </>
        )}
      </article>
    </motion.div>
  );
}
