"""Diarization step: speaker segmentation using pyannote.audio."""

import gc
import os
from pathlib import Path

import torch

from src.device import get_device
from src.pipeline.base import PipelineStep, console
from src.utils.io import write_json


class DiarizeStep(PipelineStep):
    name = "diarize"
    output_files = ["diarization.rttm", "diarization.json"]

    def execute(self, input_audio: str, **kwargs):
        from pyannote.audio import Pipeline
        from pyannote.audio.pipelines.utils import hook as pyannote_hook

        cfg = self.config["diarization"]

        # Get HF token
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            raise RuntimeError("HF_TOKEN not set. Required for pyannote models.")

        device = get_device("diarization", self.config["devices"].get("diarization", "auto"))
        console.print(f"    Model: {cfg['model']}, device: {device}")

        # Load pipeline
        console.print("    Loading diarization pipeline...")
        pipeline = Pipeline.from_pretrained(
            cfg["model"],
            use_auth_token=hf_token,
        )
        pipeline.to(device)

        # Run diarization with progress
        console.print("    Running diarization...")
        params = {}
        if cfg.get("max_speakers"):
            params["max_speakers"] = cfg["max_speakers"]
        if cfg.get("min_speakers"):
            params["min_speakers"] = cfg["min_speakers"]

        diarization = pipeline(input_audio, **params)

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
        del pipeline, diarization
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        speakers = set(t["speaker"] for t in turns)
        console.print(f"    Found {len(speakers)} speakers, {len(turns)} turns")
        console.print(f"    Saved to diarization.rttm and diarization.json")
