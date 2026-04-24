/**
 * Hook de gestion du chat Q&A.
 * Utilise le streaming SSE pour un effet "ChatGPT".
 *
 * Fonctions exposées :
 *  - sendMessage(question)  : envoie une question
 *  - stop()                 : interrompt la génération en cours
 *  - retry()                : ré-envoie la dernière question (utile en cas d'erreur)
 *  - clearMessages()        : efface l'historique et la session
 */
"use client";

import { useState, useCallback, useRef } from "react";
import { askQuestionStream, type SourceDocument } from "@/lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDocument[];
  confidence?: number;
  timestamp: Date;
  isLoading?: boolean;
  isStreaming?: boolean;
  llmUsed?: boolean;
  /** Si défini, le message est en état d'erreur (à afficher en rouge + bouton réessayer). */
  error?: string;
}

export function useChat(courseId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string | undefined>(undefined);
  const abortRef = useRef<(() => void) | null>(null);
  const lastQuestionRef = useRef<string | null>(null);

  const sendInternal = useCallback(
    (question: string) => {
      lastQuestionRef.current = question;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: question,
        timestamp: new Date(),
      };

      const assistantId = `assistant-${Date.now()}`;
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isLoading: true,
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsLoading(true);

      abortRef.current = askQuestionStream(
        courseId,
        question,
        sessionIdRef.current,
        {
          onSources: ({ sources, session_id, confidence }) => {
            sessionIdRef.current = session_id;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, sources, confidence } : m,
              ),
            );
          },
          onToken: (text) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + text, isLoading: false }
                  : m,
              ),
            );
          },
          onDone: ({ llm_used }) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      isStreaming: false,
                      isLoading: false,
                      llmUsed: llm_used,
                    }
                  : m,
              ),
            );
            setIsLoading(false);
            abortRef.current = null;
          },
          onError: (err) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: "",
                      error:
                        err.message ||
                        "Connexion interrompue. Réessaie dans un instant.",
                      isLoading: false,
                      isStreaming: false,
                    }
                  : m,
              ),
            );
            setIsLoading(false);
            abortRef.current = null;
          },
        },
      );
    },
    [courseId],
  );

  const sendMessage = useCallback(
    (question: string) => {
      const q = question.trim();
      if (!q || isLoading) return;
      sendInternal(q);
    },
    [isLoading, sendInternal],
  );

  /** Interrompt proprement la génération en cours. */
  const stop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
    // Marque le dernier message assistant comme arrêté (plus de streaming, plus de loading)
    setMessages((prev) => {
      if (prev.length === 0) return prev;
      const last = prev[prev.length - 1];
      if (last.role !== "assistant" || (!last.isStreaming && !last.isLoading)) {
        return prev;
      }
      return prev.map((m, i) =>
        i === prev.length - 1
          ? {
              ...m,
              isStreaming: false,
              isLoading: false,
              content: m.content || "_(génération interrompue)_",
            }
          : m,
      );
    });
    setIsLoading(false);
  }, []);

  /** Ré-envoie la dernière question (supprime le dernier échange en erreur). */
  const retry = useCallback(() => {
    const q = lastQuestionRef.current;
    if (!q || isLoading) return;
    // Retire le dernier user + assistant (échange en erreur)
    setMessages((prev) => {
      const next = [...prev];
      // Si le dernier est l'assistant en erreur → on retire les 2 derniers
      if (next.length >= 2 && next[next.length - 1].role === "assistant") {
        next.pop();
        if (next[next.length - 1]?.role === "user") next.pop();
      }
      return next;
    });
    sendInternal(q);
  }, [isLoading, sendInternal]);

  const clearMessages = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
    setMessages([]);
    sessionIdRef.current = undefined;
    lastQuestionRef.current = null;
    setIsLoading(false);
  }, []);

  return { messages, isLoading, sendMessage, stop, retry, clearMessages };
}
