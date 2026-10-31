"use client";

import React, { useRef, useEffect, useState } from "react";
import { Send, Mic, Paperclip, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  isLoading?: boolean;
  onOpenVoiceModal?: () => void;
  onOpenDocModal?: () => void;
  placeholder?: string;
  className?: string;
  initialValue?: string;
}

const MAX_CHARS = 1000;

export function ChatInput({
  onSendMessage,
  isLoading = false,
  onOpenVoiceModal,
  onOpenDocModal,
  placeholder = "Ask about any Indian government scheme, eligibility, or benefit...",
  className,
  initialValue = "",
}: ChatInputProps) {
  const [text, setText] = useState(initialValue);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (initialValue) {
      setText(initialValue);
    }
  }, [initialValue]);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        180
      )}px`;
    }
  }, [text]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!text.trim() || isLoading) return;
    onSendMessage(text.trim());
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const remainingChars = MAX_CHARS - text.length;

  return (
    <div
      className={cn(
        "relative rounded-2xl border border-slate-300 bg-white shadow-md focus-within:border-navy-600 focus-within:ring-2 focus-within:ring-navy-100 transition-all",
        className
      )}
    >
      <form onSubmit={handleSubmit} className="flex flex-col">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => {
            if (e.target.value.length <= MAX_CHARS) {
              setText(e.target.value);
            }
          }}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
          placeholder={placeholder}
          className="w-full resize-none border-0 bg-transparent px-4 pt-3.5 pb-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-0 disabled:opacity-50"
        />

        <div className="flex items-center justify-between px-3 py-2 border-t border-slate-100 bg-slate-50/50 rounded-b-2xl">
          <div className="flex items-center gap-1">
            {onOpenDocModal && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={onOpenDocModal}
                disabled={isLoading}
                title="Upload government circular or application PDF"
                className="h-8 w-8 text-slate-600 hover:text-navy-900 hover:bg-slate-200/60"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
            )}

            {onOpenVoiceModal && (
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={onOpenVoiceModal}
                disabled={isLoading}
                title="Use voice input"
                className="h-8 w-8 text-slate-600 hover:text-navy-900 hover:bg-slate-200/60"
              >
                <Mic className="h-4 w-4" />
              </Button>
            )}

            <span className="text-[11px] text-muted-foreground ml-2 hidden sm:inline">
              Press <kbd className="rounded bg-slate-200 px-1 py-0.5 text-[10px]">Enter</kbd> to send, <kbd className="rounded bg-slate-200 px-1 py-0.5 text-[10px]">Shift+Enter</kbd> for newline
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={cn(
                "text-[10px]",
                remainingChars < 50 ? "text-amber-600 font-bold" : "text-slate-400"
              )}
            >
              {remainingChars}
            </span>

            <Button
              type="submit"
              size="sm"
              disabled={!text.trim() || isLoading}
              className="h-8 px-3.5 bg-navy-700 hover:bg-navy-800 text-white rounded-lg flex items-center gap-1.5 transition-all shadow-xs"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span className="text-xs">Thinking...</span>
                </>
              ) : (
                <>
                  <span className="text-xs font-semibold">Send</span>
                  <Send className="h-3.5 w-3.5" />
                </>
              )}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
