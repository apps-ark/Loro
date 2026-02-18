"""TTS step: voice cloning with Coqui XTTS v2."""

import gc
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

from src.device import get_device
from src.pipeline.base import PipelineStep, console
from src.utils.audio import extract_segment, load_audio, save_wav
from src.utils.io import read_json, write_json
from src.utils.text import segment_cache_key, split_text_for_tts


class TTSStep(PipelineStep):
    name = "tts"
    output_files = ["tts_segments"]

    def outputs_exist(self) -> bool:
        """TTS outputs exist if the directory has .wav files."""
        tts_dir = self.workdir / "tts_segments"
        if not tts_dir.exists():
            return False
        return any(tts_dir.rglob("*.wav"))

    def execute(self, input_audio: str, progress_callback=None, **kwargs):
        from TTS.api import TTS

        cfg = self.config["tts"]
        device_str = str(get_device("tts", self.config["devices"].get("tts", "auto")))

        console.print(f"    Model: {cfg['model']}, device: {device_str}")

        # Load translations
        trans_data = read_json(self.workdir / "translations.json")
        segments = trans_data["segments"]

        # Extract reference clips per speaker
        refs = self._extract_reference_clips(segments, input_audio, cfg)

        # Ensure output dirs
        tts_dir = self.workdir / "tts_segments"
        speakers = set(s["speaker"] for s in segments)
        for spk in speakers:
            (tts_dir / spk).mkdir(parents=True, exist_ok=True)

        # Load TTS model
        console.print("    Loading XTTS v2...")
        tts = TTS(cfg["model"]).to(device_str)

        # Generate TTS for each segment
        total = len(segments)
        max_chars = cfg.get("max_chars_per_chunk", 350)
        manifest = []

        for i, seg in enumerate(segments):
            speaker = seg["speaker"]
            text_es = seg.get("text_es", "")

            if not text_es.strip():
                manifest.append({**seg, "tts_file": None})
                continue

            cache_key = segment_cache_key(speaker, text_es)
            out_file = tts_dir / speaker / f"seg_{i:04d}_{cache_key}.wav"

            if cfg.get("cache", True) and out_file.exists():
                console.print(f"    [{i+1}/{total}] (cached) {speaker}: {text_es[:40]}...")
                manifest.append({**seg, "tts_file": str(out_file.relative_to(self.workdir))})
                continue

            ref_wav = refs.get(speaker)
            if not ref_wav:
                console.print(f"    [{i+1}/{total}] [yellow]No ref clip for {speaker}, using silence[/yellow]")
                self._write_silence(out_file, seg["end"] - seg["start"])
                manifest.append({**seg, "tts_file": str(out_file.relative_to(self.workdir))})
                continue

            try:
                chunks = split_text_for_tts(text_es, max_chars)
                all_audio = []

                for chunk in chunks:
                    tts.tts_to_file(
                        text=chunk,
                        speaker_wav=str(ref_wav),
                        language=cfg.get("language", "es"),
                        file_path=str(out_file),
                    )
                    chunk_audio, chunk_sr = sf.read(str(out_file), dtype="float32")
                    all_audio.append(chunk_audio)

                # Concatenate chunks
                if len(all_audio) > 1:
                    combined = np.concatenate(all_audio)
                    save_wav(combined, out_file, chunk_sr)

                console.print(f"    [{i+1}/{total}] {speaker}: {text_es[:40]}...")
                manifest.append({**seg, "tts_file": str(out_file.relative_to(self.workdir))})

            except Exception as e:
                console.print(f"    [{i+1}/{total}] [red]TTS failed for segment {i}[/red]: {e}")
                self._write_silence(out_file, seg["end"] - seg["start"])
                manifest.append({**seg, "tts_file": str(out_file.relative_to(self.workdir))})

            # Emit per-segment progress
            self._emit(progress_callback, {
                "type": "step_progress",
                "step": self.name,
                "current": i + 1,
                "total": total,
            })

        # Save manifest
        write_json({"segments": manifest}, self.workdir / "tts_manifest.json")

        # Free memory
        del tts
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        console.print(f"    Generated TTS for {total} segments")

    def _extract_reference_clips(
        self, segments: list, input_audio: str, cfg: dict
    ) -> dict[str, Path]:
        """Extract the best reference clip per speaker from original audio.

        Picks the longest clean segments within ref_min/max_duration.
        """
        ref_dir = self.workdir / "speaker_refs"
        ref_dir.mkdir(exist_ok=True)

        min_dur = cfg.get("ref_min_duration", 6.0)
        max_dur = cfg.get("ref_max_duration", 30.0)

        # Group segments by speaker, sorted by duration (longest first)
        by_speaker = defaultdict(list)
        for seg in segments:
            dur = seg["end"] - seg["start"]
            if dur >= min_dur:
                by_speaker[seg["speaker"]].append(seg)

        for spk in by_speaker:
            by_speaker[spk].sort(key=lambda s: s["end"] - s["start"], reverse=True)

        refs = {}
        audio_data = load_audio(input_audio, sr=22050)  # XTTS expects 22050

        for speaker, speaker_segs in by_speaker.items():
            ref_path = ref_dir / f"{speaker}_ref.wav"
            if ref_path.exists():
                refs[speaker] = ref_path
                continue

            # Pick best segment(s) up to max_dur total
            collected_duration = 0.0
            clips = []

            for seg in speaker_segs:
                seg_dur = seg["end"] - seg["start"]
                take_dur = min(seg_dur, max_dur - collected_duration)
                if take_dur <= 0:
                    break
                clip = extract_segment(audio_data, 22050, seg["start"], seg["start"] + take_dur)
                clips.append(clip)
                collected_duration += take_dur

            if clips:
                combined = np.concatenate(clips)
                save_wav(combined, ref_path, 22050)
                refs[speaker] = ref_path
                console.print(f"    Reference clip for {speaker}: {collected_duration:.1f}s")

        return refs

    @staticmethod
    def _write_silence(path: Path, duration: float, sr: int = 22050):
        """Write a silence WAV file as fallback."""
        silence = np.zeros(int(duration * sr), dtype=np.float32)
        save_wav(silence, path, sr)
