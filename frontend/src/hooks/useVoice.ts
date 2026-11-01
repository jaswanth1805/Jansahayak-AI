"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api, Language, BACKEND_URL } from "@/lib/api";

// Web Speech API interfaces
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

interface ISpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((this: ISpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
  onerror: ((this: ISpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;
  onend: ((this: ISpeechRecognition, ev: Event) => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition?: new () => ISpeechRecognition;
    webkitSpeechRecognition?: new () => ISpeechRecognition;
  }
}

export function useVoice(language: Language = "en") {
  const [isListening, setIsListening] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSpeechSupported, setIsSpeechSupported] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<ISpeechRecognition | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const playbackIdRef = useRef(0);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  // Map language code to standard SpeechRecognition BCP-47 tag
  const getSpeechLang = useCallback((lang: Language): string => {
    switch (lang) {
      case "hi":
        return "hi-IN";
      case "te":
        return "te-IN";
      case "en":
      default:
        return "en-IN";
    }
  }, []);

  // Initialize Speech Recognition on client
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognitionConstructor =
        window.SpeechRecognition || window.webkitSpeechRecognition;

      if (SpeechRecognitionConstructor) {
        setIsSpeechSupported(true);
        const recognition = new SpeechRecognitionConstructor();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = getSpeechLang(language);

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          if (!mountedRef.current) return;
          let currentTranscript = "";
          for (let i = event.resultIndex; i < event.results.length; i++) {
            currentTranscript += event.results[i][0].transcript;
          }
          setTranscript(currentTranscript);
        };

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
          if (!mountedRef.current) return;
          console.warn("Speech recognition error:", event.error);
          setIsListening(false);
          if (event.error === "not-allowed") {
            setError("Microphone permission was denied. Please allow microphone access.");
          } else if (event.error === "no-speech") {
            // benign
          } else {
            setError(`Speech recognition error: ${event.error}`);
          }
        };

        recognition.onend = () => {
          if (mountedRef.current) setIsListening(false);
        };

        recognitionRef.current = recognition;
      } else {
        setIsSpeechSupported(false);
      }
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
        audioRef.current = null;
      }
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
      playbackIdRef.current += 1;
      utteranceRef.current = null;
      if (mountedRef.current) setIsPlaying(false);
    };
  }, [language, getSpeechLang]);

  // Update language on existing recognition instance if changed
  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = getSpeechLang(language);
    }
  }, [language, getSpeechLang]);

  const startListening = useCallback(() => {
    setError(null);
    setTranscript("");
    if (!recognitionRef.current) {
      setError("Speech recognition is not supported in this browser.");
      return;
    }
    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch (err: unknown) {
      console.error("Failed to start speech recognition:", err);
      // Sometimes it's already started
      try {
        recognitionRef.current.stop();
        recognitionRef.current.start();
        setIsListening(true);
      } catch {
        setError("Could not start speech recognition. Please try again.");
      }
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        console.error("Failed to stop speech recognition:", err);
      }
      setIsListening(false);
    }
  }, [isListening]);

  const resetTranscript = useCallback(() => {
    setTranscript("");
    setError(null);
  }, []);

  const stopAudio = useCallback(() => {
    playbackIdRef.current += 1;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current.src = "";
      audioRef.current = null;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    utteranceRef.current = null;
    if (mountedRef.current) setIsPlaying(false);
  }, []);

  const playAudio = useCallback(
    async (url: string, fallbackText?: string, langCode: Language = language) => {
      stopAudio();
      if (!url && !fallbackText) return;
      const playbackId = playbackIdRef.current;

      const fullUrl = url?.startsWith("/api/voice/audio/") ? `${BACKEND_URL}${url}` : "";

      const speakBrowserFallback = () => {
        if (typeof window !== "undefined" && "speechSynthesis" in window && fallbackText) {
          try {
            window.speechSynthesis.cancel();
            // Clean markdown syntax for speech
            const clean = fallbackText
              .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
              .replace(/https?:\/\/\S+/g, "")
              .replace(/[#*`_~>|]/g, "")
              .replace(/[💡💰🎯📄📝📋🌾🎓🔊🔍✨]/g, "")
              .replace(/\s+/g, " ")
              .trim();
            const utterance = new SpeechSynthesisUtterance(clean.slice(0, 800));
            utteranceRef.current = utterance;
            utterance.lang = getSpeechLang(langCode);
            utterance.onstart = () => {
              if (playbackId === playbackIdRef.current) setIsPlaying(true);
            };
            utterance.onend = () => {
              if (playbackId === playbackIdRef.current) {
                utteranceRef.current = null;
                setIsPlaying(false);
              }
            };
            utterance.onerror = () => {
              if (playbackId === playbackIdRef.current) {
                utteranceRef.current = null;
                setIsPlaying(false);
              }
            };
            window.speechSynthesis.resume();
            window.speechSynthesis.speak(utterance);
          } catch (e) {
            console.error("Browser speech synthesis error:", e);
            if (playbackId === playbackIdRef.current) setIsPlaying(false);
          }
        } else {
          if (playbackId === playbackIdRef.current) setIsPlaying(false);
        }
      };

      if (!fullUrl) {
        speakBrowserFallback();
        return;
      }

      try {
        const audio = new Audio(fullUrl);
        audio.preload = "auto";
        audioRef.current = audio;
        setIsPlaying(true);

        audio.onended = () => {
          if (playbackId === playbackIdRef.current) setIsPlaying(false);
        };

        audio.onerror = (e) => {
          if (playbackId !== playbackIdRef.current) return;
          console.warn("Audio file playback error, falling back to browser SpeechSynthesis:", e);
          speakBrowserFallback();
        };

        const playPromise = audio.play();
        if (playPromise !== undefined) {
          playPromise.catch((err) => {
            if (playbackId !== playbackIdRef.current) return;
            console.warn("audio.play() error or blocked by browser policy, using SpeechSynthesis:", err);
            speakBrowserFallback();
          });
        }
      } catch (err: unknown) {
        console.warn("Direct audio.play() blocked, attempting browser SpeechSynthesis:", err);
        speakBrowserFallback();
      }
    },
    [stopAudio, getSpeechLang, language]
  );

  const speakText = useCallback(
    async (text: string, lang: Language = language) => {
      try {
        const res = await api.synthesizeSpeech(text, lang);
        if (res.audio_url) {
          await playAudio(res.audio_url);
        }
      } catch (err: unknown) {
        console.error("Speech synthesis failed:", err);
        // Fallback to browser Web Speech API SpeechSynthesis if available
        if (typeof window !== "undefined" && "speechSynthesis" in window) {
          stopAudio();
          const playbackId = playbackIdRef.current;
          const utterance = new SpeechSynthesisUtterance(text);
          utteranceRef.current = utterance;
          utterance.lang = getSpeechLang(lang);
          utterance.onstart = () => { if (playbackId === playbackIdRef.current) setIsPlaying(true); };
          utterance.onend = () => { if (playbackId === playbackIdRef.current) { utteranceRef.current = null; setIsPlaying(false); } };
          utterance.onerror = () => { if (playbackId === playbackIdRef.current) { utteranceRef.current = null; setIsPlaying(false); } };
          window.speechSynthesis.speak(utterance);
        } else {
          setError("Text-to-speech could not be played.");
        }
      }
    },
    [language, getSpeechLang, playAudio, stopAudio]
  );

  return {
    isListening,
    isPlaying,
    isSpeechSupported,
    transcript,
    error,
    startListening,
    stopListening,
    resetTranscript,
    playAudio,
    stopAudio,
    speakText,
  };
}
