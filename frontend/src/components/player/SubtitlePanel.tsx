"use client";

import { useRef, useEffect } from "react";
import { SubtitleLine } from "./SubtitleLine";
import type { Language, Segment } from "@/lib/types";

interface Props {
  segments: Segment[];
  language: Language;
  activeIndex: number;
  onSeek: (time: number) => void;
}

export function SubtitlePanel({ segments, language, activeIndex, onSeek }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (activeRef.current) {
      activeRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [activeIndex]);

  return (
    <div ref={containerRef} className="h-[400px] overflow-y-auto space-y-1 pr-2">
      {segments.map((seg, i) => (
        <div key={i} ref={i === activeIndex ? activeRef : undefined}>
          <SubtitleLine
            segment={seg}
            language={language}
            isActive={i === activeIndex}
            onClick={() => onSeek(seg.start)}
          />
        </div>
      ))}
      {segments.length === 0 && (
        <p className="text-sm text-gray-400 text-center py-8">Sin segmentos disponibles</p>
      )}
    </div>
  );
}
