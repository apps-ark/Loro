"""Render step: stitch TTS segments on timeline and export WAV/MP3."""

from pathlib import Path

import numpy as np
import soundfile as sf

from src.pipeline.base import PipelineStep, console
from src.utils.audio import (
    export_mp3,
    normalize_lufs,
    resample,
    save_wav,
    time_stretch,
)
from src.utils.io import read_json, write_json


class RenderStep(PipelineStep):
    name = "render"
    output_files = ["rendered.wav", "timeline_map.json"]

    def execute(self, input_audio: str, **kwargs):
        cfg = self.config["render"]
        sr = cfg.get("sample_rate", 44100)
        tts_sr = cfg.get("tts_sample_rate", 22050)
        crossfade_ms = cfg.get("crossfade_ms", 50)
        crossfade_samples = int(crossfade_ms / 1000 * sr)
        stretch_min = cfg.get("stretch_min", 0.85)
        stretch_max = cfg.get("stretch_max", 1.15)

        # Load TTS manifest
        manifest = read_json(self.workdir / "tts_manifest.json")
        segments = manifest["segments"]

        if not segments:
            console.print("    [yellow]No segments to render[/yellow]")
            return

        # ── Phase 1: compute ES durations with soft stretch ──────────────
        seg_audio = []  # list of (np.ndarray, float) = (audio_at_sr, dur_es)
        for seg in segments:
            tts_file = seg.get("tts_file")
            if not tts_file:
                seg_audio.append(None)
                continue

            tts_path = self.workdir / tts_file
            if not tts_path.exists():
                console.print(f"    [yellow]Missing TTS file: {tts_file}[/yellow]")
                seg_audio.append(None)
                continue

            # Load & resample
            tts_data, file_sr = sf.read(str(tts_path), dtype="float32")
            if file_sr != sr:
                tts_data = resample(tts_data, file_sr, sr)

            target_duration = seg["end"] - seg["start"]
            current_duration = len(tts_data) / sr

            if current_duration <= 0:
                seg_audio.append(None)
                continue

            rate = current_duration / target_duration

            if stretch_min <= rate <= stretch_max:
                # Stretch fits — apply it (audio will match EN duration)
                tts_data = time_stretch(
                    tts_data, sr, target_duration,
                    min_rate=stretch_min, max_rate=stretch_max,
                )
                dur_es = target_duration
            else:
                # Rate outside range — apply soft stretch up to the limit only
                clamped_rate = max(stretch_min, min(stretch_max, rate))
                soft_target = current_duration / clamped_rate
                tts_data = time_stretch(
                    tts_data, sr, soft_target,
                    min_rate=stretch_min, max_rate=stretch_max,
                )
                dur_es = len(tts_data) / sr

            seg_audio.append((tts_data, dur_es))

        # ── Phase 2: build ES timeline with sequential placement ─────────
        timeline_map_segments = []
        cursor_es = segments[0]["start"]  # same initial offset

        for i, seg in enumerate(segments):
            entry = {
                "start_en": round(seg["start"], 3),
                "end_en": round(seg["end"], 3),
                "speaker": seg.get("speaker", "UNKNOWN"),
            }

            if seg_audio[i] is not None:
                _, dur_es = seg_audio[i]
                start_es = cursor_es
                end_es = cursor_es + dur_es
                entry["start_es"] = round(start_es, 3)
                entry["end_es"] = round(end_es, 3)

                # Advance cursor: dur_es + same gap as EN to next segment
                if i + 1 < len(segments):
                    gap_en = segments[i + 1]["start"] - seg["end"]
                    cursor_es = end_es + gap_en
                else:
                    cursor_es = end_es
            else:
                # No TTS — keep EN times as fallback
                entry["start_es"] = round(seg["start"], 3)
                entry["end_es"] = round(seg["end"], 3)
                if i + 1 < len(segments):
                    gap_en = segments[i + 1]["start"] - seg["end"]
                    cursor_es = entry["end_es"] + gap_en
                else:
                    cursor_es = entry["end_es"]

            timeline_map_segments.append(entry)

        # Compute total durations
        max_end_en = max(seg["end"] for seg in segments)
        max_end_es = max(e["end_es"] for e in timeline_map_segments)

        # ── Phase 3: render ES audio onto timeline ───────────────────────
        total_samples = int(max_end_es * sr) + sr  # +1s padding
        timeline = np.zeros(total_samples, dtype=np.float32)

        console.print(
            f"    Rendering {len(segments)} segments onto "
            f"{max_end_es:.1f}s ES timeline (EN: {max_end_en:.1f}s)"
        )

        rendered_count = 0
        for i, seg in enumerate(segments):
            if seg_audio[i] is None:
                continue

            tts_data, _ = seg_audio[i]
            start_es = timeline_map_segments[i]["start_es"]
            start_sample = int(start_es * sr)
            end_sample = start_sample + len(tts_data)

            if end_sample > len(timeline):
                extra = np.zeros(end_sample - len(timeline) + sr, dtype=np.float32)
                timeline = np.concatenate([timeline, extra])

            # Crossfade at boundaries
            if crossfade_samples > 0 and start_sample > 0:
                fade_len = min(crossfade_samples, len(tts_data))
                fade_in = np.linspace(0, 1, fade_len, dtype=np.float32)
                fade_out = np.linspace(1, 0, fade_len, dtype=np.float32)

                overlap_start = max(0, start_sample - fade_len)
                actual_fade = start_sample - overlap_start
                if actual_fade > 0:
                    timeline[overlap_start:start_sample] *= fade_out[:actual_fade]

                tts_data[:fade_len] *= fade_in

            timeline[start_sample:start_sample + len(tts_data)] += tts_data
            rendered_count += 1

        # Trim trailing silence
        last_nonzero = np.max(np.nonzero(timeline)) if np.any(timeline) else len(timeline)
        timeline = timeline[: last_nonzero + sr]  # Keep 1s trailing

        # Normalize LUFS
        target_lufs = cfg.get("target_lufs", -16.0)
        try:
            timeline = normalize_lufs(timeline, sr, target_lufs)
        except Exception as e:
            console.print(f"    [yellow]LUFS normalization skipped: {e}[/yellow]")

        # Clip to prevent distortion
        timeline = np.clip(timeline, -1.0, 1.0)

        # Save WAV
        wav_path = self.workdir / "rendered.wav"
        save_wav(timeline, wav_path, sr)
        console.print(f"    Saved rendered.wav ({len(timeline) / sr:.1f}s, {sr}Hz)")

        # Export MP3
        if cfg.get("export_mp3", True):
            mp3_path = self.workdir / "rendered.mp3"
            try:
                export_mp3(wav_path, mp3_path, quality=cfg.get("mp3_quality", 2))
                console.print(f"    Saved rendered.mp3")
            except Exception as e:
                console.print(f"    [red]MP3 export failed: {e}[/red]")

        # ── Phase 4: save timeline map ───────────────────────────────────
        timeline_map = {
            "segments": timeline_map_segments,
            "duration_en": round(max_end_en, 3),
            "duration_es": round(max_end_es, 3),
        }
        write_json(timeline_map, self.workdir / "timeline_map.json")
        console.print(f"    Saved timeline_map.json ({len(timeline_map_segments)} segments)")

        console.print(f"    Rendered {rendered_count}/{len(segments)} segments")
