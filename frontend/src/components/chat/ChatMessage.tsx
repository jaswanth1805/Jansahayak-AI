"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ExtendedChatMessage } from "@/hooks/useChat";
import { AgentSteps } from "@/components/ui/AgentSteps";
import { SourceCitationList } from "@/components/ui/SourceCitation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Copy,
  Check,
  Volume2,
  VolumeX,
  Bot,
  User,
  Sparkles,
  ExternalLink,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  message: ExtendedChatMessage;
  onSelectSuggestion?: (suggestion: string) => void;
  onPlayAudio?: (url: string) => void;
  isPlayingAudio?: boolean;
}

export function ChatMessage({
  message,
  onSelectSuggestion,
  onPlayAudio,
  isPlayingAudio = false,
}: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div
      className={cn(
        "flex w-full gap-3 py-3 px-1 transition-all",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {/* Bot Avatar */}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full bg-navy-700 text-white shadow-sm mt-1">
          <Bot className="h-4 w-4" />
        </div>
      )}

      {/* Message Body */}
      <div
        className={cn(
          "flex flex-col space-y-2 max-w-[85%] md:max-w-[75%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm shadow-sm relative group",
            isUser
              ? "bg-navy-700 text-white rounded-tr-xs"
              : "bg-white border border-slate-200 text-slate-900 rounded-tl-xs shadow-xs"
          )}
        >
          {/* Top meta row */}
          <div className="flex items-center justify-between gap-4 mb-1 text-[11px] opacity-75">
            <span className="font-semibold">
              {isUser ? "You" : "JanSahayak AI"}
            </span>
            <div className="flex items-center gap-2">
              {formattedTime && <span>{formattedTime}</span>}
              <button
                onClick={handleCopy}
                className="opacity-0 group-hover:opacity-100 transition p-0.5 hover:bg-black/10 rounded"
                title="Copy response"
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5 text-emerald-500" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
              </button>
            </div>
          </div>

          {/* Reasoning Steps if present */}
          {!isUser && message.agent_steps && message.agent_steps.length > 0 && (
            <div className="mb-3">
              <AgentSteps
                steps={message.agent_steps}
                defaultExpanded={false}
              />
            </div>
          )}

          {/* Markdown Content */}
          <div
            className={cn(
              "prose prose-sm max-w-none break-words leading-relaxed",
              isUser
                ? "prose-invert text-white [&>p]:leading-relaxed"
                : "text-slate-800 prose-headings:text-navy-950 prose-a:text-indigo-600 prose-a:underline hover:prose-a:text-indigo-800 prose-strong:text-navy-950 prose-ul:my-2 prose-li:my-0.5"
            )}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Audio Player Control if available */}
          {!isUser && message.audio_url && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onPlayAudio && onPlayAudio(message.audio_url!)}
                  className="h-7 px-2.5 text-xs gap-1.5 border-indigo-200 text-indigo-700 hover:bg-indigo-50"
                >
                  {isPlayingAudio ? (
                    <>
                      <VolumeX className="h-3.5 w-3.5 text-indigo-600" />
                      <span>Stop Listening</span>
                    </>
                  ) : (
                    <>
                      <Volume2 className="h-3.5 w-3.5 text-indigo-600" />
                      <span>Listen to Answer</span>
                    </>
                  )}
                </Button>
                <span className="text-[11px] text-muted-foreground">
                  Voice Synthesis
                </span>
              </div>
            </div>
          )}

          {/* Eligibility Data Quick Summary if present */}
          {!isUser && message.eligibility_data && (
            <div className="mt-3 rounded-lg bg-emerald-50 border border-emerald-200 p-2.5 text-xs text-emerald-950">
              <div className="flex items-center gap-1.5 font-semibold mb-1 text-emerald-900">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700" />
                <span>Eligibility Assessment Detected</span>
              </div>
              <p className="text-[11px] text-emerald-800">
                You can run a full assessment on the{" "}
                <a
                  href="/eligibility"
                  className="underline font-semibold hover:text-emerald-950"
                >
                  Eligibility Checker page
                </a>
                .
              </p>
            </div>
          )}

          {/* Source Citations */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <SourceCitationList citations={message.sources} />
          )}
        </div>

        {/* Suggested Questions Chips */}
        {!isUser &&
          message.suggested_questions &&
          message.suggested_questions.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {message.suggested_questions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectSuggestion && onSelectSuggestion(suggestion)}
                  className="rounded-full border border-navy-200 bg-white px-3 py-1 text-xs text-navy-800 shadow-2xs transition hover:bg-navy-50 hover:border-navy-400 text-left font-medium active:scale-[0.98]"
                >
                  💡 {suggestion}
                </button>
              ))}
            </div>
          )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full bg-slate-300 text-slate-700 shadow-sm mt-1">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}
