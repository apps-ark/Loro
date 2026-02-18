"""Configuration loading and validation."""

import os
import shutil
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config(config_path: str = "configs/default.yaml") -> dict:
    """Load YAML configuration file."""
    path = Path(config_path)
    if not path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def apply_cli_overrides(config: dict, **kwargs) -> dict:
    """Apply CLI argument overrides to config."""
    if kwargs.get("max_speakers") is not None:
        config["diarization"]["max_speakers"] = kwargs["max_speakers"]
    if kwargs.get("asr_model") is not None:
        config["asr"]["model_size"] = kwargs["asr_model"]
    return config


def validate_environment() -> dict:
    """Validate that required tools and tokens are available.

    Returns:
        dict with validated environment info.
    """
    load_dotenv()
    errors = []

    # Check ffmpeg
    if not shutil.which("ffmpeg"):
        errors.append("ffmpeg not found in PATH. Install it: brew install ffmpeg")

    # Check HF_TOKEN
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        errors.append(
            "HF_TOKEN not set. Create a .env file with HF_TOKEN=your_token_here\n"
            "  Get your token at: https://huggingface.co/settings/tokens"
        )

    if errors:
        for err in errors:
            print(f"[ERROR] {err}")
        sys.exit(1)

    return {"hf_token": hf_token}


def ensure_workdir(workdir: str) -> Path:
    """Create workdir and subdirectories if needed."""
    path = Path(workdir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "tts_segments").mkdir(exist_ok=True)
    return path
