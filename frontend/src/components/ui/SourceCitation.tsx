"use client";

import React from "react";
import { SourceCitation as CitationType } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, CheckCircle, ShieldCheck, Clock, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface SourceCitationProps {
  citation: CitationType;
  className?: string;
}

export function SourceCitation({ citation, className }: SourceCitationProps) {
  const formattedDate = citation.retrieved_at
    ? new Date(citation.retrieved_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null;

  return (
    <div
      className={cn(
        "group relative flex flex-col gap-1.5 rounded-lg border border-slate-200 bg-white p-3 text-xs shadow-xs transition hover:border-navy-300 hover:shadow-sm",
        className
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          <Badge
            variant="navy"
            className="text-[10px] uppercase tracking-wider py-0 px-2"
          >
            {citation.source_type || "Official Source"}
          </Badge>

          {citation.is_verified ? (
            <Badge
              variant="success"
              className="flex items-center gap-1 text-[10px] py-0 px-1.5"
            >
              <ShieldCheck className="h-3 w-3" />
              Verified
            </Badge>
          ) : (
            <Badge variant="secondary" className="text-[10px] py-0 px-1.5">
              Unverified
            </Badge>
          )}

          {citation.page_number && (
            <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
              <FileText className="h-3 w-3" />
              Page {citation.page_number}
            </span>
          )}

          {citation.section && (
            <span className="text-[11px] text-muted-foreground font-mono">
              Sec: {citation.section}
            </span>
          )}
        </div>

        {formattedDate && (
          <span className="flex items-center gap-1 text-[10px] text-muted-foreground shrink-0">
            <Clock className="h-2.5 w-2.5" />
            {formattedDate}
          </span>
        )}
      </div>

      <div className="mt-0.5">
        <h4 className="font-semibold text-navy-950 text-xs line-clamp-1 group-hover:text-navy-700">
          {citation.title}
        </h4>
      </div>

      {citation.url && (
        <a
          href={citation.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-[11px] text-indigo-600 hover:text-indigo-800 font-medium mt-1 truncate"
        >
          <span className="truncate">{citation.url}</span>
          <ExternalLink className="h-3 w-3 shrink-0" />
        </a>
      )}
    </div>
  );
}

export function SourceCitationList({
  citations,
  className,
}: {
  citations: CitationType[];
  className?: string;
}) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className={cn("space-y-2 mt-3", className)}>
      <div className="flex items-center gap-1.5 text-xs font-semibold text-navy-800">
        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
        <span>Official Government Sources & Citations ({citations.length})</span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {citations.map((c, i) => (
          <SourceCitation key={i} citation={c} />
        ))}
      </div>
    </div>
  );
}
