"use client";

import { useEffect } from "react";
import { Card } from "@/components/ui/card";
import { useAudioEngine } from "@/hooks/useAudioEngine";
import { useSubtitleSync } from "@/hooks/useSubtitleSync";
import { PlaybackControls } from "./PlaybackControls";
import { LanguageSwitch } from "./LanguageSwitch";
import { SubtitlePanel } from "./SubtitlePanel";
import { getAudioUrl } from "@/lib/api";
import type { Segment } from "@/lib/types";

interface Props {
  jobId: string;
  segments: Segment[];
}

export function InterviewPlayer({ jobId, segments }: Props) {
  const originalUrl = getAudioUrl(jobId, "original");
  const translatedUrl = getAudioUrl(jobId, "translated");

  const engine = useAudioEngine(originalUrl, translatedUrl);
  const activeIndex = useSubtitleSync(segments, engine.currentTime);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      switch (e.code) {
        case "Space":
          e.preventDefault();
          engine.togglePlay();
          break;
        case "KeyL":
          engine.switchLanguage(engine.language === "en" ? "es" : "en");
          break;
        case "ArrowLeft":
          e.preventDefault();
          engine.seek(Math.max(0, engine.currentTime - 5));
          break;
        case "ArrowRight":
          e.preventDefault();
          engine.seek(Math.min(engine.duration, engine.currentTime + 5));
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [engine]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Player controls */}
      <div className="lg:col-span-2 space-y-4">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Reproductor</h2>
            <LanguageSwitch language={engine.language} onChange={engine.switchLanguage} />
          </div>
          <PlaybackControls
            isPlaying={engine.isPlaying}
            currentTime={engine.currentTime}
            duration={engine.duration}
            volume={engine.volume}
            onTogglePlay={engine.togglePlay}
            onSeek={engine.seek}
            onVolumeChange={engine.setVolume}
          />
          <p className="mt-3 text-xs text-gray-400">
            Atajos: Espacio = play/pausa, L = cambiar idioma, &larr; &rarr; = saltar 5s
          </p>
        </Card>
      </div>

      {/* Subtitles */}
      <div className="lg:col-span-1">
        <Card className="p-4">
          <h3 className="text-sm font-semibold mb-3">
            Subtítulos ({engine.language === "en" ? "Inglés" : "Español"})
          </h3>
          <SubtitlePanel
            segments={segments}
            language={engine.language}
            activeIndex={activeIndex}
            onSeek={engine.seek}
          />
        </Card>
      </div>
    </div>
  );
}
