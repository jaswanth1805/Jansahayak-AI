"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  ShieldCheck,
  Landmark,
  Languages,
  Code2,
  Lock,
  AlertTriangle,
  ExternalLink,
  Users,
  Heart,
  Globe,
  Database,
  CheckCircle2,
  FileText,
  Bot,
  Zap,
} from "lucide-react";
import Link from "next/link";

export default function AboutPage() {
  const verifiedSources = [
    {
      name: "myScheme Portal",
      authority: "Ministry of Electronics and Information Technology (MeitY)",
      url: "https://www.myscheme.gov.in",
      dataType: "Central & State Welfare Scheme metadata, criteria, and benefits",
      frequency: "Daily automated synchronization",
      coverage: "500+ National & State schemes",
    },
    {
      name: "National Portal of India",
      authority: "National Informatics Centre (NIC)",
      url: "https://www.india.gov.in",
      dataType: "Official circulars, citizen service portals, ministry directories",
      frequency: "Weekly index verification",
      coverage: "All Central Ministries & State Secretariats",
    },
    {
      name: "Open Government Data (OGD) Platform",
      authority: "Government of India",
      url: "https://data.gov.in",
      dataType: "Public sector datasets, budget allocations, census profiles",
      frequency: "Monthly policy metrics",
      coverage: "Nationwide demographic & scheme disbursement records",
    },
    {
      name: "PM-KISAN & DBT Bharat Portals",
      authority: "Ministry of Agriculture & Farmers Welfare / DBT Mission",
      url: "https://dbtbharat.gov.in",
      dataType: "Direct Benefit Transfer rules and Aadhaar mapping protocols",
      frequency: "Real-time verification",
      coverage: "Farmer and rural subsidy benefit pipelines",
    },
  ];

  const techStack = [
    { name: "Next.js 14", desc: "App Router, Server Components & Streaming UI", category: "Frontend" },
    { name: "TypeScript", desc: "Strict type safety across API schemas", category: "Language" },
    { name: "Tailwind CSS & shadcn/ui", desc: "Accessible, responsive civic design system", category: "Styling" },
    { name: "FastAPI & Python", desc: "High-performance RAG backend service", category: "Backend" },
    { name: "Web Speech API", desc: "In-browser multilingual Speech-to-Text", category: "Voice" },
    { name: "LangChain / LLM Agent", desc: "Knowledge retrieval and source citation verification", category: "AI & RAG" },
  ];

  return (
    <div className="flex-1 py-12 px-4 sm:px-8 max-w-6xl mx-auto w-full space-y-16">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto">
        <Badge variant="indigo" className="mb-3 text-xs font-semibold px-3 py-1">
          Civic Tech Initiative
        </Badge>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-navy-950 tracking-tight leading-tight">
          About JanSahayak AI
        </h1>
        <p className="text-slate-600 mt-4 text-sm sm:text-base leading-relaxed">
          Democratizing access to Indian public policy through transparent,
          multilingual, and source-grounded artificial intelligence.
        </p>
      </div>

      {/* Mission & Problem Statement */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-navy-100 text-navy-800 mb-4">
            <AlertTriangle className="h-6 w-6 text-navy-700" />
          </div>
          <h2 className="text-xl font-bold text-navy-950 mb-3">
            The Problem We Are Solving
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed space-y-2">
            Every year, thousands of crores of rupees allocated to Indian welfare
            schemes remain unclaimed. Complex gazette circulars, bureaucratic
            jargon, fragmented portals, and language barriers prevent rural,
            marginalized, and vernacular-speaking citizens from discovering
            benefits they legally qualify for.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-emerald-800 mb-4">
            <Heart className="h-6 w-6 text-emerald-700" />
          </div>
          <h2 className="text-xl font-bold text-navy-950 mb-3">
            Our Mission & Vision
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
            JanSahayak AI was built to ensure that no citizen in India is left
            behind due to digital or linguistic literacy divides. By combining
            modern AI language models with strict retrieval from official
            government documents, we provide instant, verified, and plain-language
            guidance in English, Hindi, and Telugu.
          </p>
        </div>
      </div>

      {/* Official Government Sources Registry */}
      <div className="space-y-6">
        <div className="border-b border-slate-200 pb-4">
          <div className="flex items-center gap-2 text-indigo-700 font-bold text-xs uppercase tracking-wider mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Integrity & Verification</span>
          </div>
          <h2 className="text-2xl font-bold text-navy-950 tracking-tight">
            Official Data Sources Registry
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 mt-1">
            All facts, criteria, and benefits displayed in JanSahayak AI are
            retrieved directly from authorized Indian government sources.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {verifiedSources.map((source, idx) => (
            <Card key={idx} className="border-slate-200 bg-white shadow-xs">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-bold text-navy-950">
                    {source.name}
                  </CardTitle>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:text-indigo-800 flex items-center gap-1 text-xs font-semibold"
                  >
                    Portal <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <span className="text-[11px] text-muted-foreground font-medium">
                  {source.authority}
                </span>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-slate-700 pt-0">
                <div>
                  <span className="font-semibold text-navy-900">Data Type: </span>
                  {source.dataType}
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                  <span>Frequency: {source.frequency}</span>
                  <span className="font-semibold text-emerald-700">● {source.coverage}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Supported Languages */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs">
        <div className="flex items-center gap-2 mb-4">
          <Languages className="w-5 h-5 text-indigo-600" />
          <h2 className="text-xl font-bold text-navy-950">
            Multilingual Accessibility
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-slate-600 mb-6 leading-relaxed">
          JanSahayak AI provides end-to-end question answering, scheme cards, and
          voice assistance in three major Indian languages:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 text-center">
            <span className="text-2xl mb-1 block">🇮🇳</span>
            <h3 className="font-bold text-navy-950 text-sm">English</h3>
            <span className="text-xs text-slate-500">Official Indian English</span>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 text-center">
            <span className="text-2xl mb-1 block">🇮🇳</span>
            <h3 className="font-bold text-navy-950 text-sm">हिंदी (Hindi)</h3>
            <span className="text-xs text-slate-500">Devanagari script support</span>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 text-center">
            <span className="text-2xl mb-1 block">🇮🇳</span>
            <h3 className="font-bold text-navy-950 text-sm">తెలుగు (Telugu)</h3>
            <span className="text-xs text-slate-500">Telugu script support</span>
          </div>
        </div>
      </div>

      {/* Technology Architecture */}
      <div className="space-y-6">
        <div className="border-b border-slate-200 pb-4">
          <div className="flex items-center gap-2 text-navy-700 font-bold text-xs uppercase tracking-wider mb-1">
            <Code2 className="w-4 h-4" />
            <span>Modern Engineering</span>
          </div>
          <h2 className="text-2xl font-bold text-navy-950 tracking-tight">
            Technology Stack
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {techStack.map((tech, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-navy-950 text-sm">
                  {tech.name}
                </span>
                <Badge variant="secondary" className="text-[10px]">
                  {tech.category}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                {tech.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Privacy Policy & Data Handling */}
      <div id="privacy" className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs space-y-4">
        <div className="flex items-center gap-2">
          <Lock className="w-5 h-5 text-emerald-600" />
          <h2 className="text-xl font-bold text-navy-950">
            Privacy Policy & Data Security
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          We believe civic software must protect user privacy unconditionally:
        </p>
        <ul className="space-y-2 text-xs sm:text-sm text-slate-700">
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>
              <strong>No Personal Data Stored Permanently:</strong> We do not ask
              for Aadhaar numbers, bank account passwords, or personal credentials.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>
              <strong>Document Lifecycle:</strong> Uploaded circulars and PDFs are
              temporarily cached in volatile memory for indexing and deleted automatically
              within 24 hours.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>
              <strong>No Mandatory User Accounts:</strong> Anyone can explore schemes
              and run eligibility assessments anonymously.
            </span>
          </li>
        </ul>
      </div>

      {/* Limitations & Disclaimers */}
      <div id="terms" className="rounded-2xl border border-amber-200 bg-amber-50/70 p-6 sm:p-8 text-amber-950 space-y-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-600" />
          <h2 className="text-lg font-bold">Important Civic Disclaimer & Limitations</h2>
        </div>
        <p className="text-xs sm:text-sm leading-relaxed">
          JanSahayak AI is an independent, non-commercial informational tool designed
          to assist citizens. <strong>JanSahayak AI is not a government agency</strong>,
          and responses generated by artificial intelligence do not constitute legal
          commitments. Government scheme guidelines, budget outlays, and eligibility rules
          are subject to amendments by respective authorities. Always confirm final criteria
          on official portal links provided before submitting formal applications.
        </p>
      </div>

      {/* Team & GitHub CTA */}
      <div className="text-center py-6 border-t border-slate-200">
        <h3 className="text-lg font-bold text-navy-950 mb-2">
          Built for the Hackathon & Citizens of India
        </h3>
        <p className="text-xs sm:text-sm text-slate-600 mb-5">
          Have suggestions or want to contribute to the open-source civic repository?
        </p>
        <div className="flex justify-center gap-3">
          <Link href="/assistant">
            <Button className="bg-navy-700 hover:bg-navy-800 text-white text-xs px-6">
              Try JanSahayak AI Assistant
            </Button>
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button variant="outline" className="text-xs px-6">
              GitHub Repository <ExternalLink className="w-3.5 h-3.5 ml-1" />
            </Button>
          </a>
        </div>
      </div>
    </div>
  );
}
