"""Diarization step: speaker segmentation using pyannote.audio."""

import gc
import os
from pathlib import Path

import torch
import soundfile as sf

from src.device import get_device
from src.pipeline.base import PipelineStep, console
from src.utils.io import write_json


class DiarizeStep(PipelineStep):
    name = "diarize"
    output_files = ["diarization.rttm", "diarization.json"]

    def execute(self, input_audio: str, **kwargs):
        from pyannote.audio import Pipeline

        cfg = self.config["diarization"]

        # Get HF token
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            raise RuntimeError("HF_TOKEN not set. Required for pyannote models.")

        device = get_device("diarization", self.config["devices"].get("diarization", "auto"))
        console.print(f"    Model: {cfg['model']}, device: {device}")

        # Login globally so sub-dependencies also get the token
        from huggingface_hub import login
        login(token=hf_token, add_to_git_credential=False)

        # Load pipeline
        console.print("    Loading diarization pipeline...")
        pipeline = Pipeline.from_pretrained(
            cfg["model"],
            token=hf_token,
        )
        pipeline.to(device)

        # Pre-load audio as waveform tensor (torchcodec is broken with torch 2.8.0)
        console.print("    Loading audio waveform...")
        # Convert to WAV if needed (soundfile can't read MP3)
        audio_path = input_audio
        if input_audio.lower().endswith(".mp3"):
            import subprocess
            wav_path = str(self.workdir / "diarize_input.wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", input_audio, "-ac", "1", "-ar", "16000", wav_path],
                capture_output=True, check=True,
            )
            audio_path = wav_path
        waveform, sample_rate = sf.read(audio_path, dtype="float32")
        # soundfile returns (samples, channels) or (samples,) for mono
        waveform_tensor = torch.from_numpy(waveform)
        if waveform_tensor.ndim == 1:
            waveform_tensor = waveform_tensor.unsqueeze(0)  # (1, samples)
        else:
            waveform_tensor = waveform_tensor.T  # (channels, samples)
        audio_input = {"waveform": waveform_tensor, "sample_rate": sample_rate}

        # Run diarization with progress
        console.print("    Running diarization...")
        params = {}
        if cfg.get("max_speakers"):
            params["max_speakers"] = cfg["max_speakers"]
        if cfg.get("min_speakers"):
            params["min_speakers"] = cfg["min_speakers"]

        result = pipeline(audio_input, **params)

        # pyannote 4.x returns DiarizeOutput; extract the Annotation object
        if hasattr(result, "speaker_diarization"):
            diarization = result.speaker_diarization
        else:
            diarization = result

        # Export RTTM
        rttm_path = self.workdir / "diarization.rttm"
        with open(rttm_path, "w") as f:
            diarization.write_rttm(f)

        # Export JSON for easier consumption
        turns = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            turns.append({
                "start": round(turn.start, 3),
                "end": round(turn.end, 3),
                "duration": round(turn.end - turn.start, 3),
                "speaker": speaker,
            })

        json_path = self.workdir / "diarization.json"
        write_json({"turns": turns}, json_path)

        # Free memory
        del pipeline, diarization, result
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        speakers = set(t["speaker"] for t in turns)
        console.print(f"    Found {len(speakers)} speakers, {len(turns)} turns")
        console.print(f"    Saved to diarization.rttm and diarization.json")
