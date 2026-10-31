"use client";

import React from "react";
import { LANGUAGES } from "@/lib/constants";
import { Language } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Languages } from "lucide-react";
import { cn } from "@/lib/utils";

interface LanguageSelectorProps {
  value?: Language;
  onChange?: (lang: Language) => void;
  className?: string;
  variant?: "default" | "compact";
}

export function LanguageSelector({
  value,
  onChange,
  className,
  variant = "default",
}: LanguageSelectorProps) {
  const context = useLanguage();
  const currentLang = value || context.language;

  const handleValueChange = (newVal: string) => {
    const lang = newVal as Language;
    if (onChange) {
      onChange(lang);
    } else {
      context.setLanguage(lang);
    }
  };

  const selectedItem = LANGUAGES.find((l) => l.code === currentLang) || LANGUAGES[0];

  return (
    <div className={cn("inline-flex items-center", className)}>
      <Select value={currentLang} onValueChange={handleValueChange}>
        <SelectTrigger className="w-[145px] h-9 bg-white border-navy-200 text-navy-900 font-medium text-xs shadow-sm hover:border-navy-400 focus:ring-navy-700">
          <div className="flex items-center gap-2 truncate">
            <Languages className="w-3.5 h-3.5 text-navy-700 shrink-0" />
            <span className="truncate">
              {selectedItem.flag} {selectedItem.nativeName}
            </span>
          </div>
        </SelectTrigger>
        <SelectContent align="end" className="bg-white border-navy-100 shadow-lg">
          {LANGUAGES.map((lang) => (
            <SelectItem
              key={lang.code}
              value={lang.code}
              className="text-xs font-medium cursor-pointer py-2 hover:bg-navy-50"
            >
              <div className="flex items-center justify-between w-full gap-2">
                <span>
                  {lang.flag} {lang.name}
                </span>
                <span className="text-muted-foreground text-[11px]">
                  ({lang.nativeName})
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
