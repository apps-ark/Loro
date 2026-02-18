"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import type { Language } from "@/lib/types";

interface AudioEngineState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  language: Language;
  volume: number;
}

export function useAudioEngine(originalUrl: string | null, translatedUrl: string | null) {
  const audioENRef = useRef<HTMLAudioElement | null>(null);
  const audioESRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number>(0);

  const [state, setState] = useState<AudioEngineState>({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    language: "es",
    volume: 1,
  });

  // Initialize audio elements
  useEffect(() => {
    if (!originalUrl || !translatedUrl) return;

    const audioEN = new Audio(originalUrl);
    const audioES = new Audio(translatedUrl);
    audioEN.preload = "auto";
    audioES.preload = "auto";

    // ES is default active
    audioEN.volume = 0;
    audioES.volume = 1;

    audioENRef.current = audioEN;
    audioESRef.current = audioES;

    const onLoadedMetadata = () => {
      const dur = Math.max(audioEN.duration || 0, audioES.duration || 0);
      if (dur > 0) setState((s) => ({ ...s, duration: dur }));
    };

    audioEN.addEventListener("loadedmetadata", onLoadedMetadata);
    audioES.addEventListener("loadedmetadata", onLoadedMetadata);

    audioES.addEventListener("ended", () => {
      setState((s) => ({ ...s, isPlaying: false }));
    });

    return () => {
      audioEN.pause();
      audioES.pause();
      audioEN.removeEventListener("loadedmetadata", onLoadedMetadata);
      audioES.removeEventListener("loadedmetadata", onLoadedMetadata);
      audioEN.src = "";
      audioES.src = "";
      cancelAnimationFrame(rafRef.current);
    };
  }, [originalUrl, translatedUrl]);

  // Time update loop
  const updateTime = useCallback(() => {
    const active = state.language === "en" ? audioENRef.current : audioESRef.current;
    if (active) {
      setState((s) => ({ ...s, currentTime: active.currentTime }));
    }
    rafRef.current = requestAnimationFrame(updateTime);
  }, [state.language]);

  useEffect(() => {
    if (state.isPlaying) {
      rafRef.current = requestAnimationFrame(updateTime);
    } else {
      cancelAnimationFrame(rafRef.current);
    }
    return () => cancelAnimationFrame(rafRef.current);
  }, [state.isPlaying, updateTime]);

  // Drift correction every 5s
  useEffect(() => {
    if (!state.isPlaying) return;
    const interval = setInterval(() => {
      const en = audioENRef.current;
      const es = audioESRef.current;
      if (en && es) {
        const drift = Math.abs(en.currentTime - es.currentTime);
        if (drift > 0.1) {
          const active = state.language === "en" ? en : es;
          const inactive = state.language === "en" ? es : en;
          inactive.currentTime = active.currentTime;
        }
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [state.isPlaying, state.language]);

  const play = useCallback(() => {
    audioENRef.current?.play();
    audioESRef.current?.play();
    setState((s) => ({ ...s, isPlaying: true }));
  }, []);

  const pause = useCallback(() => {
    audioENRef.current?.pause();
    audioESRef.current?.pause();
    setState((s) => ({ ...s, isPlaying: false }));
  }, []);

  const togglePlay = useCallback(() => {
    if (state.isPlaying) pause();
    else play();
  }, [state.isPlaying, play, pause]);

  const seek = useCallback((time: number) => {
    if (audioENRef.current) audioENRef.current.currentTime = time;
    if (audioESRef.current) audioESRef.current.currentTime = time;
    setState((s) => ({ ...s, currentTime: time }));
  }, []);

  const switchLanguage = useCallback((lang: Language) => {
    const en = audioENRef.current;
    const es = audioESRef.current;
    if (en && es) {
      if (lang === "en") {
        en.volume = state.volume;
        es.volume = 0;
      } else {
        en.volume = 0;
        es.volume = state.volume;
      }
    }
    setState((s) => ({ ...s, language: lang }));
  }, [state.volume]);

  const setVolume = useCallback((vol: number) => {
    const active = state.language === "en" ? audioENRef.current : audioESRef.current;
    if (active) active.volume = vol;
    setState((s) => ({ ...s, volume: vol }));
  }, [state.language]);

  return {
    ...state,
    play,
    pause,
    togglePlay,
    seek,
    switchLanguage,
    setVolume,
  };
}
