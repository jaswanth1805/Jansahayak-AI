"use client";

import React, { useState } from "react";
import { GovernmentScheme } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Building2,
  ExternalLink,
  CheckCircle2,
  Calendar,
  Sparkles,
  Users,
  FileCheck,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface SchemeCardProps {
  scheme: GovernmentScheme;
  onCheckEligibility?: (scheme: GovernmentScheme) => void;
  className?: string;
}

export function SchemeCard({
  scheme,
  onCheckEligibility,
  className,
}: SchemeCardProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);

  const formattedDate = scheme.last_verified
    ? new Date(scheme.last_verified).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : null;

  return (
    <>
      <Card
        className={cn(
          "flex flex-col justify-between border-slate-200 bg-white transition duration-200 hover:shadow-md hover:border-navy-200",
          className
        )}
      >
        <CardHeader className="p-5 pb-3">
          <div className="flex flex-wrap items-center gap-1.5 mb-2">
            {scheme.category && (
              <Badge variant="indigo" className="text-[10px] py-0 px-2 font-medium">
                {scheme.category}
              </Badge>
            )}
            {scheme.ministry && (
              <Badge variant="navy" className="text-[10px] py-0 px-2 flex items-center gap-1 font-medium">
                <Building2 className="w-3 h-3" />
                <span className="truncate max-w-[150px]">{scheme.ministry}</span>
              </Badge>
            )}
            {scheme.state && (
              <Badge variant="secondary" className="text-[10px] py-0 px-2">
                {scheme.state}
              </Badge>
            )}
          </div>

          <CardTitle className="text-base font-bold text-navy-950 leading-snug line-clamp-2">
            {scheme.name}
          </CardTitle>

          {(scheme.name_hindi || scheme.name_telugu) && (
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground mt-1">
              {scheme.name_hindi && (
                <span className="font-hindi text-[11px] text-navy-700">
                  {scheme.name_hindi}
                </span>
              )}
              {scheme.name_telugu && (
                <span className="text-[11px] text-indigo-700">
                  {scheme.name_telugu}
                </span>
              )}
            </div>
          )}

          <CardDescription className="text-xs text-slate-600 line-clamp-3 mt-2 leading-relaxed">
            {scheme.description}
          </CardDescription>
        </CardHeader>

        <CardContent className="p-5 pt-0 pb-3 flex-1">
          {scheme.beneficiary_types && scheme.beneficiary_types.length > 0 && (
            <div className="mb-3">
              <div className="flex items-center gap-1 text-[11px] font-semibold text-navy-900 mb-1">
                <Users className="w-3.5 h-3.5 text-navy-600" />
                <span>Target Beneficiaries</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {scheme.beneficiary_types.slice(0, 3).map((b, i) => (
                  <span
                    key={i}
                    className="inline-block bg-slate-100 text-slate-700 rounded px-1.5 py-0.5 text-[10px] font-medium"
                  >
                    {b}
                  </span>
                ))}
                {scheme.beneficiary_types.length > 3 && (
                  <span className="inline-block bg-slate-100 text-slate-500 rounded px-1.5 py-0.5 text-[10px]">
                    +{scheme.beneficiary_types.length - 3} more
                  </span>
                )}
              </div>
            </div>
          )}

          {scheme.benefits && scheme.benefits.length > 0 && (
            <div>
              <div className="flex items-center gap-1 text-[11px] font-semibold text-emerald-800 mb-1">
                <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                <span>Key Benefits</span>
              </div>
              <ul className="text-xs text-slate-700 space-y-1">
                {scheme.benefits.slice(0, 2).map((benefit, idx) => (
                  <li key={idx} className="flex items-start gap-1.5 text-[11px] leading-tight">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span className="line-clamp-2">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>

        <CardFooter className="p-5 pt-2 flex flex-col gap-2.5 border-t border-slate-100 bg-slate-50/50 rounded-b-xl">
          <div className="flex items-center justify-between w-full text-[11px] text-muted-foreground">
            {formattedDate ? (
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3 text-slate-400" />
                Source fetched: {formattedDate}
              </span>
            ) : (
              <span className="flex items-center gap-1 text-amber-700">
                {scheme.source === "curated_registry" ? "Curated reference — not freshly checked" : "Source date unavailable"}
              </span>
            )}

            <button
              onClick={() => setDetailsOpen(true)}
              className="text-navy-700 font-semibold hover:underline flex items-center gap-0.5"
            >
              Details
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 w-full">
            <Link
              href={`/eligibility?scheme=${encodeURIComponent(scheme.name)}`}
              className="w-full"
            >
              <Button
                variant="outline"
                size="sm"
                className="w-full text-xs h-8 border-navy-300 text-navy-800 hover:bg-navy-50"
              >
                Check Eligibility
              </Button>
            </Link>

            {scheme.official_url ? (
              <a
                href={scheme.official_url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full"
              >
                <Button
                  size="sm"
                  className="w-full text-xs h-8 bg-navy-700 hover:bg-navy-800 text-white flex items-center justify-center gap-1"
                >
                  Official Link
                  <ExternalLink className="w-3 h-3" />
                </Button>
              </a>
            ) : scheme.application_url ? (
              <a
                href={scheme.application_url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full"
              >
                <Button
                  size="sm"
                  className="w-full text-xs h-8 bg-navy-700 hover:bg-navy-800 text-white flex items-center justify-center gap-1"
                >
                  Apply Now
                  <ExternalLink className="w-3 h-3" />
                </Button>
              </a>
            ) : null}
          </div>
        </CardFooter>
      </Card>

      {/* Full Scheme Details Dialog */}
      <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex flex-wrap gap-2 mb-2">
              {scheme.category && <Badge variant="indigo">{scheme.category}</Badge>}
              {scheme.ministry && <Badge variant="navy">{scheme.ministry}</Badge>}
              {scheme.state && <Badge variant="secondary">{scheme.state}</Badge>}
            </div>
            <DialogTitle className="text-xl text-navy-950 font-bold leading-tight">
              {scheme.name}
            </DialogTitle>
            {(scheme.name_hindi || scheme.name_telugu) && (
              <div className="flex flex-wrap gap-3 text-sm text-muted-foreground pt-1">
                {scheme.name_hindi && <span>हिंदी: {scheme.name_hindi}</span>}
                {scheme.name_telugu && <span>తెలుగు: {scheme.name_telugu}</span>}
              </div>
            )}
            <DialogDescription className="text-sm text-slate-700 pt-2 leading-relaxed">
              {scheme.description}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {scheme.benefits && scheme.benefits.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-navy-900 mb-2 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  Benefits Offered
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-700 bg-emerald-50/60 p-3 rounded-lg border border-emerald-100">
                  {scheme.benefits.map((b, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {scheme.eligibility_criteria && scheme.eligibility_criteria.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-navy-900 mb-2 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                  Eligibility Criteria
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-200">
                  {scheme.eligibility_criteria.map((c, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-navy-600 shrink-0 mt-1.5" />
                      <span>{c}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {scheme.required_documents && scheme.required_documents.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-navy-900 mb-2 flex items-center gap-1.5">
                  <FileCheck className="w-4 h-4 text-amber-600" />
                  Required Documents
                </h4>
                <div className="flex flex-wrap gap-1.5 bg-amber-50/50 p-3 rounded-lg border border-amber-100">
                  {scheme.required_documents.map((doc, i) => (
                    <Badge
                      key={i}
                      variant="outline"
                      className="bg-white text-slate-700 text-xs border-amber-200"
                    >
                      {doc}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-2 flex flex-col sm:flex-row gap-2 justify-between items-center border-t text-xs text-muted-foreground">
              <span>Source: {scheme.source || "Official Government Portal"}</span>
              <div className="flex gap-2 w-full sm:w-auto">
                <Link
                  href={`/eligibility?scheme=${encodeURIComponent(scheme.name)}`}
                  className="flex-1 sm:flex-initial"
                >
                  <Button variant="outline" size="sm" className="w-full">
                    Check Eligibility
                  </Button>
                </Link>
                {scheme.official_url && (
                  <a
                    href={scheme.official_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 sm:flex-initial"
                  >
                    <Button size="sm" className="bg-navy-700 text-white w-full">
                      Visit Portal <ExternalLink className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </a>
                )}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
