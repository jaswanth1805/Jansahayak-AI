"use client";

import React, { useState, useRef } from "react";
import { api, DocumentUploadResponse, SourceCitation, Language } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageSelector } from "@/components/ui/LanguageSelector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { SourceCitationList } from "@/components/ui/SourceCitation";
import {
  UploadCloud,
  FileText,
  Calendar,
  CheckCircle2,
  FileCheck2,
  Send,
  Loader2,
  HelpCircle,
  FileQuestion,
  AlertCircle,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface DocQuestionAnswer {
  question: string;
  answer: string;
  sources: SourceCitation[];
  timestamp: string;
}

export default function DocumentsPage() {
  const { language } = useLanguage();

  // Document management state
  const [documents, setDocuments] = useState<DocumentUploadResponse[]>([]);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);

  // Upload state
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Q&A state for active document
  const [docQueries, setDocQueries] = useState<Record<string, DocQuestionAnswer[]>>({});
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const activeDoc = documents.find((d) => d.document_id === activeDocId) || null;
  const currentHistory = activeDocId ? docQueries[activeDocId] || [] : [];

  const handleProcessFile = async (file: File) => {
    if (file.type !== "application/pdf") {
      setUploadError("Only official PDF documents are supported.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setUploadError("Document size exceeds 20MB limit.");
      return;
    }

    setUploadError(null);
    setIsUploading(true);
    setUploadProgress(25);
    let interval: ReturnType<typeof setInterval> | null = null;
    try {
      interval = setInterval(() => {
        setUploadProgress((prev) => (prev < 85 ? prev + 15 : prev));
      }, 200);

      const response = await api.uploadDocument(file);
      setUploadProgress(100);

      setDocuments((prev) => [response, ...prev]);
      setActiveDocId(response.document_id);
    } catch (err: unknown) {
      console.error("Document upload failed:", err);
      const msg = err instanceof Error ? err.message : "Failed to upload document. Please ensure backend server is running.";
      setUploadError(msg);
    } finally {
      if (interval) clearInterval(interval);
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentQuestion.trim() || !activeDocId || isQuerying) return;

    const questionText = currentQuestion.trim();
    setCurrentQuestion("");
    setIsQuerying(true);
    setQueryError(null);

    try {
      if (!activeDoc?.access_token) throw new Error("Upload this document again to restore its access token.");
      const result = await api.queryDocument(activeDocId, activeDoc.access_token, questionText, language);

      const newQA: DocQuestionAnswer = {
        question: questionText,
        answer: result.answer,
        sources: result.sources || [],
        timestamp: new Date().toISOString(),
      };

      setDocQueries((prev) => ({
        ...prev,
        [activeDocId]: [...(prev[activeDocId] || []), newQA],
      }));
    } catch (err: unknown) {
      setQueryError(err instanceof Error ? err.message : "Document query failed. Please retry.");
    } finally {
      setIsQuerying(false);
    }
  };

  const handleDeleteDocument = async () => {
    if (!activeDoc?.access_token || isDeleting || isQuerying) return;
    setIsDeleting(true);
    setUploadError(null);
    try {
      await api.deleteDocument(activeDoc.document_id, activeDoc.access_token);
      const remaining = documents.filter((doc) => doc.document_id !== activeDoc.document_id);
      setDocuments(remaining);
      setActiveDocId(remaining[0]?.document_id || null);
      setDocQueries((prev) => {
        const next = { ...prev };
        delete next[activeDoc.document_id];
        return next;
      });
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Document deletion failed.");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex-1 py-8 px-4 sm:px-8 max-w-7xl mx-auto w-full">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 mb-6 border-b border-slate-200">
        <div>
          <Badge variant="indigo" className="mb-1 text-xs">
            Government Document Analyzer
          </Badge>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-navy-950 tracking-tight">
            Official PDF Document & Circular Analyzer
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 mt-1">
            Upload complex government circulars, notifications, and application
            guidelines to get clear summaries, key dates, and ask direct questions.
          </p>
        </div>

      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Upload Area & Document Switcher (4 cols) */}
        <div className="lg:col-span-4 space-y-5">
          {/* Upload Drop Zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={cn(
              "rounded-2xl border-2 border-dashed p-6 text-center transition-all bg-white shadow-xs",
              isDragging
                ? "border-indigo-600 bg-indigo-50/50 scale-[1.01]"
                : "border-slate-300 hover:border-navy-500",
              isUploading ? "pointer-events-none opacity-80" : ""
            )}
          >
            <UploadCloud className="h-10 w-10 text-navy-700 mx-auto mb-3" />
            <h3 className="text-sm font-bold text-navy-950 mb-1">
              Upload PDF Circular / Scheme Guidelines
            </h3>
            <p className="text-[11px] text-muted-foreground mb-4">
              Drag & drop official PDF or click to browse (Max 20MB)
            </p>

            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleProcessFile(e.target.files[0]);
                }
              }}
            />

            <Button
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="bg-navy-700 hover:bg-navy-800 text-white text-xs px-4"
            >
              {isUploading ? "Uploading & Analyzing..." : "Browse Local File"}
            </Button>

            {isUploading && (
              <div className="mt-4 space-y-1.5">
                <Progress value={uploadProgress} className="h-2" />
                <span className="text-[10px] text-slate-500 font-medium">
                  Extracting text and identifying clauses ({uploadProgress}%)
                </span>
              </div>
            )}

            {uploadError && (
              <div className="mt-3 flex items-center gap-1 text-xs text-red-600 bg-red-50 p-2 rounded-lg text-left">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}
          </div>

          {/* Uploaded Documents List */}
          {documents.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-navy-950 uppercase tracking-wider">
                  Analyzed Documents ({documents.length})
                </span>
              </div>
              <div className="space-y-2 max-h-72 overflow-y-auto">
                {documents.map((doc) => (
                  <button
                    key={doc.document_id}
                    onClick={() => setActiveDocId(doc.document_id)}
                    className={cn(
                      "w-full text-left p-3 rounded-lg border text-xs transition flex items-start gap-2.5",
                      activeDocId === doc.document_id
                        ? "bg-navy-50 border-navy-300 text-navy-950 font-semibold"
                        : "bg-white border-slate-100 hover:bg-slate-50 text-slate-700"
                    )}
                  >
                    <FileText className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                    <div className="truncate flex-1">
                      <p className="truncate">{doc.filename}</p>
                      <span className="text-[10px] text-muted-foreground font-normal">
                        {doc.page_count} pages • {doc.language_detected || "English"}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Document Details & Interactive Q&A (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {!activeDoc ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center">
              <FileQuestion className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-navy-950 mb-1">
                No Document Selected
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">
                Upload a PDF document to view extracted text and ask questions about it.
              </p>
            </div>
          ) : (
            <>
              {/* Document Overview Card */}
              <Card className="border-slate-200 bg-white shadow-xs">
                <CardHeader className="pb-3 border-b">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-indigo-600" />
                      <CardTitle className="text-lg font-bold text-navy-950 truncate max-w-md">
                        {activeDoc.filename}
                      </CardTitle>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {activeDoc.document_type && (
                        <Badge variant="outline" className="text-[10px] bg-slate-50 text-slate-700 border-slate-300">
                          {activeDoc.document_type}
                        </Badge>
                      )}
                      <Badge variant="navy" className="text-[10px]">
                        {activeDoc.page_count} Pages
                      </Badge>
                      <Badge variant="indigo" className="text-[10px]">
                        {activeDoc.language_detected || "English"}
                      </Badge>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleDeleteDocument}
                        disabled={isDeleting || isQuerying || !activeDoc.access_token}
                        className="h-7 gap-1 px-2 text-[10px] text-red-700"
                      >
                        {isDeleting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
                        Delete
                      </Button>
                    </div>
                  </div>
                  {activeDoc.extracted_text_preview && (
                    <div className="text-xs text-slate-700 bg-slate-50/80 border border-slate-200 rounded-lg p-3 mt-3 whitespace-pre-wrap font-sans leading-relaxed">
                      {activeDoc.extracted_text_preview}
                    </div>
                  )}
                </CardHeader>

                <CardContent className="pt-4 space-y-5">
                  {/* Scanned Document Notice Banner */}
                  {(activeDoc.is_scanned || activeDoc.extracted_text_preview?.includes("Scanned Image")) && (
                    <div className="rounded-xl bg-amber-50/80 border border-amber-200 p-4 flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                      <div className="text-xs space-y-1">
                        <h4 className="font-bold text-amber-950">
                          Scanned Photo / Image Document Detected
                        </h4>
                        <p className="text-amber-800 leading-relaxed">
                          This document was uploaded as a scanned image or photo without an embedded digital text layer. Machine-readable text could not be extracted directly.
                        </p>
                        <p className="text-amber-700 font-medium text-[11px]">
                          💡 <strong>Tip:</strong> Upload a text-searchable PDF (with selectable text) or add a free <code className="bg-amber-100 px-1 py-0.5 rounded text-amber-900">GEMINI_API_KEY</code> in <code className="bg-amber-100 px-1 py-0.5 rounded text-amber-900">backend/.env</code> for automatic AI Vision OCR.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Key Clauses / Summary Points */}
                  {activeDoc.key_clauses && activeDoc.key_clauses.length > 0 && (
                    <div>
                      <h4 className="text-xs font-bold text-navy-950 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        Key Identified Clauses & Overview
                      </h4>
                      <ul className="space-y-1.5 text-xs text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-200">
                        {activeDoc.key_clauses.map((clause, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="font-bold text-navy-700 shrink-0">•</span>
                            <span>{clause}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Important Dates & Eligibility Mentions Grid */}
                  {((activeDoc.important_dates && activeDoc.important_dates.length > 0) ||
                    (activeDoc.eligibility_mentions && activeDoc.eligibility_mentions.length > 0)) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Important Dates */}
                      {activeDoc.important_dates && activeDoc.important_dates.length > 0 && (
                        <div className="rounded-lg bg-indigo-50/50 border border-indigo-100 p-3">
                          <h4 className="text-xs font-bold text-indigo-950 mb-2 flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5 text-indigo-600" />
                            Important Dates & Deadlines
                          </h4>
                          <ul className="space-y-1 text-xs text-indigo-900">
                            {activeDoc.important_dates.map((date, idx) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span className="font-semibold text-indigo-600">→</span>
                                <span>{date}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Eligibility Mentions */}
                      {activeDoc.eligibility_mentions && activeDoc.eligibility_mentions.length > 0 && (
                        <div className="rounded-lg bg-emerald-50/50 border border-emerald-100 p-3">
                          <h4 className="text-xs font-bold text-emerald-950 mb-2 flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            Eligibility Mentions
                          </h4>
                          <ul className="space-y-1 text-xs text-emerald-900">
                            {activeDoc.eligibility_mentions.map((elig, idx) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span className="font-semibold text-emerald-600">✓</span>
                                <span>{elig}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Required Documents */}
                  {activeDoc.required_documents_mentioned &&
                    activeDoc.required_documents_mentioned.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold text-navy-950 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                          <FileCheck2 className="w-3.5 h-3.5 text-amber-600" />
                          Mandatory Documents Mentioned
                        </h4>
                        <div className="flex flex-wrap gap-1.5">
                          {activeDoc.required_documents_mentioned.map((doc, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="text-xs bg-amber-50/60 border-amber-200 text-slate-800"
                            >
                              {doc}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Processing Notes */}
                  {activeDoc.processing_notes && activeDoc.processing_notes.length > 0 && (
                    <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
                      <span className="font-semibold text-slate-600 block mb-1">Extraction Pipeline Notes:</span>
                      {activeDoc.processing_notes.map((note, idx) => (
                        <p key={idx} className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-400 inline-block shrink-0" />
                          <span>{note}</span>
                        </p>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Document Interactive Q&A Section */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b">
                  <div className="flex items-center gap-2">
                    <FileQuestion className="h-5 w-5 text-indigo-600" />
                    <div>
                      <h3 className="text-sm font-bold text-navy-950">
                        Ask Questions About This Document
                      </h3>
                      <p className="text-[11px] text-muted-foreground">
                        Get verified clause-by-clause answers with page numbers
                      </p>
                    </div>
                  </div>
                  <LanguageSelector />
                </div>

                {/* Input Form */}
                <form onSubmit={handleAskQuestion} className="flex gap-2">
                  <Input
                    placeholder="e.g. What is the penalty for late renewal? Who is excluded from benefits?"
                    value={currentQuestion}
                    onChange={(e) => setCurrentQuestion(e.target.value)}
                    disabled={isQuerying}
                    className="h-10 text-xs sm:text-sm"
                  />
                  <Button
                    type="submit"
                    disabled={!currentQuestion.trim() || isQuerying}
                    className="h-10 px-4 bg-navy-700 hover:bg-navy-800 text-white text-xs shrink-0 font-semibold"
                  >
                    {isQuerying ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <>
                        <span>Ask</span>
                        <Send className="w-3.5 h-3.5 ml-1.5" />
                      </>
                    )}
                  </Button>
                </form>

                {/* Q&A History for this document */}
                <div className="space-y-4 pt-2">
                  {currentHistory.map((item, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 space-y-2 text-xs"
                    >
                      <div className="font-bold text-navy-950 flex items-start gap-2">
                        <span className="text-indigo-600 font-extrabold">Q:</span>
                        <span>{item.question}</span>
                      </div>
                      <div className="text-slate-800 leading-relaxed pl-5 whitespace-pre-wrap">
                        {item.answer}
                      </div>
                      {item.sources && item.sources.length > 0 && (
                        <div className="pl-5 pt-1">
                          <SourceCitationList citations={item.sources} />
                        </div>
                      )}
                    </div>
                  ))}

                  {currentHistory.length === 0 && (
                    <div className="text-center py-6 text-xs text-slate-400">
                      No questions asked yet about this document. Try asking about eligibility or deadlines!
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
