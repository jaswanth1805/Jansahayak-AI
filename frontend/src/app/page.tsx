"use client";

import React from "react";
import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sparkles,
  Bot,
  Search,
  CheckCircle2,
  FileText,
  Volume2,
  ShieldCheck,
  ArrowRight,
  Landmark,
  Languages,
  BookOpen,
  FileCheck2,
  Clock,
  Layers,
  Award,
  Zap,
} from "lucide-react";

export default function HomePage() {
  const { language, setLanguage } = useLanguage();

  const subheadlines = {
    en: "Empowering citizens with AI-driven, official government scheme guidance in English, Hindi, and Telugu.",
    hi: "अंग्रेजी, हिंदी और तेलुगु में आधिकारिक सरकारी योजना मार्गदर्शन के साथ नागरिकों को सशक्त बनाना।",
    te: "ఇంగ్లీష్, హిందీ మరియు తెలుగులో అధికారిక ప్రభుత్వ పథకాల మార్గదర్శకత్వంతో పౌరులకు సాధికారత కల్పించడం.",
  };

  const featureCards = [
    {
      icon: FileText,
      title: "AI Document Understanding",
      desc: "Upload official PDFs, guidelines, and gazette notifications. Get clear, plain-language summaries without bureaucratic jargon.",
      tag: "PDF Analyzer",
      href: "/documents",
    },
    {
      icon: Search,
      title: "Live Scheme Discovery",
      desc: "Search hundreds of Central and State government schemes covering agriculture, education, pensions, and housing.",
      tag: "Live Data",
      href: "/schemes",
    },
    {
      icon: CheckCircle2,
      title: "Personalized Eligibility",
      desc: "Complete a simple multi-step assessment to verify if your profile meets specific criteria, plus see required documents.",
      tag: "Rule Engine",
      href: "/eligibility",
    },
    {
      icon: Languages,
      title: "Multilingual By Design",
      desc: "Interact smoothly across English, Hindi (हिंदी), and Telugu (తెలుగు) with native script responses and localized nuances.",
      tag: "3 Languages",
      href: "/assistant",
    },
    {
      icon: Volume2,
      title: "Voice Assistance",
      desc: "Speak your questions aloud using Web Speech input and listen to synthesized audio answers for maximum accessibility.",
      tag: "Voice STT & TTS",
      href: "/assistant",
    },
    {
      icon: ShieldCheck,
      title: "100% Verified Citations",
      desc: "Zero hallucination guarantee. Every response links directly to verified portals like myScheme.gov.in and india.gov.in.",
      tag: "Official Sources",
      href: "/about",
    },
  ];

  const workflowSteps = [
    {
      step: "01",
      title: "Ask in Your Language",
      desc: "Type or speak your query naturally in English, Hindi, or Telugu about any welfare scheme, grant, or subsidy.",
      icon: Bot,
    },
    {
      step: "02",
      title: "Official Verification",
      desc: "The AI agent consults real government databases, official guidelines, and eligibility rules in real time.",
      icon: ShieldCheck,
    },
    {
      step: "03",
      title: "Plain-Language Advice",
      desc: "Receive clear step-by-step guidance, benefits breakdown, required documents list, and warnings.",
      icon: Sparkles,
    },
    {
      step: "04",
      title: "Direct Application Link",
      desc: "Obtain official portals and application links directly to submit your forms with confidence.",
      icon: Landmark,
    },
  ];

  const officialSources = [
    {
      name: "myScheme Portal",
      domain: "myscheme.gov.in",
      desc: "National platform for Central & State Government schemes discovery",
    },
    {
      name: "National Portal of India",
      domain: "india.gov.in",
      desc: "Single-window access to information and government services",
    },
    {
      name: "Open Government Data Platform",
      domain: "data.gov.in",
      desc: "Direct access to published public government datasets",
    },
    {
      name: "Ministry & State Portals",
      domain: "gov.in domains",
      desc: "Authentic circulars from MoA&FW, MoHFW, MoE, and State departments",
    },
  ];

  return (
    <div className="flex flex-col w-full overflow-hidden">
      {/* Hero Section */}
      <section className="relative w-full pt-16 pb-24 md:pt-24 md:pb-32 overflow-hidden bg-gradient-to-b from-[#0f1f33] via-[#1e3a5f] to-[#0f1f33] text-white">
        {/* Subtle decorative glow circles */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-indigo-500/20 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute bottom-0 right-10 w-[400px] h-[250px] bg-sky-500/15 blur-[100px] rounded-full pointer-events-none" />

        <div className="container mx-auto px-4 sm:px-8 relative z-10 flex flex-col items-center text-center">
          {/* Language Pills */}
          <div className="inline-flex items-center gap-1.5 p-1 rounded-full bg-white/10 backdrop-blur-md border border-white/15 mb-6 text-xs">
            <span className="px-2 text-slate-300 font-medium">Select Language:</span>
            <button
              onClick={() => setLanguage("en")}
              className={`px-3 py-1 rounded-full font-semibold transition ${
                language === "en"
                  ? "bg-white text-navy-950 shadow-sm"
                  : "text-white/80 hover:text-white"
              }`}
            >
              English
            </button>
            <button
              onClick={() => setLanguage("hi")}
              className={`px-3 py-1 rounded-full font-semibold transition ${
                language === "hi"
                  ? "bg-white text-navy-950 shadow-sm"
                  : "text-white/80 hover:text-white"
              }`}
            >
              हिंदी
            </button>
            <button
              onClick={() => setLanguage("te")}
              className={`px-3 py-1 rounded-full font-semibold transition ${
                language === "te"
                  ? "bg-white text-navy-950 shadow-sm"
                  : "text-white/80 hover:text-white"
              }`}
            >
              తెలుగు
            </button>
          </div>

          {/* Trust Badge */}
          <div className="flex items-center gap-2 mb-4 px-3.5 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 text-xs font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Official Government Data Verification Engine</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight max-w-4xl text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-indigo-200 leading-[1.15] mb-6">
            Understand Your Rights. <br />
            Access Your Benefits.
          </h1>

          {/* Subheadline in Active Language */}
          <p className="text-base sm:text-xl text-slate-200 max-w-2xl mb-8 leading-relaxed font-normal">
            {subheadlines[language]}
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full justify-center max-w-md">
            <Link href="/assistant" className="w-full sm:w-auto">
              <Button
                size="lg"
                className="w-full sm:w-auto bg-indigo-500 hover:bg-indigo-600 text-white font-semibold shadow-lg shadow-indigo-500/25 gap-2 px-8 py-6 text-base rounded-xl"
              >
                <Bot className="w-5 h-5" />
                <span>Start Asking AI</span>
              </Button>
            </Link>

            <Link href="/schemes" className="w-full sm:w-auto">
              <Button
                size="lg"
                variant="outline"
                className="w-full sm:w-auto bg-white/10 hover:bg-white/20 text-white border-white/20 font-semibold backdrop-blur-xs gap-2 px-8 py-6 text-base rounded-xl"
              >
                <Layers className="w-5 h-5" />
                <span>Explore Schemes</span>
              </Button>
            </Link>
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-14 pt-8 border-t border-white/10 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl w-full text-center">
            <div>
              <div className="text-2xl sm:text-3xl font-extrabold text-white">500+</div>
              <div className="text-xs text-slate-300 mt-0.5">Central & State Schemes</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-extrabold text-white">3 Languages</div>
              <div className="text-xs text-slate-300 mt-0.5">English, Hindi & Telugu</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400">100%</div>
              <div className="text-xs text-slate-300 mt-0.5">Official Citations</div>
            </div>
            <div>
              <div className="text-2xl sm:text-3xl font-extrabold text-white">0 ₹</div>
              <div className="text-xs text-slate-300 mt-0.5">Completely Free & Open</div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Indicators Bar */}
      <section className="bg-navy-900 border-y border-white/10 py-5 text-slate-300">
        <div className="container mx-auto px-4 sm:px-8">
          <div className="flex flex-wrap items-center justify-around gap-6 text-xs sm:text-sm font-semibold">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <span>No Hallucinated Data</span>
            </div>
            <div className="flex items-center gap-2">
              <Landmark className="w-5 h-5 text-indigo-400" />
              <span>Official Government Sources Only</span>
            </div>
            <div className="flex items-center gap-2">
              <FileCheck2 className="w-5 h-5 text-sky-400" />
              <span>Verified Direct Portals</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-400" />
              <span>Real-Time Policy Updates</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-slate-50">
        <div className="container mx-auto px-4 sm:px-8">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <Badge variant="indigo" className="mb-3 px-3 py-1 font-semibold text-xs">
              Powerful Citizen Features
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-950 tracking-tight">
              Bridging the Gap Between Citizens & Public Policies
            </h2>
            <p className="text-slate-600 mt-3 text-sm sm:text-base">
              Every citizen deserves effortless access to government benefits.
              JanSahayak AI removes complex legal language and administrative friction.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featureCards.map((feat, idx) => (
              <Link
                key={idx}
                href={feat.href}
                className="group relative rounded-2xl border border-slate-200 bg-white p-7 shadow-xs transition duration-200 hover:-translate-y-1 hover:border-navy-300 hover:shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-navy-50 text-navy-700 transition group-hover:bg-navy-700 group-hover:text-white">
                      <feat.icon className="h-6 w-6" />
                    </div>
                    <Badge variant="secondary" className="text-[11px] font-medium">
                      {feat.tag}
                    </Badge>
                  </div>
                  <h3 className="text-lg font-bold text-navy-950 mb-2 group-hover:text-navy-700 transition">
                    {feat.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                    {feat.desc}
                  </p>
                </div>
                <div className="mt-6 flex items-center text-xs font-semibold text-navy-700 group-hover:text-indigo-600 transition">
                  <span>Learn more</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1 transition group-hover:translate-x-1" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-white border-t border-slate-200">
        <div className="container mx-auto px-4 sm:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <Badge variant="navy" className="mb-3 px-3 py-1 font-semibold text-xs">
              Simple 4-Step Process
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-navy-950 tracking-tight">
              How JanSahayak AI Works For You
            </h2>
            <p className="text-slate-600 mt-3 text-sm sm:text-base">
              From an informal query in your mother tongue to official portal application.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
            {workflowSteps.map((step, idx) => (
              <div
                key={idx}
                className="relative flex flex-col items-center text-center p-6 rounded-2xl bg-slate-50 border border-slate-100"
              >
                <div className="text-xs font-extrabold text-indigo-600 mb-2 tracking-wider">
                  STEP {step.step}
                </div>
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-navy-700 text-white shadow-md mb-4">
                  <step.icon className="w-7 h-7" />
                </div>
                <h3 className="text-base font-bold text-navy-950 mb-2">
                  {step.title}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Official Government Sources Registry */}
      <section className="py-20 bg-slate-50 border-t border-slate-200">
        <div className="container mx-auto px-4 sm:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <div className="flex items-center justify-center gap-2 text-emerald-700 font-bold text-xs uppercase tracking-wider mb-2">
              <ShieldCheck className="w-4 h-4" />
              <span>Authentic Government Portals</span>
            </div>
            <h2 className="text-3xl font-extrabold text-navy-950 tracking-tight">
              Data Sourced Directly From Official Portals
            </h2>
            <p className="text-slate-600 mt-2 text-sm">
              We never fabricate answers. JanSahayak AI indexes authorized Indian government portals.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {officialSources.map((source, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Landmark className="w-4 h-4 text-navy-700" />
                    <span className="font-bold text-navy-950 text-sm">
                      {source.name}
                    </span>
                  </div>
                  <span className="inline-block font-mono text-[11px] text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded mb-2">
                    {source.domain}
                  </span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {source.desc}
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-muted-foreground">
                  <span className="text-emerald-700 font-medium">● Verified Source</span>
                  <span>Daily Sync</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA Banner */}
      <section className="py-16 bg-gradient-to-r from-navy-900 to-indigo-900 text-white">
        <div className="container mx-auto px-4 sm:px-8 text-center max-w-3xl">
          <Sparkles className="w-10 h-10 text-indigo-300 mx-auto mb-4 animate-bounce" />
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
            Start using JanSahayak AI for free
          </h2>
          <p className="text-slate-300 text-sm sm:text-base mb-8 max-w-xl mx-auto">
            Discover all government scholarships, farmer benefits, housing subsidies,
            and health coverages tailored to your profile right now.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/assistant">
              <Button
                size="lg"
                className="bg-white text-navy-950 hover:bg-slate-100 font-bold px-8 h-12 rounded-xl shadow-md text-sm"
              >
                Launch AI Assistant
              </Button>
            </Link>
            <Link href="/eligibility">
              <Button
                size="lg"
                variant="outline"
                className="border-white/40 text-white hover:bg-white/10 font-bold px-8 h-12 rounded-xl text-sm"
              >
                Check Your Eligibility
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
