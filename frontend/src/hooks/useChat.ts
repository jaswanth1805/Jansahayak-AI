"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  api,
  Language,
  ChatMessage,
  SourceCitation,
  ChatResponse,
} from "@/lib/api";

export interface ExtendedChatMessage extends ChatMessage {
  id?: string;
  sources?: SourceCitation[];
  agent_steps?: string[];
  has_audio?: boolean;
  audio_url?: string;
  suggested_questions?: string[];
  eligibility_data?: Record<string, unknown>;
}

const STORAGE_SESSION_KEY = "jansahayak_chat_session_id";
const STORAGE_MESSAGES_KEY = "jansahayak_chat_messages";

function createSessionId(): string {
  const bytes = new Uint8Array(16);
  window.crypto.getRandomValues(bytes);
  return `sess_${Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}

export function useChat(initialLanguage: Language = "en") {
  const [messages, setMessages] = useState<ExtendedChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [agentSteps, setAgentSteps] = useState<string[]>([]);
  const lastUserPromptRef = useRef<{ text: string; language: Language; documentId?: string; documentAccessToken?: string; userProfile?: Record<string, unknown> } | null>(null);

  // Initialize session ID and restore cached messages if available
  useEffect(() => {
    if (typeof window !== "undefined") {
      let currentSession = localStorage.getItem(STORAGE_SESSION_KEY);
      if (!currentSession || !/^sess_[0-9a-f]{32}$/.test(currentSession)) {
        currentSession = createSessionId();
        localStorage.setItem(STORAGE_SESSION_KEY, currentSession);
      }
      setSessionId(currentSession);

      const cached = localStorage.getItem(STORAGE_MESSAGES_KEY);
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setMessages(parsed.slice(-200));
          }
        } catch (e) {
          console.warn("Failed to parse cached chat messages", e);
        }
      }
    }
  }, []);

  // Save messages to localStorage when updated
  useEffect(() => {
    if (typeof window !== "undefined" && messages.length > 0) {
      try {
        localStorage.setItem(STORAGE_MESSAGES_KEY, JSON.stringify(messages));
      } catch (e) {
        console.warn("Failed to save chat messages to localStorage", e);
      }
    }
  }, [messages]);

  const sendMessage = useCallback(
    async (
      text: string,
      language: Language = initialLanguage,
      userProfile?: Record<string, unknown>,
      documentId?: string,
      documentAccessToken?: string
    ) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;

      setError(null);
      lastUserPromptRef.current = { text: trimmed, language, documentId, documentAccessToken, userProfile };

      const userMessage: ExtendedChatMessage = {
        role: "user",
        content: trimmed,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage].slice(-200));
      setIsLoading(true);
      setAgentSteps([
        "Analyzing request and identifying user intent...",
        "Searching available scheme and policy references...",
      ]);

      try {
        // If documentId is provided, query the document endpoint directly
        if (documentId) {
          setAgentSteps((prev) => [
            ...prev,
            "Searching the uploaded document and collecting page references...",
          ]);
          if (!documentAccessToken) throw new Error("This document is not authorized for querying. Upload it again to continue.");
          const docRes = await api.queryDocument(documentId, documentAccessToken, trimmed, language);

          const assistantMsg: ExtendedChatMessage = {
            role: "assistant",
            content: docRes.answer,
            sources: docRes.sources,
            agent_steps: [
              "Indexed document successfully",
              "Matched user query against document sections",
              "Collected matching passages from the uploaded document",
            ],
            timestamp: new Date().toISOString(),
          };

          setMessages((prev) => [...prev, assistantMsg].slice(-200));
          setAgentSteps([]);
          setIsLoading(false);
          return;
        }

        // Standard chat conversation
        // Filter history to conform to backend ChatMessage schema (role & content)
        const historyForApi: ChatMessage[] = messages.slice(-30).map((m) => ({
          role: m.role,
          content: m.content,
        }));

        setAgentSteps((prev) => [
          ...prev,
          "Querying Government Knowledge Base (myscheme.gov.in & datasets)...",
          "Preparing a response from available evidence and source links...",
        ]);

        const response: ChatResponse = await api.chat(
          trimmed,
          language,
          historyForApi,
          sessionId,
          undefined,
          undefined,
          userProfile
        );

        if (response.session_id && response.session_id !== sessionId) {
          setSessionId(response.session_id);
          if (typeof window !== "undefined") {
            localStorage.setItem(STORAGE_SESSION_KEY, response.session_id);
          }
        }

        const assistantMsg: ExtendedChatMessage = {
          role: "assistant",
          content: response.answer,
          sources: response.sources || [],
          agent_steps: response.agent_steps || [],
          has_audio: response.has_audio || false,
          audio_url: response.audio_url,
          suggested_questions: response.suggested_questions || [],
          eligibility_data: response.eligibility_data,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMsg].slice(-200));
        setAgentSteps([]);
      } catch (err: unknown) {
        console.error("Chat error:", err);
        const errMsg =
          err instanceof Error
            ? err.message
            : "An unexpected error occurred while communicating with JanSahayak AI.";
        setError(errMsg);

        // Add a friendly assistant fallback message so conversation continues gracefully
        const fallbackMsg: ExtendedChatMessage = {
          role: "assistant",
          content: `⚠️ We encountered an issue contacting the JanSahayak AI service: "${errMsg}". \n\nPlease ensure your backend service is running and reachable.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, fallbackMsg].slice(-200));
      } finally {
        setIsLoading(false);
      }
    },
    [initialLanguage, isLoading, messages, sessionId]
  );

  const retryLastMessage = useCallback(async () => {
    if (!lastUserPromptRef.current) return;
      const { text, language, documentId, documentAccessToken, userProfile } = lastUserPromptRef.current;
    // Remove last message if it was the error fallback
    setMessages((prev) => {
      if (prev.length > 0 && prev[prev.length - 1].role === "assistant") {
        return prev.slice(0, prev.length - 1);
      }
      return prev;
    });
    await sendMessage(text, language, userProfile, documentId, documentAccessToken);
  }, [sendMessage]);

  const clearHistory = useCallback(() => {
    if (sessionId) {
      void api.deleteChatSession(sessionId).catch((err) => {
        console.warn("Could not clear server-side chat history", err);
      });
    }
    setMessages([]);
    setError(null);
    setAgentSteps([]);
    if (typeof window !== "undefined") {
      localStorage.removeItem(STORAGE_MESSAGES_KEY);
      const newSession = createSessionId();
      localStorage.setItem(STORAGE_SESSION_KEY, newSession);
      setSessionId(newSession);
    }
  }, [sessionId]);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    agentSteps,
    sendMessage,
    clearHistory,
    retryLastMessage,
  };
}
