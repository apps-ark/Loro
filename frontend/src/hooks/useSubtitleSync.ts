"use client";

import { useMemo } from "react";
import type { Segment } from "@/lib/types";

export function useSubtitleSync(segments: Segment[], currentTime: number): number {
  return useMemo(() => {
    for (let i = 0; i < segments.length; i++) {
      if (currentTime >= segments[i].start && currentTime < segments[i].end) {
        return i;
      }
    }
    // If between segments, find the closest upcoming
    for (let i = 0; i < segments.length; i++) {
      if (currentTime < segments[i].start) {
        return i > 0 ? i - 1 : -1;
      }
    }
    return segments.length > 0 ? segments.length - 1 : -1;
  }, [segments, currentTime]);
}
