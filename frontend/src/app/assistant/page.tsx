"use client";

import React, { useState, useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import { useVoice } from "@/hooks/useVoice";
import { useLanguage } from "@/context/LanguageContext";
import { SUGGESTED_QUESTIONS } from "@/lib/constants";
import { api, DocumentUploadResponse } from "@/lib/api";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { VoiceControl } from "@/components/chat/VoiceControl";
import { AgentSteps } from "@/components/ui/AgentSteps";
import { LanguageSelector } from "@/components/ui/LanguageSelector";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Bot,
  Trash2,
  Activity,
  UploadCloud,
  FileText,
  Sparkles,
  HelpCircle,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Mic,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function AssistantPage() {
  const { language, setLanguage } = useLanguage();
  const {
    messages,
    isLoading,
    error,
    sessionId,
    agentSteps,
    sendMessage,
    clearHistory,
    retryLastMessage,
  } = useChat(language);

  const {
    isListening,
    isPlaying,
    transcript,
    error: voiceError,
    startListening,
    stopListening,
    playAudio,
    stopAudio,
    resetTranscript,
  } = useVoice(language);

  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [docModalOpen, setDocModalOpen] = useState(false);
  const [voiceModalOpen, setVoiceModalOpen] = useState(false);
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);
  const [uploadedDoc, setUploadedDoc] = useState<DocumentUploadResponse | null>(null);
  const [docUploadError, setDocUploadError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Check backend health on mount
  useEffect(() => {
    let mounted = true;
    api
      .healthCheck()
      .then(() => {
        if (mounted) setBackendStatus("online");
      })
      .catch(() => {
        if (mounted) setBackendStatus("offline");
      });
    return () => {
      mounted = false;
    };
  }, []);

  // Auto-scroll chat to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentSteps, isLoading]);

  // When speech transcript completes, if listening stops, allow user to send
  const handleVoiceSend = () => {
    if (transcript.trim()) {
      sendMessage(transcript.trim(), language, undefined, uploadedDoc?.document_id);
      stopListening();
      resetTranscript();
      setVoiceModalOpen(false);
    }
  };

  // Document upload handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      setDocUploadError("Only PDF files are supported.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setDocUploadError("File size exceeds 20MB limit.");
      return;
    }

    setIsUploadingDoc(true);
    setDocUploadError(null);
    try {
      const response = await api.uploadDocument(file);
      setUploadedDoc(response);
      setDocModalOpen(false);
      // Notify in chat that document is loaded
      sendMessage(
        `I have uploaded document: "${response.filename}". Can you summarize the key benefits and who is eligible?`,
        language,
        undefined,
        response.document_id
      );
    } catch (err: unknown) {
      console.error("Document upload error:", err);
      setDocUploadError(
        err instanceof Error ? err.message : "Failed to upload and parse document."
      );
    } finally {
      setIsUploadingDoc(false);
    }
  };

  const currentSuggestions =
    SUGGESTED_QUESTIONS[language] || SUGGESTED_QUESTIONS["en"];

  const welcomeTexts = {
    en: "Namaste! I am JanSahayak AI. Ask me anything about Indian government schemes, subsidies, pensions, and welfare benefits.",
    hi: "नमस्ते! मैं जनसहायक एआई हूँ। मुझसे भारत सरकार की योजनाओं, सब्सिडी, पेंशन और कल्याणकारी लाभों के बारे में कुछ भी पूछें।",
    te: "నమస్కారం! నేను జనసహాయక్ AI. భారత ప్రభుత్వ పథకాలు, సబ్సిడీలు, పెన్షన్లు మరియు సంక్షేమ ప్రయోజనాల గురించి నన్ను ఏదైనా అడగండి.",
  };

  return (
    <div className="flex-1 flex flex-col md:flex-row h-[calc(100vh-4rem)] overflow-hidden bg-slate-50">
      {/* Desktop / Mobile Collapsible Sidebar */}
      <aside
        className={cn(
          "border-r border-slate-200 bg-white flex flex-col justify-between transition-all duration-300 z-20 shrink-0",
          sidebarOpen ? "w-full md:w-80 lg:w-88" : "w-0 hidden md:flex md:w-0 overflow-hidden"
        )}
      >
        <div className="p-4 flex flex-col h-full overflow-y-auto space-y-5">
          {/* Top Sidebar Header */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-navy-700 text-white flex items-center justify-center font-bold">
                <Bot className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-navy-950">
                  Assistant Settings
                </h3>
                <span className="text-[10px] text-muted-foreground font-mono">
                  Session: {sessionId.substring(0, 14)}...
                </span>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="md:hidden h-8 w-8"
              onClick={() => setSidebarOpen(false)}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>

          {/* Backend Status Indicator */}
          <div className="rounded-lg bg-slate-50 border border-slate-200 p-2.5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-navy-600" />
              <span className="font-semibold text-slate-700">API Connection</span>
            </div>
            {backendStatus === "online" && (
              <Badge variant="success" className="text-[10px] py-0 px-2 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live (FastAPI)
              </Badge>
            )}
            {backendStatus === "offline" && (
              <Badge variant="destructive" className="text-[10px] py-0 px-2 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                Offline
              </Badge>
            )}
            {backendStatus === "checking" && (
              <Badge variant="secondary" className="text-[10px] py-0 px-2">
                Checking...
              </Badge>
            )}
          </div>

          {/* Language Selector */}
          <div>
            <label className="text-xs font-semibold text-navy-900 block mb-1.5">
              Response Language
            </label>
            <LanguageSelector className="w-full" />
          </div>

          {/* Active Attached Document Indicator if any */}
          {uploadedDoc && (
            <div className="rounded-xl border border-indigo-200 bg-indigo-50/70 p-3 text-xs">
              <div className="flex items-center justify-between font-semibold text-indigo-950 mb-1">
                <span className="flex items-center gap-1">
                  <FileText className="h-3.5 w-3.5 text-indigo-600" />
                  Active Document
                </span>
                <button
                  onClick={() => setUploadedDoc(null)}
                  className="text-indigo-600 hover:text-indigo-900 text-[10px] underline"
                >
                  Detach
                </button>
              </div>
              <p className="font-medium text-slate-800 truncate">
                {uploadedDoc.filename}
              </p>
              <span className="text-[10px] text-indigo-700">
                {uploadedDoc.page_count} pages • {uploadedDoc.language_detected || "English"}
              </span>
            </div>
          )}

          {/* Suggested Questions */}
          <div className="flex-1">
            <div className="flex items-center gap-1 text-xs font-semibold text-navy-950 mb-2">
              <HelpCircle className="h-3.5 w-3.5 text-navy-700" />
              <span>Recommended Inquiries</span>
            </div>
            <div className="space-y-1.5">
              {currentSuggestions.map((q, i) => (
                <button
                  key={i}
                  disabled={isLoading}
                  onClick={() => {
                    sendMessage(q, language, undefined, uploadedDoc?.document_id);
                    if (window.innerWidth < 768) setSidebarOpen(false);
                  }}
                  className="w-full text-left text-xs p-2 rounded-lg border border-slate-100 bg-slate-50/60 hover:bg-navy-50 hover:border-navy-200 text-slate-700 transition font-normal active:scale-[0.99] disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Action buttons in sidebar */}
          <div className="pt-3 border-t border-slate-100 flex flex-col gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDocModalOpen(true)}
              className="w-full justify-start text-xs text-navy-900 border-navy-200 hover:bg-navy-50"
            >
              <UploadCloud className="h-3.5 w-3.5 mr-2 text-navy-700" />
              Upload PDF Circular
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={clearHistory}
              disabled={messages.length === 0}
              className="w-full justify-start text-xs text-slate-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-3.5 w-3.5 mr-2 text-slate-400" />
              Clear Conversation
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Chat Workspace */}
      <section className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50 relative">
        {/* Mobile top toggle bar */}
        <div className="md:hidden flex items-center justify-between px-4 py-2 bg-white border-b border-slate-200">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(true)}
            className="text-xs text-navy-800"
          >
            <ChevronRight className="h-4 w-4 mr-1" />
            Sidebar & Options
          </Button>
          <LanguageSelector />
        </div>

        {/* Chat History Viewport */}
        <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8 space-y-4">
          {/* Welcome Card if no messages yet */}
          {messages.length === 0 && (
            <div className="max-w-2xl mx-auto my-8 p-6 rounded-2xl bg-white border border-slate-200 shadow-sm text-center">
              <div className="h-14 w-14 rounded-2xl bg-gradient-to-tr from-navy-900 to-indigo-700 text-white flex items-center justify-center mx-auto mb-4 shadow-md">
                <ShieldCheck className="h-8 w-8 text-indigo-200" />
              </div>
              <h2 className="text-xl font-bold text-navy-950 mb-2">
                JanSahayak AI Scheme Assistant
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed max-w-lg mx-auto mb-6">
                {welcomeTexts[language]}
              </p>

              <div className="text-left">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-3 text-center">
                  Select a topic to start:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {currentSuggestions.slice(0, 4).map((sq, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(sq, language)}
                      className="p-3 text-left rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-navy-50 hover:border-navy-300 text-xs text-navy-900 font-medium transition"
                    >
                      💡 {sq}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Active Messages */}
          {messages.map((msg, index) => (
            <ChatMessage
              key={index}
              message={msg}
              onSelectSuggestion={(s) => sendMessage(s, language, undefined, uploadedDoc?.document_id)}
              onPlayAudio={(url, text, lang) => playAudio(url, text, lang)}
              isPlayingAudio={isPlaying}
            />
          ))}

          {/* Agent Steps / Reasoning Activity while Loading */}
          {isLoading && agentSteps.length > 0 && (
            <div className="max-w-[85%] md:max-w-[75%] my-2">
              <AgentSteps steps={agentSteps} isLoading={true} />
            </div>
          )}

          {/* Loading Skeleton if no steps yet */}
          {isLoading && agentSteps.length === 0 && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-white border border-slate-200 shadow-xs max-w-sm">
              <Loader2 className="h-5 w-5 text-navy-700 animate-spin" />
              <span className="text-xs font-medium text-slate-600">
                Searching verified government repositories...
              </span>
            </div>
          )}

          {/* Global Error Banner with Retry */}
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 flex items-center justify-between text-xs text-red-900">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
                <span>{error}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={retryLastMessage}
                className="h-7 text-xs border-red-300 hover:bg-red-100 text-red-800 gap-1"
              >
                <RotateCcw className="h-3 w-3" />
                Retry
              </Button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input Floating Footer */}
        <div className="p-4 md:px-8 border-t border-slate-200 bg-white">
          <div className="max-w-4xl mx-auto">
            <ChatInput
              onSendMessage={(text) =>
                sendMessage(text, language, undefined, uploadedDoc?.document_id)
              }
              isLoading={isLoading}
              onOpenVoiceModal={() => setVoiceModalOpen(true)}
              onOpenDocModal={() => setDocModalOpen(true)}
              placeholder={
                language === "hi"
                  ? "किसी भी भारतीय सरकारी योजना या पात्रता के बारे में पूछें..."
                  : language === "te"
                  ? "ఏదైనా భారత ప్రభుత్వ పథకం లేదా అర్హత గురించి అడగండి..."
                  : "Ask about any Indian government scheme, eligibility, or benefit..."
              }
            />
          </div>
        </div>
      </section>

      {/* Voice Assistant Modal */}
      <Dialog open={voiceModalOpen} onOpenChange={setVoiceModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base text-navy-950 font-bold">
              <Mic className="h-5 w-5 text-navy-700" />
              Voice Query Mode
            </DialogTitle>
            <DialogDescription className="text-xs">
              Speak naturally in your selected language ({language.toUpperCase()}).
            </DialogDescription>
          </DialogHeader>

          <VoiceControl
            isListening={isListening}
            isPlaying={isPlaying}
            language={language}
            transcript={transcript}
            error={voiceError}
            onStartListening={startListening}
            onStopListening={stopListening}
            onStopAudio={stopAudio}
          />

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                stopListening();
                setVoiceModalOpen(false);
              }}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              disabled={!transcript.trim() || isListening}
              onClick={handleVoiceSend}
              className="bg-navy-700 text-white text-xs"
            >
              Submit Question
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Document Upload Modal */}
      <Dialog open={docModalOpen} onOpenChange={setDocModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base text-navy-950 font-bold">
              <UploadCloud className="h-5 w-5 text-indigo-600" />
              Upload Government Circular / Policy PDF
            </DialogTitle>
            <DialogDescription className="text-xs text-slate-600">
              Upload an official gazette, guideline, or application brochure to
              get instant clause analysis and eligibility verification.
            </DialogDescription>
          </DialogHeader>

          <div className="p-4 border-2 border-dashed border-slate-300 rounded-xl text-center hover:border-navy-500 transition">
            <FileText className="h-10 w-10 text-slate-400 mx-auto mb-2" />
            <p className="text-xs font-semibold text-navy-900 mb-1">
              Select or drag PDF file here
            </p>
            <p className="text-[11px] text-muted-foreground mb-3">
              Supported format: PDF up to 20MB
            </p>
            <input
              type="file"
              accept="application/pdf"
              id="file-upload-input"
              className="hidden"
              onChange={handleFileUpload}
              disabled={isUploadingDoc}
            />
            <label htmlFor="file-upload-input">
              <Button
                variant="outline"
                size="sm"
                asChild
                disabled={isUploadingDoc}
                className="cursor-pointer text-xs"
              >
                <span>{isUploadingDoc ? "Processing..." : "Browse Local File"}</span>
              </Button>
            </label>
          </div>

          {isUploadingDoc && (
            <div className="flex items-center justify-center gap-2 text-xs text-navy-700 py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Analyzing document clauses with AI...</span>
            </div>
          )}

          {docUploadError && (
            <div className="flex items-center gap-1.5 text-xs text-red-600 bg-red-50 p-2 rounded-lg">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{docUploadError}</span>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
