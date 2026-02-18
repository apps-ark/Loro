"use client";

import { useMemo } from "react";
import type { Language, Segment } from "@/lib/types";

export function useSubtitleSync(
  segments: Segment[],
  currentTime: number,
  language: Language,
): number {
  return useMemo(() => {
    const getStart = (seg: Segment) =>
      language === "es" && seg.start_es != null ? seg.start_es : seg.start;
    const getEnd = (seg: Segment) =>
      language === "es" && seg.end_es != null ? seg.end_es : seg.end;

    for (let i = 0; i < segments.length; i++) {
      if (currentTime >= getStart(segments[i]) && currentTime < getEnd(segments[i])) {
        return i;
      }
    }
    // If between segments, find the closest upcoming
    for (let i = 0; i < segments.length; i++) {
      if (currentTime < getStart(segments[i])) {
        return i > 0 ? i - 1 : -1;
      }
    }
    return segments.length > 0 ? segments.length - 1 : -1;
  }, [segments, currentTime, language]);
}
