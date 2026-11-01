"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, Heart, ExternalLink, AlertTriangle } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-navy-950 text-white">
      <div className="container mx-auto px-4 sm:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Column 1: Branding */}
          <div className="md:col-span-1 space-y-3">
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <span className="font-extrabold text-lg tracking-tight">
                JanSahayak AI
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Empowering citizens across India with accessible, multilingual
              explanations of central and state government schemes.
            </p>
            <div className="pt-2 flex items-center gap-1.5 text-xs text-indigo-300 font-medium">
              <span>English</span> • <span>हिंदी</span> • <span>తెలుగు</span>
            </div>
          </div>

          {/* Column 2: Navigation */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-xs text-slate-300">
              <li>
                <Link href="/" className="hover:text-white transition">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/assistant" className="hover:text-white transition">
                  AI Scheme Assistant
                </Link>
              </li>
              <li>
                <Link href="/schemes" className="hover:text-white transition">
                  Scheme Explorer
                </Link>
              </li>
              <li>
                <Link
                  href="/eligibility"
                  className="hover:text-white transition"
                >
                  Eligibility Checker
                </Link>
              </li>
              <li>
                <Link href="/documents" className="hover:text-white transition">
                  Document Analyzer
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Government portal links */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
              Government Portals
            </h4>
            <ul className="space-y-2 text-xs text-slate-300">
              <li>
                <a
                  href="https://www.myscheme.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-white transition"
                >
                  myScheme.gov.in <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.india.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-white transition"
                >
                  National Portal (india.gov.in) <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a
                  href="https://data.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-white transition"
                >
                  Open Data Platform (data.gov.in) <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <Link href="/about" className="hover:text-white transition">
                  View Portal Directory
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 4: Legal & Trust */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
              Transparency & Ethics
            </h4>
            <div className="rounded-lg bg-navy-900 border border-navy-800 p-3 text-[11px] text-slate-300 leading-relaxed">
              <div className="flex items-center gap-1 text-amber-400 font-semibold mb-1">
                <AlertTriangle className="h-3 w-3 shrink-0" />
                <span>Disclaimer</span>
              </div>
              JanSahayak AI is an independent civic tech initiative. We do not
              claim to be a government authority. Source links are shown when
              available; confirm current eligibility and application rules with
              the responsible department before relying on them.
            </div>
            <div className="mt-3 text-xs text-slate-400">
              <Link href="/about#privacy" className="hover:underline mr-3">
                Privacy
              </Link>
              <Link href="/about#terms" className="hover:underline">
                Terms of Use
              </Link>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-navy-800 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-3">
          <p>© {new Date().getFullYear()} JanSahayak AI. Built for the citizens of India.</p>
          <div className="flex items-center gap-1 text-[11px]">
            <span>Crafted with</span>
            <Heart className="h-3 w-3 text-red-500 fill-red-500" />
            <span>for digital accessibility</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
