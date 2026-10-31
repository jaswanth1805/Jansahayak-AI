"use client";

import React from "react";
import { Mic, MicOff, Square, AlertCircle, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Language } from "@/lib/api";
import { cn } from "@/lib/utils";

interface VoiceControlProps {
  isListening: boolean;
  isPlaying?: boolean;
  language: Language;
  transcript: string;
  error?: string | null;
  onStartListening: () => void;
  onStopListening: () => void;
  onStopAudio?: () => void;
  className?: string;
}

export function VoiceControl({
  isListening,
  isPlaying = false,
  language,
  transcript,
  error,
  onStartListening,
  onStopListening,
  onStopAudio,
  className,
}: VoiceControlProps) {
  const languageLabels: Record<Language, string> = {
    en: "English (India)",
    hi: "हिंदी (Hindi)",
    te: "తెలుగు (Telugu)",
  };

  return (
    <div
      className={cn(
        "rounded-xl border bg-white p-4 shadow-sm transition-all",
        isListening ? "border-red-300 bg-red-50/30 ring-2 ring-red-100" : "border-slate-200",
        className
      )}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {/* Main Action Button */}
          {isListening ? (
            <button
              onClick={onStopListening}
              className="relative flex h-11 w-11 items-center justify-center rounded-full bg-red-600 text-white shadow-md transition hover:bg-red-700 animate-pulse"
              title="Stop listening"
            >
              <Square className="h-4 w-4 fill-white" />
              <span className="absolute -inset-1 rounded-full border-2 border-red-500 animate-ping opacity-75" />
            </button>
          ) : isPlaying ? (
            <button
              onClick={onStopAudio}
              className="flex h-11 w-11 items-center justify-center rounded-full bg-indigo-600 text-white shadow-md transition hover:bg-indigo-700"
              title="Stop playback"
            >
              <Square className="h-4 w-4 fill-white" />
            </button>
          ) : (
            <button
              onClick={onStartListening}
              className="flex h-11 w-11 items-center justify-center rounded-full bg-navy-700 text-white shadow-md transition hover:bg-navy-800 hover:scale-105 active:scale-95"
              title="Start voice search"
            >
              <Mic className="h-5 w-5" />
            </button>
          )}

          {/* Status & Waveform */}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-navy-950">
                {isListening
                  ? "Listening..."
                  : isPlaying
                  ? "Speaking response..."
                  : "Voice Assistance"}
              </span>
              <Badge variant="outline" className="text-[10px] py-0 px-2 font-mono">
                {languageLabels[language]}
              </Badge>
            </div>

            <p className="text-xs text-muted-foreground mt-0.5">
              {isListening
                ? "Speak clearly into your microphone..."
                : isPlaying
                ? "Playing audio synthesis..."
                : "Tap the microphone to speak your question"}
            </p>
          </div>
        </div>

        {/* CSS Animated Audio Waveform */}
        {isListening && (
          <div className="flex items-center gap-1 h-6 px-2">
            <span className="w-1 bg-red-500 rounded-full h-3 animate-waveform" style={{ animationDelay: "0ms" }} />
            <span className="w-1 bg-red-600 rounded-full h-6 animate-waveform" style={{ animationDelay: "200ms" }} />
            <span className="w-1 bg-red-500 rounded-full h-4 animate-waveform" style={{ animationDelay: "400ms" }} />
            <span className="w-1 bg-red-600 rounded-full h-5 animate-waveform" style={{ animationDelay: "150ms" }} />
            <span className="w-1 bg-red-500 rounded-full h-2 animate-waveform" style={{ animationDelay: "300ms" }} />
          </div>
        )}

        {isPlaying && (
          <div className="flex items-center gap-1 h-6 px-2">
            <span className="w-1 bg-indigo-500 rounded-full h-3 animate-waveform" style={{ animationDelay: "0ms" }} />
            <span className="w-1 bg-indigo-600 rounded-full h-5 animate-waveform" style={{ animationDelay: "250ms" }} />
            <span className="w-1 bg-indigo-500 rounded-full h-2 animate-waveform" style={{ animationDelay: "100ms" }} />
            <span className="w-1 bg-indigo-600 rounded-full h-4 animate-waveform" style={{ animationDelay: "350ms" }} />
          </div>
        )}
      </div>

      {/* Live Transcript Preview */}
      {isListening && transcript && (
        <div className="mt-3 rounded-md bg-white border border-red-200 p-2.5 text-xs text-slate-800 italic">
          &ldquo;{transcript}&rdquo;
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-2.5 flex items-center gap-1.5 rounded-md bg-red-50 p-2 text-xs text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
