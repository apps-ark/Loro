import type { Segment } from "./types";

/**
 * Map a playback position from one language timeline to another.
 *
 * Within a segment, maps proportionally (same fraction of the segment).
 * In gaps between segments, interpolates linearly between adjacent segment boundaries.
 * Falls back to `currentTime` if ES timestamps are not available.
 */
export function mapTime(
  currentTime: number,
  fromLang: "en" | "es",
  toLang: "en" | "es",
  segments: Segment[],
): number {
  if (fromLang === toLang) return currentTime;
  if (segments.length === 0) return currentTime;

  // Check if ES timeline data is available
  const hasEsTimeline = segments.some((s) => s.start_es != null && s.end_es != null);
  if (!hasEsTimeline) return currentTime;

  const getStart = (seg: Segment, lang: "en" | "es") =>
    lang === "es" && seg.start_es != null ? seg.start_es : seg.start;
  const getEnd = (seg: Segment, lang: "en" | "es") =>
    lang === "es" && seg.end_es != null ? seg.end_es : seg.end;

  // Check if inside a segment
  for (const seg of segments) {
    const fromStart = getStart(seg, fromLang);
    const fromEnd = getEnd(seg, fromLang);

    if (currentTime >= fromStart && currentTime <= fromEnd) {
      const fromDuration = fromEnd - fromStart;
      const fraction = fromDuration > 0 ? (currentTime - fromStart) / fromDuration : 0;

      const toStart = getStart(seg, toLang);
      const toEnd = getEnd(seg, toLang);
      return toStart + fraction * (toEnd - toStart);
    }
  }

  // Before first segment
  const firstFrom = getStart(segments[0], fromLang);
  if (currentTime < firstFrom) {
    const firstTo = getStart(segments[0], toLang);
    // Scale proportionally in the leading gap
    if (firstFrom > 0) {
      return (currentTime / firstFrom) * firstTo;
    }
    return currentTime;
  }

  // After last segment
  const lastSeg = segments[segments.length - 1];
  const lastFromEnd = getEnd(lastSeg, fromLang);
  if (currentTime > lastFromEnd) {
    const lastToEnd = getEnd(lastSeg, toLang);
    const overflow = currentTime - lastFromEnd;
    return lastToEnd + overflow;
  }

  // In a gap between two segments — interpolate linearly
  for (let i = 0; i < segments.length - 1; i++) {
    const gapFromStart = getEnd(segments[i], fromLang);
    const gapFromEnd = getStart(segments[i + 1], fromLang);

    if (currentTime >= gapFromStart && currentTime <= gapFromEnd) {
      const gapDuration = gapFromEnd - gapFromStart;
      const fraction = gapDuration > 0 ? (currentTime - gapFromStart) / gapDuration : 0;

      const gapToStart = getEnd(segments[i], toLang);
      const gapToEnd = getStart(segments[i + 1], toLang);
      return gapToStart + fraction * (gapToEnd - gapToStart);
    }
  }

  // Fallback
  return currentTime;
}
