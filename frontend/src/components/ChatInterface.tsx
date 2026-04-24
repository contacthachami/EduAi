/**
 * ChatInterface — Interface de chat Q&A.
 *
 * Messages utilisateur à droite (fond accent-light).
 * Réponses IA à gauche (fond bg-secondary).
 * Sources en footnotes académiques sous chaque réponse.
 * Curseur clignotant pendant la génération.
 */
"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Send, RotateCcw, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useChat, type ChatMessage } from "@/hooks/useChat";
import SourceCard from "./SourceCard";

interface ChatInterfaceProps {
  courseId: string;
  courseName: string;
}

export default function ChatInterface({
  courseId,
  courseName,
}: ChatInterfaceProps) {
  const { messages, isLoading, sendMessage, clearMessages } = useChat(courseId);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage(input.trim());
    setInput("");
    inputRef.current?.focus();
  };

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
          <div className="text-center py-16">
            <p className="text-sm text-ink-muted">
              Posez votre première question sur le contenu du cours.
            </p>
            <p className="text-xs text-ink-muted mt-1">
              Les réponses sont basées uniquement sur le PDF uploadé.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={msg.id} message={msg} index={i} />
        ))}
      </div>

      {/* Zone de saisie */}
      <div className="border-t border-border px-5 py-3">
        <div className="flex items-end gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Votre question…"
            rows={1}
            disabled={isLoading}
            className="flex-1 resize-none px-4 py-2.5 text-sm border border-border rounded-card
                       bg-bg-card text-ink-primary placeholder-ink-muted
                       focus:outline-none focus:border-accent transition-colors
                       disabled:opacity-50"
            style={{ maxHeight: "120px" }}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="btn-primary px-3 py-2.5 disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
            aria-label="Envoyer"
          >
            <Send size={16} strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({
  message,
  index,
}: {
  message: ChatMessage;
  index: number;
}) {
  const isUser = message.role === "user";

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

        {message.isLoading ? (
          <span className="typing-cursor text-sm text-ink-secondary">
            Recherche en cours
          </span>
        ) : (
          <>
            <div className="text-sm leading-relaxed">
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <p className="my-1.5 first:mt-0 last:mb-0 whitespace-pre-wrap">
                      {children}
                    </p>
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
                }}
              >
                {message.content || ""}
              </ReactMarkdown>
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 bg-accent ml-0.5 animate-pulse align-middle" />
              )}
            </div>

            {/* Badge IA + Confiance */}
            {(message.llmUsed !== undefined ||
              message.confidence !== undefined) &&
              !message.isStreaming && (
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  {message.llmUsed && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-accent bg-accent-light/40 px-1.5 py-0.5 rounded">
                      <Sparkles size={10} strokeWidth={2} />
                      Généré par IA locale
                    </span>
                  )}
                  {message.confidence !== undefined &&
                    message.confidence > 0 && (
                      <span className="text-xs text-ink-muted">
                        Confiance : {Math.round(message.confidence * 100)}%
                      </span>
                    )}
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
