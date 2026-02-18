"use client";

import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";

interface Props {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  onTogglePlay: () => void;
  onSeek: (time: number) => void;
  onVolumeChange: (vol: number) => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function PlaybackControls({
  isPlaying,
  currentTime,
  duration,
  volume,
  onTogglePlay,
  onSeek,
  onVolumeChange,
}: Props) {
  return (
    <div className="space-y-3">
      {/* Seek bar */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-500 w-10 text-right font-mono">
          {formatTime(currentTime)}
        </span>
        <Slider
          value={[currentTime]}
          max={duration || 100}
          step={0.1}
          onValueChange={([v]) => onSeek(v)}
          className="flex-1"
        />
        <span className="text-xs text-gray-500 w-10 font-mono">
          {formatTime(duration)}
        </span>
      </div>

      {/* Controls row */}
      <div className="flex items-center justify-between">
        <Button onClick={onTogglePlay} variant="outline" size="sm">
          {isPlaying ? "Pausa" : "Reproducir"}
        </Button>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Vol</span>
          <Slider
            value={[volume * 100]}
            max={100}
            step={1}
            onValueChange={([v]) => onVolumeChange(v / 100)}
            className="w-24"
          />
        </div>
      </div>
    </div>
  );
}
