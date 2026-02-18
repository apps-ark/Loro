"use client";

import { useRef, useState, useCallback, useEffect, type RefObject } from "react";
import type { Language, Segment } from "@/lib/types";
import { mapTime } from "@/lib/timelineMap";

interface AudioEngineState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  language: Language;
  volume: number;
}

export function useAudioEngine(
  originalUrl: string | null,
  translatedUrl: string | null,
  segmentsRef: RefObject<Segment[]>,
) {
  const audioENRef = useRef<HTMLAudioElement | null>(null);
  const audioESRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number>(0);
  const durationENRef = useRef<number>(0);
  const durationESRef = useRef<number>(0);

  const [state, setState] = useState<AudioEngineState>({
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    language: "es",
    volume: 1,
  });

  // Keep a ref to language for use in callbacks without stale closures
  const langRef = useRef<Language>(state.language);
  langRef.current = state.language;

  // Initialize audio elements
  useEffect(() => {
    if (!originalUrl || !translatedUrl) return;

    const audioEN = new Audio(originalUrl);
    const audioES = new Audio(translatedUrl);
    audioEN.preload = "auto";
    audioES.preload = "auto";

    // Only active track plays; inactive is paused
    audioEN.volume = 0;
    audioES.volume = 1;

    audioENRef.current = audioEN;
    audioESRef.current = audioES;

    const onENMetadata = () => {
      durationENRef.current = audioEN.duration || 0;
      if (langRef.current === "en") {
        setState((s) => ({ ...s, duration: audioEN.duration || 0 }));
      }
    };

    const onESMetadata = () => {
      durationESRef.current = audioES.duration || 0;
      if (langRef.current === "es") {
        setState((s) => ({ ...s, duration: audioES.duration || 0 }));
      }
    };

    const onEnded = () => {
      setState((s) => ({ ...s, isPlaying: false }));
    };

    audioEN.addEventListener("loadedmetadata", onENMetadata);
    audioES.addEventListener("loadedmetadata", onESMetadata);
    audioEN.addEventListener("ended", onEnded);
    audioES.addEventListener("ended", onEnded);

    return () => {
      audioEN.pause();
      audioES.pause();
      audioEN.removeEventListener("loadedmetadata", onENMetadata);
      audioES.removeEventListener("loadedmetadata", onESMetadata);
      audioEN.removeEventListener("ended", onEnded);
      audioES.removeEventListener("ended", onEnded);
      audioEN.src = "";
      audioES.src = "";
      cancelAnimationFrame(rafRef.current);
    };
  }, [originalUrl, translatedUrl]);

  // Time update loop — reads from active track only
  const updateTime = useCallback(() => {
    const active = langRef.current === "en" ? audioENRef.current : audioESRef.current;
    if (active) {
      setState((s) => ({ ...s, currentTime: active.currentTime }));
    }
    rafRef.current = requestAnimationFrame(updateTime);
  }, []);

  useEffect(() => {
    if (state.isPlaying) {
      rafRef.current = requestAnimationFrame(updateTime);
    } else {
      cancelAnimationFrame(rafRef.current);
    }
    return () => cancelAnimationFrame(rafRef.current);
  }, [state.isPlaying, updateTime]);

  const play = useCallback(() => {
    const active = langRef.current === "en" ? audioENRef.current : audioESRef.current;
    active?.play();
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
    const active = langRef.current === "en" ? audioENRef.current : audioESRef.current;
    if (active) active.currentTime = time;
    setState((s) => ({ ...s, currentTime: time }));
  }, []);

  const switchLanguage = useCallback((lang: Language) => {
    const en = audioENRef.current;
    const es = audioESRef.current;
    if (!en || !es) return;

    const currentLang = langRef.current;
    if (lang === currentLang) return;

    const segments = segmentsRef.current ?? [];
    const active = currentLang === "en" ? en : es;
    const newActive = lang === "en" ? en : es;
    const currentPos = active.currentTime;

    // Map position to new timeline
    const mappedPos = mapTime(currentPos, currentLang, lang, segments);

    // Switch tracks
    active.pause();
    active.volume = 0;

    newActive.currentTime = mappedPos;
    newActive.volume = state.volume;

    const newDuration = lang === "en" ? durationENRef.current : durationESRef.current;

    if (state.isPlaying) {
      newActive.play();
    }

    setState((s) => ({
      ...s,
      language: lang,
      currentTime: mappedPos,
      duration: newDuration || s.duration,
    }));
  }, [segmentsRef, state.volume, state.isPlaying]);

  const setVolume = useCallback((vol: number) => {
    const active = langRef.current === "en" ? audioENRef.current : audioESRef.current;
    if (active) active.volume = vol;
    setState((s) => ({ ...s, volume: vol }));
  }, []);

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
