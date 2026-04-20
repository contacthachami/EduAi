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
import { Send, RotateCcw } from "lucide-react";
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
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>

            {/* Confiance */}
            {message.confidence !== undefined && message.confidence > 0 && (
              <p className="text-xs text-ink-muted mt-2">
                Confiance : {Math.round(message.confidence * 100)}%
              </p>
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
