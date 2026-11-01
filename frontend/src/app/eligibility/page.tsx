"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import {
  api,
  EligibilityProfile,
  EligibilityResult,
  Language,
} from "@/lib/api";
import { INDIAN_STATES } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  ExternalLink,
  ShieldCheck,
  FileCheck2,
  ListChecks,
  Loader2,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const OCCUPATION_OPTIONS = [
  "Farmer",
  "Student",
  "Government Employee",
  "Private Employee",
  "Self-employed / Micro-Entrepreneur",
  "Daily Wage Worker / Laborer",
  "Homemaker",
  "Unemployed",
  "Retired / Senior Citizen",
  "Other",
];

function EligibilityWizard() {
  const searchParams = useSearchParams();
  const { language } = useLanguage();

  const [step, setStep] = useState(1);
  const [schemeQuery, setSchemeQuery] = useState("");

  // Step 2 profile
  const [age, setAge] = useState<number | "">("");
  const [state, setState] = useState<string>("");
  const [gender, setGender] = useState<string>("");
  const [occupation, setOccupation] = useState<string>("");

  // Step 3 financial
  const [annualIncome, setAnnualIncome] = useState<number | "">("");
  const [isBPL, setIsBPL] = useState<boolean | undefined>(undefined);

  // Step 4 additional details
  const [isStudent, setIsStudent] = useState<boolean | undefined>(undefined);
  const [educationLevel, setEducationLevel] = useState<string>("Undergraduate");
  const [landHoldingAcres, setLandHoldingAcres] = useState<number | "">("");
  const [hasBusinessRegistration, setHasBusinessRegistration] = useState<boolean>(false);

  // Results & Loading
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<EligibilityResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check URL query parameters
  useEffect(() => {
    const q = searchParams.get("scheme");
    if (q) {
      setSchemeQuery(q);
    }
  }, [searchParams]);

  const handleRunAssessment = async () => {
    if (age === '' || !state || !gender || !occupation || annualIncome === '' || isStudent === undefined || isBPL === undefined) {
      setError('Please provide your age, state, gender, occupation, annual household income, student status, and BPL status before running the assessment.');
      return;
    }

    setIsLoading(true);
    setError(null);
    const profile: EligibilityProfile = {
      age,
      state,
      gender,
      occupation,
      annual_income: annualIncome,
      is_student: isStudent || occupation === 'Student',
      is_employed: occupation !== 'Unemployed',
      additional_info: {
        is_bpl: isBPL,
        education_level: educationLevel,
        land_holding_acres: landHoldingAcres,
        has_business_reg: hasBusinessRegistration,
      },
    };

    try {
      const response = await api.checkEligibility(
        profile,
        schemeQuery,
        language
      );
      setResults(response);
      setStep(5);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Eligibility assessment failed. Please retry.');
    } finally {
      setIsLoading(false);
    }
  };
  const getStatusBadge = (status: EligibilityResult["status"]) => {
    switch (status) {
      case "likely_eligible":
        return (
          <Badge variant="success" className="gap-1 font-semibold text-xs py-1 px-3">
            <CheckCircle2 className="w-3.5 h-3.5" /> Likely Eligible
          </Badge>
        );
      case "possibly_eligible":
        return (
          <Badge variant="warning" className="gap-1 font-semibold text-xs py-1 px-3">
            <AlertTriangle className="w-3.5 h-3.5" /> Possibly Eligible
          </Badge>
        );
      case "not_eligible":
        return (
          <Badge variant="destructive" className="gap-1 font-semibold text-xs py-1 px-3">
            <XCircle className="w-3.5 h-3.5" /> Not Eligible
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary" className="gap-1 font-semibold text-xs py-1 px-3">
            <HelpCircle className="w-3.5 h-3.5" /> Insufficient Info
          </Badge>
        );
    }
  };

  return (
    <div className="flex-1 py-10 px-4 sm:px-8 max-w-4xl mx-auto w-full">
      {/* Top Heading */}
      <div className="text-center mb-8">
        <Badge variant="indigo" className="mb-2 font-semibold">
          Smart Eligibility Engine
        </Badge>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 tracking-tight">
          Check Your Scheme Eligibility
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-xl mx-auto">
          Answer a few quick questions to find out which government schemes you
          qualify for, documents you need, and exact application procedures.
        </p>

        {/* Wizard Step Indicator */}
        <div className="max-w-md mx-auto mt-6">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
            <span className={step >= 1 ? "text-navy-900 font-bold" : ""}>1. Target</span>
            <span className={step >= 2 ? "text-navy-900 font-bold" : ""}>2. Profile</span>
            <span className={step >= 3 ? "text-navy-900 font-bold" : ""}>3. Financial</span>
            <span className={step >= 4 ? "text-navy-900 font-bold" : ""}>4. Specifics</span>
            <span className={step === 5 ? "text-emerald-700 font-bold" : ""}>5. Result</span>
          </div>
          <Progress value={(step / 5) * 100} className="h-2" />
        </div>
      </div>

      {/* Wizard Form Cards */}
      <Card className="border-slate-200 bg-white shadow-sm rounded-2xl">
        {/* STEP 1: What are you looking for? */}
        {step === 1 && (
          <div>
            <CardHeader>
              <CardTitle className="text-lg">Step 1: What benefits are you seeking?</CardTitle>
              <CardDescription className="text-xs">
                Specify a scheme name or describe your required assistance (e.g., student scholarships, crop loss aid, housing subsidy).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="scheme-query" className="text-xs font-semibold mb-1 block">
                  Search or describe benefit
                </Label>
                <Input
                  id="scheme-query"
                  placeholder="e.g. PM-KISAN, higher education scholarship, electric vehicle subsidy..."
                  value={schemeQuery}
                  onChange={(e) => setSchemeQuery(e.target.value)}
                  className="h-10 text-sm"
                />
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-600 block mb-2">
                  Popular topics:
                </span>
                <div className="flex flex-wrap gap-2">
                  {[
                    "Farmer Income Support (PM-KISAN)",
                    "Urban Housing (PMAY)",
                    "MUDRA Business Loan",
                    "Engineering Student Scholarship",
                    "Ayushman Bharat Health Cover",
                  ].map((preset, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setSchemeQuery(preset)}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-navy-50 hover:border-navy-300 text-xs text-navy-900 font-medium transition text-left"
                    >
                      {preset}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end border-t pt-4">
              <Button
                onClick={() => setStep(2)}
                className="bg-navy-700 text-white text-xs gap-1.5 h-9 px-5"
              >
                <span>Continue to Profile</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </CardFooter>
          </div>
        )}

        {/* STEP 2: Basic Information */}
        {step === 2 && (
          <div>
            <CardHeader>
              <CardTitle className="text-lg">Step 2: Basic Demographic Profile</CardTitle>
              <CardDescription className="text-xs">
                Your location, age, and occupation help determine regional and category-specific eligibility.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="age-input" className="text-xs font-semibold mb-1 block">
                    Age (Years)
                  </Label>
                  <Input
                    id="age-input"
                    type="number"
                    min={0}
                    max={120}
                    placeholder="e.g. 32"
                    value={age}
                    onChange={(e) =>
                      setAge(e.target.value ? parseInt(e.target.value, 10) : "")
                    }
                    className="h-9 text-sm"
                  />
                </div>

                <div>
                  <Label className="text-xs font-semibold mb-1 block">
                    State / Union Territory
                  </Label>
                  <Select value={state} onValueChange={setState}>
                    <SelectTrigger className="h-9 text-xs">
                      <SelectValue placeholder="Select state" />
                    </SelectTrigger>
                    <SelectContent className="max-h-60">
                      {INDIAN_STATES.map((st) => (
                        <SelectItem key={st} value={st} className="text-xs">
                          {st}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label className="text-xs font-semibold mb-1.5 block">Gender</Label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {["Male", "Female", "Other", "Prefer not to say"].map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setGender(g)}
                      className={cn(
                        "py-2 px-3 rounded-lg border text-xs font-semibold transition text-center",
                        gender === g
                          ? "bg-navy-700 text-white border-navy-700 shadow-xs"
                          : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                      )}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-xs font-semibold mb-1 block">
                  Primary Occupation
                </Label>
                <Select value={occupation} onValueChange={setOccupation}>
                  <SelectTrigger className="h-9 text-xs">
                    <SelectValue placeholder="Select occupation" />
                  </SelectTrigger>
                  <SelectContent className="max-h-60">
                    {OCCUPATION_OPTIONS.map((occ) => (
                      <SelectItem key={occ} value={occ} className="text-xs">
                        {occ}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between border-t pt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setStep(1)}
                className="text-xs gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </Button>
              <Button
                onClick={() => setStep(3)}
                className="bg-navy-700 text-white text-xs gap-1.5 h-9 px-5"
              >
                <span>Continue to Financials</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </CardFooter>
          </div>
        )}

        {/* STEP 3: Financial Information */}
        {step === 3 && (
          <div>
            <CardHeader>
              <CardTitle className="text-lg">Step 3: Household Financial Information</CardTitle>
              <CardDescription className="text-xs">
                Most government welfare initiatives have income ceilings or prioritize low-income households.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="income-input" className="text-xs font-semibold mb-1 block">
                  Annual Household Income (₹ INR)
                </Label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-slate-500 font-bold text-sm">
                    ₹
                  </span>
                  <Input
                    id="income-input"
                    type="number"
                    min={0}
                    step={10000}
                    placeholder="e.g. 250000"
                    value={annualIncome}
                    onChange={(e) =>
                      setAnnualIncome(
                        e.target.value ? parseInt(e.target.value, 10) : ""
                      )
                    }
                    className="pl-8 h-10 text-sm"
                  />
                </div>
                <span className="text-[11px] text-muted-foreground mt-1 block">
                  Total gross income of all family members combined per financial year.
                </span>
              </div>

              <div>
                <Label className="text-xs font-semibold mb-1.5 block">
                  Do you or your family hold a valid BPL / Antyodaya / Priority Ration Card?
                </Label>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setIsBPL(true)}
                    className={cn(
                      "flex-1 py-2.5 px-4 rounded-lg border text-xs font-semibold transition text-center",
                      isBPL
                        ? "bg-navy-700 text-white border-navy-700 shadow-xs"
                        : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                    )}
                  >
                    Yes, BPL / Ration Card Holder
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsBPL(false)}
                    className={cn(
                      "flex-1 py-2.5 px-4 rounded-lg border text-xs font-semibold transition text-center",
                      isBPL === false
                        ? "bg-navy-700 text-white border-navy-700 shadow-xs"
                        : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                    )}
                  >
                    No / Non-BPL
                  </button>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between border-t pt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setStep(2)}
                className="text-xs gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </Button>
              <Button
                onClick={() => setStep(4)}
                className="bg-navy-700 text-white text-xs gap-1.5 h-9 px-5"
              >
                <span>Continue to Specifics</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </CardFooter>
          </div>
        )}

        {/* STEP 4: Additional Details */}
        {step === 4 && (
          <div>
            <CardHeader>
              <CardTitle className="text-lg">Step 4: Additional Criteria Details</CardTitle>
              <CardDescription className="text-xs">
                Provide contextual details to refine criteria for student scholarships, farmer land requirements, or MSME loans.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Student Checkbox */}
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold text-navy-950 block">
                      Enrolled Student Status
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      Enable if applicant is currently enrolled in school, college, or university.
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={isStudent}
                    onChange={(e) => setIsStudent(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-navy-700 focus:ring-navy-600"
                  />
                </div>
                {isStudent && (
                  <div className="pt-2">
                    <Label className="text-[11px] font-semibold block mb-1">
                      Current Course Level
                    </Label>
                    <Select value={educationLevel} onValueChange={setEducationLevel}>
                      <SelectTrigger className="h-8 text-xs bg-white">
                        <SelectValue placeholder="Select level" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Secondary (Class 9-10)">Secondary (Class 9-10)</SelectItem>
                        <SelectItem value="Higher Secondary (11-12)">Higher Secondary (11-12)</SelectItem>
                        <SelectItem value="Undergraduate">Undergraduate Degree (B.Tech/BA/B.Sc)</SelectItem>
                        <SelectItem value="Postgraduate">Postgraduate / Doctorate</SelectItem>
                        <SelectItem value="Vocational / ITI">Vocational / ITI / Diploma</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>

              {/* Farmer Land details */}
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
                <Label htmlFor="land-acres" className="text-xs font-semibold text-navy-950 block">
                  Agricultural Land Holding (Acres) — for Farmers
                </Label>
                <Input
                  id="land-acres"
                  type="number"
                  step={0.1}
                  placeholder="e.g. 2.5 (leave empty if non-farmer or landless)"
                  value={landHoldingAcres}
                  onChange={(e) =>
                    setLandHoldingAcres(
                      e.target.value ? parseFloat(e.target.value) : ""
                    )
                  }
                  className="h-9 text-xs bg-white"
                />
              </div>

              {/* Business Registration */}
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-navy-950 block">
                    Udyam / MSME Business Registration
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    Do you possess an active MSME, GST, or shop registration?
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={hasBusinessRegistration}
                  onChange={(e) => setHasBusinessRegistration(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-navy-700 focus:ring-navy-600"
                />
              </div>
            </CardContent>
            <CardFooter className="flex justify-between border-t pt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setStep(3)}
                className="text-xs gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Back
              </Button>
              <Button
                onClick={handleRunAssessment}
                disabled={isLoading}
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs gap-1.5 h-9 px-6 font-semibold"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Evaluating Against Rules...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Run Eligibility Check</span>
                  </>
                )}
              </Button>
              {error && <p role="alert" className="text-xs text-red-700">{error}</p>}
            </CardFooter>
          </div>
        )}

        {/* STEP 5: Results View */}
        {step === 5 && results && (
          <div>
            <CardHeader className="border-b pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <Badge variant="indigo" className="mb-1 text-[11px]">
                    Assessment Complete
                  </Badge>
                  <CardTitle className="text-xl text-navy-950 font-bold">
                    Eligibility Analysis Report
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Evaluated profile for: {state} • Age {age} • {occupation} • Income ₹{annualIncome}
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setStep(1)}
                  className="text-xs gap-1 border-slate-300"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Test Another Profile
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-6 pt-6">
              {results.map((res, index) => (
                <div
                  key={index}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition hover:shadow-md"
                >
                  {/* Scheme Header Row */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3 border-b border-slate-100">
                    <div>
                      <h3 className="text-base font-bold text-navy-950">
                        {res.scheme.name}
                      </h3>
                      <p className="text-xs text-slate-600 mt-1">
                        {res.scheme.description}
                      </p>
                    </div>
                    <div className="shrink-0">{getStatusBadge(res.status)}</div>
                  </div>

                  {/* Conditions Breakdown Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
                    {/* Satisfied */}
                    <div className="rounded-lg bg-emerald-50/70 border border-emerald-200 p-3">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-900 mb-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>Satisfied Conditions ({res.satisfied_conditions.length})</span>
                      </div>
                      {res.satisfied_conditions.length > 0 ? (
                        <ul className="space-y-1 text-xs text-emerald-800">
                          {res.satisfied_conditions.map((sc, i) => (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="text-emerald-600 font-bold">✓</span>
                              <span>{sc}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-[11px] text-slate-500 italic">None recorded</p>
                      )}
                    </div>

                    {/* Unsatisfied */}
                    <div className="rounded-lg bg-red-50/70 border border-red-200 p-3">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-red-900 mb-2">
                        <XCircle className="w-4 h-4 text-red-600" />
                        <span>Unmet Conditions ({res.unsatisfied_conditions.length})</span>
                      </div>
                      {res.unsatisfied_conditions.length > 0 ? (
                        <ul className="space-y-1 text-xs text-red-800">
                          {res.unsatisfied_conditions.map((uc, i) => (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="text-red-600 font-bold">✗</span>
                              <span>{uc}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-[11px] text-emerald-700 italic">No disqualifying criteria found!</p>
                      )}
                    </div>
                  </div>

                  {/* Required Documents */}
                  {res.required_documents && res.required_documents.length > 0 && (
                    <div className="mb-4">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-navy-900 mb-1.5">
                        <FileCheck2 className="w-4 h-4 text-navy-700" />
                        <span>Required Documents to Prepare:</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {res.required_documents.map((doc, idx) => (
                          <Badge
                            key={idx}
                            variant="secondary"
                            className="bg-slate-100 text-slate-800 text-xs py-0.5 px-2"
                          >
                            {doc}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Application Steps */}
                  {res.application_steps && res.application_steps.length > 0 && (
                    <div className="mb-4 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-navy-900 mb-2">
                        <ListChecks className="w-4 h-4 text-indigo-600" />
                        <span>Step-by-Step Application Procedure:</span>
                      </div>
                      <ol className="space-y-1.5 text-xs text-slate-700 list-decimal list-inside">
                        {res.application_steps.map((st, idx) => (
                          <li key={idx} className="leading-relaxed">
                            {st}
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}

                  {/* Official Portal Link & Actions */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
                    <p className="text-[11px] text-slate-500 italic max-w-md">
                      ⚠️ {res.disclaimer}
                    </p>

                    {res.scheme.official_url && (
                      <a
                        href={res.scheme.official_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Button
                          size="sm"
                          className="bg-navy-700 hover:bg-navy-800 text-white text-xs gap-1.5"
                        >
                          <span>Official Portal</span>
                          <ExternalLink className="w-3 h-3" />
                        </Button>
                      </a>
                    )}
                  </div>
                </div>
              ))}
              {results.length === 0 && (
                <p className="rounded-lg bg-amber-50 p-4 text-sm text-amber-900" role="status">
                  No schemes matched the supplied filters. Try a broader scheme search or check the official portal.
                </p>
              )}
            </CardContent>
          </div>
        )}
      </Card>
    </div>
  );
}

export default function EligibilityPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-xs text-muted-foreground">
          Loading Eligibility Assistant...
        </div>
      }
    >
      <EligibilityWizard />
    </Suspense>
  );
}
