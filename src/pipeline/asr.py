"""ASR step: English transcription using WhisperX."""

import gc
from pathlib import Path

from src.device import get_device_str
from src.pipeline.base import PipelineStep, console
from src.utils.io import write_json


class ASRStep(PipelineStep):
    name = "asr"
    output_files = ["asr.json"]

    def execute(self, input_audio: str, **kwargs):
        import whisperx

        cfg = self.config["asr"]
        device = get_device_str("asr", self.config["devices"].get("asr", "auto"))
        compute_type = cfg.get("compute_type", "float32")

        console.print(f"    Model: {cfg['model_size']}, device: {device}, compute: {compute_type}")

        # Load model
        model = whisperx.load_model(
            cfg["model_size"],
            device=device,
            compute_type=compute_type,
            language=cfg.get("language", "en"),
        )

        # Transcribe
        console.print("    Transcribing...")
        audio = whisperx.load_audio(input_audio)
        result = model.transcribe(audio, batch_size=cfg.get("batch_size", 8))

        # Free transcription model memory
        del model
        gc.collect()

        # Align timestamps (word-level)
        console.print("    Aligning word timestamps...")
        align_model, align_metadata = whisperx.load_align_model(
            language_code=cfg.get("language", "en"),
            device=device,
        )
        result = whisperx.align(
            result["segments"],
            align_model,
            align_metadata,
            audio,
            device=device,
            return_char_alignments=False,
        )

        # Free alignment model memory
        del align_model, align_metadata
        gc.collect()

        # Save output
        output_path = self.workdir / "asr.json"
        output_data = {
            "language": cfg.get("language", "en"),
            "segments": result["segments"],
        }
        if "word_segments" in result:
            output_data["word_segments"] = result["word_segments"]

        write_json(output_data, output_path)
        console.print(f"    Saved {len(result['segments'])} segments to asr.json")
