"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LanguageSelector } from "@/components/ui/LanguageSelector";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Menu,
  Sparkles,
  Bot,
  Layers,
  CheckCircle,
  FileText,
  Info,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { name: "Home", href: "/", icon: Sparkles },
  { name: "AI Assistant", href: "/assistant", icon: Bot },
  { name: "Schemes", href: "/schemes", icon: Layers },
  { name: "Eligibility", href: "/eligibility", icon: CheckCircle },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "About", href: "/about", icon: Info },
];

export function Header() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-navy-100 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-8">
        {/* Logo Branding */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-navy-900 to-indigo-700 text-white shadow-sm transition group-hover:scale-105">
            <ShieldCheck className="h-5 w-5 text-indigo-200" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-lg text-navy-950 tracking-tight">
                JanSahayak
              </span>
              <span className="rounded-md bg-indigo-600 px-1.5 py-0.2 text-[10px] font-bold text-white uppercase tracking-wider">
                AI
              </span>
            </div>
            <span className="text-[10px] text-slate-500 font-medium">
              National Scheme Explainer
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "px-3.5 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5",
                  isActive
                    ? "bg-navy-50 text-navy-900 font-bold"
                    : "text-slate-600 hover:text-navy-950 hover:bg-slate-100/60"
                )}
              >
                <item.icon
                  className={cn(
                    "w-3.5 h-3.5",
                    isActive ? "text-navy-700" : "text-slate-400"
                  )}
                />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Actions & Language Selector */}
        <div className="flex items-center gap-2 sm:gap-3">
          <LanguageSelector />

          <Link href="/assistant" className="hidden sm:inline-flex">
            <Button
              size="sm"
              className="bg-navy-700 hover:bg-navy-800 text-white text-xs h-9 shadow-xs gap-1.5 font-medium"
            >
              <Bot className="w-3.5 h-3.5 text-indigo-300" />
              <span>Ask AI</span>
            </Button>
          </Link>

          {/* Mobile Menu Hamburger */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden h-9 w-9 text-slate-700"
                aria-label="Open menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[280px] sm:w-[320px] p-6">
              <SheetHeader className="text-left pb-4 border-b">
                <SheetTitle className="flex items-center gap-2 text-base text-navy-950 font-bold">
                  <ShieldCheck className="h-5 w-5 text-indigo-600" />
                  JanSahayak AI
                </SheetTitle>
              </SheetHeader>

              <div className="flex flex-col gap-2 py-4">
                {NAV_ITEMS.map((item) => {
                  const isActive =
                    item.href === "/"
                      ? pathname === "/"
                      : pathname.startsWith(item.href);

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition",
                        isActive
                          ? "bg-navy-100 text-navy-900 font-bold"
                          : "text-slate-700 hover:bg-slate-100"
                      )}
                    >
                      <item.icon
                        className={cn(
                          "w-4 h-4",
                          isActive ? "text-navy-700" : "text-slate-500"
                        )}
                      />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>

              <div className="pt-4 border-t flex flex-col gap-3">
                <span className="text-xs font-semibold text-slate-500">
                  Select Language
                </span>
                <LanguageSelector className="w-full" />
                <Link
                  href="/assistant"
                  onClick={() => setMobileMenuOpen(false)}
                  className="mt-2"
                >
                  <Button className="w-full bg-navy-700 text-white text-xs">
                    Open AI Assistant
                  </Button>
                </Link>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
