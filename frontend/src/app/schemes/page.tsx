"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { api, GovernmentScheme, Language } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";
import { INDIAN_STATES, SCHEME_CATEGORIES } from "@/lib/constants";
import { SchemeCard } from "@/components/ui/SchemeCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Search,
  Filter,
  ShieldCheck,
  RotateCcw,
  Loader2,
  Layers,
  Sparkles,
  AlertCircle,
  HelpCircle,
  X,
} from "lucide-react";

export default function SchemesPage() {
  const { language } = useLanguage();

  const [schemes, setSchemes] = useState<GovernmentScheme[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedState, setSelectedState] = useState<string>("all");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedBeneficiary, setSelectedBeneficiary] = useState<string>("all");

  const [statesList, setStatesList] = useState<string[]>(INDIAN_STATES);
  const [categoriesList, setCategoriesList] = useState<string[]>(SCHEME_CATEGORIES);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sourceWarning, setSourceWarning] = useState<string | null>(null);
  const [retrievedAt, setRetrievedAt] = useState<string | null>(null);
  const latestSearch = useRef(0);
  const searchController = useRef<AbortController | null>(null);

  useEffect(() => () => {
    latestSearch.current += 1;
    searchController.current?.abort();
  }, []);

  // Beneficiary quick filters
  const BENEFICIARY_TYPES = [
    "All Beneficiaries",
    "Farmers",
    "Students",
    "Women",
    "Senior Citizens",
    "Small Business Owners",
    "Unemployed Youth",
    "Persons with Disabilities",
  ];

  // Fetch filter dropdown options from backend with fallback
  useEffect(() => {
    api
      .getStates()
      .then((states) => {
        if (states && states.length > 0) setStatesList(states);
      })
      .catch((e) => console.warn("Using default states list", e));

    api
      .getCategories()
      .then((cats) => {
        if (cats && cats.length > 0) setCategoriesList(cats);
      })
      .catch((e) => console.warn("Using default categories list", e));
  }, []);

  const loadSchemes = useCallback(
    async (query = "", state = "", category = "", lang: Language = language, beneficiary = selectedBeneficiary) => {
      searchController.current?.abort();
      const controller = new AbortController();
      searchController.current = controller;
      const requestId = ++latestSearch.current;
      setIsLoading(true);
      setError(null);
      setSourceWarning(null);
      try {
        const queryState = state === "all" ? undefined : state;
        const queryCategory = category === "all" ? undefined : category;

        const res = await api.searchSchemes(
          query,
          queryState,
          queryCategory,
          lang,
          beneficiary === "all" || beneficiary === "All Beneficiaries" ? undefined : beneficiary,
          controller.signal
        );
        if (requestId !== latestSearch.current) return;
        setSchemes(res.schemes || []);
        setTotal(res.total || res.schemes?.length || 0);
        setRetrievedAt(res.retrieved_at || null);
        setSourceWarning(res.warning || null);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        if (requestId !== latestSearch.current) return;
        console.error("Scheme fetch failed:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Could not retrieve schemes. Please verify that the backend is active."
        );
        setSchemes([]);
        setTotal(0);
        setRetrievedAt(null);
        setSourceWarning(null);
      } finally {
        if (requestId === latestSearch.current) setIsLoading(false);
      }
    },
    [language, selectedBeneficiary]
  );

  // Trigger search on mount and when filters change
  useEffect(() => {
    loadSchemes(searchQuery, selectedState, selectedCategory, language, selectedBeneficiary);
  }, [loadSchemes, selectedState, selectedCategory, selectedBeneficiary, language]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadSchemes(searchQuery, selectedState, selectedCategory, language, selectedBeneficiary);
  };

  const handleResetFilters = () => {
    setSearchQuery("");
    setSelectedState("all");
    setSelectedCategory("all");
    setSelectedBeneficiary("all");
    loadSchemes("", "all", "all", language, "all");
  };

  const displayedSchemes = schemes;

  return (
    <div className="flex-1 py-8 px-4 sm:px-8 max-w-7xl mx-auto w-full">
      {/* Header Banner */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="indigo" className="text-xs">
                Scheme Directory
              </Badge>
              {retrievedAt && (
                <span className="flex items-center gap-1 text-[11px] text-emerald-700 font-medium">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Search run {new Date(retrievedAt).toLocaleString()}
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 tracking-tight">
              Government Schemes Explorer
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-1">
              Search and filter through Indian Central & State Government
              initiatives from connected sources and a clearly labeled curated reference list.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetFilters}
              className="text-xs gap-1 border-slate-300 text-slate-700 hover:bg-slate-100"
            >
              <RotateCcw className="w-3 h-3" />
              Reset Filters
            </Button>
          </div>
        </div>

        {/* Search Bar & Dropdowns Filter Panel */}
        <div className="mt-6 rounded-2xl bg-white border border-slate-200 p-4 sm:p-5 shadow-xs space-y-4">
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                placeholder="Search by scheme name, keywords (e.g., kisan, solar, scholarship, housing)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-10 text-sm"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            <Button
              type="submit"
              disabled={isLoading}
              className="h-10 px-5 bg-navy-700 hover:bg-navy-800 text-white font-semibold text-xs"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
            </Button>
          </form>

          {/* Filter Dropdowns Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-100">
            {/* State Filter */}
            <div>
              <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                State / UT
              </label>
              <Select value={selectedState} onValueChange={setSelectedState}>
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder="All States & UTs" />
                </SelectTrigger>
                <SelectContent className="max-h-72">
                  <SelectItem value="all">All States / Central</SelectItem>
                  {statesList.map((state: any) => {
                    const val = typeof state === "string" ? state : state?.name || "";
                    if (!val) return null;
                    return (
                      <SelectItem key={val} value={val} className="text-xs">
                        {val}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                Sector / Category
              </label>
              <Select
                value={selectedCategory}
                onValueChange={setSelectedCategory}
              >
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent className="max-h-72">
                  <SelectItem value="all">All Categories</SelectItem>
                  {categoriesList.map((cat: any) => {
                    const val = typeof cat === "string" ? cat : cat?.name || "";
                    if (!val) return null;
                    return (
                      <SelectItem key={val} value={val} className="text-xs">
                        {val}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            {/* Beneficiary Filter */}
            <div>
              <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                Beneficiary Group
              </label>
              <Select
                value={selectedBeneficiary}
                onValueChange={setSelectedBeneficiary}
              >
                <SelectTrigger className="h-9 text-xs">
                  <SelectValue placeholder="All Groups" />
                </SelectTrigger>
                <SelectContent className="max-h-72">
                  {BENEFICIARY_TYPES.map((type) => (
                    <SelectItem
                      key={type}
                      value={type === "All Beneficiaries" ? "all" : type}
                      className="text-xs"
                    >
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-xs text-slate-600 font-medium">
          Showing{" "}
          <span className="font-bold text-navy-950">
            {displayedSchemes.length}
          </span>{" "}
          of <span className="font-bold text-navy-950">{total}</span> available schemes
        </div>

        {(error || sourceWarning) && (
          <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 px-2.5 py-1 rounded-md">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{error || sourceWarning}</span>
          </div>
        )}
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="rounded-xl border border-slate-200 bg-white p-5 space-y-3 animate-pulse"
            >
              <div className="flex gap-2">
                <div className="h-5 w-20 bg-slate-200 rounded-full" />
                <div className="h-5 w-24 bg-slate-200 rounded-full" />
              </div>
              <div className="h-6 w-3/4 bg-slate-200 rounded" />
              <div className="h-12 w-full bg-slate-100 rounded" />
              <div className="h-8 w-full bg-slate-200 rounded mt-4" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && displayedSchemes.length === 0 && (
        <div className="text-center py-16 px-4 bg-white rounded-2xl border border-slate-200">
          <HelpCircle className="h-12 w-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-navy-950 mb-1">
            No schemes found matching your criteria
          </h3>
          <p className="text-xs text-slate-600 max-w-sm mx-auto mb-6">
            Try adjusting your search query, or clear filters to view all
            available national and state schemes.
          </p>
          <Button
            onClick={handleResetFilters}
            className="bg-navy-700 text-white text-xs h-9"
          >
            Clear All Filters
          </Button>
        </div>
      )}

      {/* Scheme Cards Grid */}
      {!isLoading && displayedSchemes.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayedSchemes.map((scheme) => (
            <SchemeCard key={scheme.id} scheme={scheme} />
          ))}
        </div>
      )}
    </div>
  );
}
