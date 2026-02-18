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
from src.utils.io import read_json


class RenderStep(PipelineStep):
    name = "render"
    output_files = ["rendered.wav"]

    def execute(self, input_audio: str, **kwargs):
        cfg = self.config["render"]
        sr = cfg.get("sample_rate", 44100)
        tts_sr = cfg.get("tts_sample_rate", 22050)
        crossfade_ms = cfg.get("crossfade_ms", 50)
        crossfade_samples = int(crossfade_ms / 1000 * sr)

        # Load TTS manifest
        manifest = read_json(self.workdir / "tts_manifest.json")
        segments = manifest["segments"]

        if not segments:
            console.print("    [yellow]No segments to render[/yellow]")
            return

        # Determine total duration from last segment end
        max_end = max(seg["end"] for seg in segments)
        total_samples = int(max_end * sr) + sr  # +1s padding
        timeline = np.zeros(total_samples, dtype=np.float32)

        console.print(f"    Rendering {len(segments)} segments onto {max_end:.1f}s timeline")

        rendered_count = 0
        for i, seg in enumerate(segments):
            tts_file = seg.get("tts_file")
            if not tts_file:
                continue

            tts_path = self.workdir / tts_file
            if not tts_path.exists():
                console.print(f"    [yellow]Missing TTS file: {tts_file}[/yellow]")
                continue

            # Load TTS segment
            tts_audio, file_sr = sf.read(str(tts_path), dtype="float32")

            # Resample to target SR if needed
            if file_sr != sr:
                tts_audio = resample(tts_audio, file_sr, sr)

            # Time-stretch to fit original segment duration
            target_duration = seg["end"] - seg["start"]
            stretch_min = cfg.get("stretch_min", 0.7)
            stretch_max = cfg.get("stretch_max", 1.5)

            tts_audio = time_stretch(
                tts_audio, sr, target_duration,
                min_rate=stretch_min, max_rate=stretch_max,
            )

            # Place on timeline
            start_sample = int(seg["start"] * sr)
            end_sample = start_sample + len(tts_audio)

            if end_sample > len(timeline):
                # Extend timeline if needed
                extra = np.zeros(end_sample - len(timeline) + sr, dtype=np.float32)
                timeline = np.concatenate([timeline, extra])

            # Apply crossfade at boundaries
            if crossfade_samples > 0 and start_sample > 0:
                fade_len = min(crossfade_samples, len(tts_audio))
                fade_in = np.linspace(0, 1, fade_len, dtype=np.float32)
                fade_out = np.linspace(1, 0, fade_len, dtype=np.float32)

                # Fade out existing audio at overlap point
                overlap_start = max(0, start_sample - fade_len)
                actual_fade = start_sample - overlap_start
                if actual_fade > 0:
                    timeline[overlap_start:start_sample] *= fade_out[:actual_fade]

                # Fade in new segment
                tts_audio[:fade_len] *= fade_in

            # Mix onto timeline (additive for crossfade region)
            timeline[start_sample:start_sample + len(tts_audio)] += tts_audio
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

        console.print(f"    Rendered {rendered_count}/{len(segments)} segments")
