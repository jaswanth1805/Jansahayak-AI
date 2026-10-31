"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { Language } from "@/lib/api";

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
}

const STORAGE_LANG_KEY = "jansahayak_lang";

const LanguageContext = createContext<LanguageContextType>({
  language: "en",
  setLanguage: () => {},
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(STORAGE_LANG_KEY) as Language;
      if (saved && (saved === "en" || saved === "hi" || saved === "te")) {
        setLanguageState(saved);
      }
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_LANG_KEY, lang);
    }
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
