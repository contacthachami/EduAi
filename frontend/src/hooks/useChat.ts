/**
 * Hook de gestion du chat Q&A.
 * Utilise le streaming SSE pour un effet "ChatGPT".
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
}

export function useChat(courseId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string | undefined>(undefined);
  const abortRef = useRef<(() => void) | null>(null);

  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || isLoading) return;

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
                m.id === assistantId
                  ? { ...m, sources, confidence, isLoading: false }
                  : m,
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
                      content: `Erreur : ${err.message}`,
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
    [courseId, isLoading],
  );

  const clearMessages = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = null;
    }
    setMessages([]);
    sessionIdRef.current = undefined;
    setIsLoading(false);
  }, []);

  return { messages, isLoading, sendMessage, clearMessages };
}
