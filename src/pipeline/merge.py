"""Merge step: combine ASR segments with diarization speaker labels."""

from pathlib import Path

from src.pipeline.base import PipelineStep, console
from src.utils.io import read_json, write_json


class MergeStep(PipelineStep):
    name = "merge"
    output_files = ["merged_segments.json"]

    def execute(self, **kwargs):
        cfg = self.config["merge"]

        # Load ASR and diarization results
        asr_data = read_json(self.workdir / "asr.json")
        diar_data = read_json(self.workdir / "diarization.json")

        asr_segments = asr_data["segments"]
        diar_turns = diar_data["turns"]

        # Try whisperx.assign_word_speakers if word-level data available
        merged = self._assign_speakers(asr_segments, diar_turns)

        # Post-process: merge tiny segments from same speaker
        min_dur = cfg.get("min_segment_duration", 0.5)
        merged = self._merge_tiny_segments(merged, min_dur)

        # Optional smoothing
        if cfg.get("smoothing", False):
            window = cfg.get("smoothing_window", 3)
            merged = self._smooth_speakers(merged, window)

        # Save
        output_path = self.workdir / "merged_segments.json"
        write_json({"segments": merged}, output_path)
        console.print(f"    Merged {len(merged)} segments")

    def _assign_speakers(self, asr_segments: list, diar_turns: list) -> list:
        """Assign speaker to each ASR segment based on max overlap with diarization."""
        merged = []
        for seg in asr_segments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            seg_text = seg.get("text", "").strip()

            if not seg_text:
                continue

            # Find speaker with maximum overlap
            best_speaker = "UNKNOWN"
            best_overlap = 0.0

            for turn in diar_turns:
                overlap_start = max(seg_start, turn["start"])
                overlap_end = min(seg_end, turn["end"])
                overlap = max(0.0, overlap_end - overlap_start)

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = turn["speaker"]

            merged.append({
                "start": round(seg_start, 3),
                "end": round(seg_end, 3),
                "duration": round(seg_end - seg_start, 3),
                "speaker": best_speaker,
                "text_en": seg_text,
            })

        return merged

    def _merge_tiny_segments(self, segments: list, min_duration: float) -> list:
        """Merge segments shorter than min_duration into adjacent same-speaker segments."""
        if not segments:
            return segments

        result = [segments[0]]

        for seg in segments[1:]:
            prev = result[-1]
            if (
                seg["duration"] < min_duration
                and seg["speaker"] == prev["speaker"]
            ):
                # Merge into previous
                prev["end"] = seg["end"]
                prev["duration"] = round(prev["end"] - prev["start"], 3)
                prev["text_en"] = f"{prev['text_en']} {seg['text_en']}"
            else:
                result.append(seg)

        return result

    def _smooth_speakers(self, segments: list, window: int) -> list:
        """Apply median filter smoothing to speaker labels.

        If a segment's speaker differs from the majority of its neighbors
        within the window, reassign it to the majority speaker.
        """
        if len(segments) < window:
            return segments

        speakers = [s["speaker"] for s in segments]
        smoothed = speakers.copy()
        half = window // 2

        for i in range(half, len(speakers) - half):
            neighborhood = speakers[i - half: i + half + 1]
            # Find most common speaker in window
            from collections import Counter
            counts = Counter(neighborhood)
            majority = counts.most_common(1)[0][0]
            smoothed[i] = majority

        for i, seg in enumerate(segments):
            seg["speaker"] = smoothed[i]

        return segments
