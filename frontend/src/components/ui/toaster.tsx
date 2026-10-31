"use client";

import { useToast } from "@/components/ui/use-toast";
import { X, CheckCircle2, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

export function Toaster() {
  const { toasts, dismiss } = useToast();

  if (!toasts.length) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "pointer-events-auto flex items-start gap-3 rounded-lg border p-4 shadow-lg transition-all animate-in slide-in-from-bottom-5 bg-white text-navy-950",
            t.variant === "destructive" && "border-red-200 bg-red-50 text-red-900",
            t.variant === "success" && "border-emerald-200 bg-emerald-50 text-emerald-900"
          )}
        >
          {t.variant === "destructive" && (
            <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          )}
          {t.variant === "success" && (
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
          )}
          {(!t.variant || t.variant === "default") && (
            <Info className="h-5 w-5 text-navy-700 shrink-0 mt-0.5" />
          )}

          <div className="flex-1">
            {t.title && <p className="text-sm font-semibold">{t.title}</p>}
            {t.description && (
              <p className="text-xs text-muted-foreground mt-0.5">{t.description}</p>
            )}
          </div>

          <button
            onClick={() => dismiss(t.id)}
            className="text-gray-400 hover:text-gray-700 p-0.5 rounded transition"
            aria-label="Dismiss toast"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
