/**
 * Hook de gestion du chat Q&A.
 * Gère les messages, le streaming, et le session_id.
 */
"use client";

import { useState, useCallback, useRef } from "react";
import { askQuestion, type AnswerResponse, type SourceDocument } from "@/lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDocument[];
  confidence?: number;
  timestamp: Date;
  isLoading?: boolean;
}

export function useChat(courseId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const sessionIdRef = useRef<string | undefined>(undefined);

  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || isLoading) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: question,
        timestamp: new Date(),
      };

      const loadingMsg: ChatMessage = {
        id: `loading-${Date.now()}`,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isLoading: true,
      };

      setMessages((prev) => [...prev, userMsg, loadingMsg]);
      setIsLoading(true);

      try {
        const response: AnswerResponse = await askQuestion(
          courseId,
          question,
          sessionIdRef.current
        );

        sessionIdRef.current = response.session_id;

        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          confidence: response.confidence,
          timestamp: new Date(),
        };

        setMessages((prev) =>
          prev.filter((m) => !m.isLoading).concat(assistantMsg)
        );
      } catch (err: unknown) {
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content:
            err instanceof Error
              ? `Erreur : ${err.message}`
              : "Une erreur est survenue. Veuillez réessayer.",
          timestamp: new Date(),
        };
        setMessages((prev) =>
          prev.filter((m) => !m.isLoading).concat(errorMsg)
        );
      } finally {
        setIsLoading(false);
      }
    },
    [courseId, isLoading]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    sessionIdRef.current = undefined;
  }, []);

  return { messages, isLoading, sendMessage, clearMessages };
}
