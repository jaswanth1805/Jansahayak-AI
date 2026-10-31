"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Bot, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentStepsProps {
  steps: string[];
  isLoading?: boolean;
  className?: string;
  defaultExpanded?: boolean;
}

export function AgentSteps({
  steps,
  isLoading = false,
  className,
  defaultExpanded = true,
}: AgentStepsProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  if (!steps || steps.length === 0) return null;

  return (
    <div
      className={cn(
        "rounded-lg border border-navy-100 bg-gradient-to-r from-navy-50/70 to-indigo-50/40 p-3 text-xs shadow-sm transition-all",
        className
      )}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between text-navy-800 font-medium hover:text-navy-950 transition"
      >
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-navy-700 text-white shadow-xs">
            {isLoading ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Sparkles className="h-3 w-3" />
            )}
          </div>
          <span className="font-semibold text-navy-900">
            Agent Reasoning & Verification
          </span>
          <span className="rounded-full bg-navy-200/60 px-2 py-0.5 text-[10px] text-navy-800 font-mono">
            {steps.length} {steps.length === 1 ? "step" : "steps"}
          </span>
        </div>
        <div className="flex items-center gap-1 text-muted-foreground text-[11px]">
          <span>{isExpanded ? "Hide" : "Show"} details</span>
          {isExpanded ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="mt-2.5 pt-2 border-t border-navy-100 space-y-1.5">
          {steps.map((step, idx) => {
            const isLast = idx === steps.length - 1;
            const isRunning = isLast && isLoading;

            return (
              <div
                key={idx}
                className="flex items-start gap-2 text-navy-900/90 leading-relaxed font-sans"
              >
                {isRunning ? (
                  <Loader2 className="h-3.5 w-3.5 text-indigo-600 animate-spin shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0 mt-0.5" />
                )}
                <span className={cn(isRunning ? "font-medium text-indigo-900" : "")}>
                  {step}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
