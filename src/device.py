"""Device selection for each pipeline component.

Apple Silicon (MPS) compatibility:
- WhisperX/CTranslate2: NO MPS support → CPU float32
- pyannote.audio: Inestable en MPS → CPU
- NLLB-200 (transformers): MPS funciona → MPS
- Coqui XTTS v2: Se cuelga en MPS → CPU
"""

import torch

# MPS compatibility map per component
_MPS_COMPATIBLE = {
    "asr": False,
    "diarization": False,
    "translation": True,
    "tts": False,
}


def get_device(component: str, config_override: str = "auto") -> torch.device:
    """Get the appropriate torch.device for a pipeline component.

    Args:
        component: One of 'asr', 'diarization', 'translation', 'tts'.
        config_override: 'auto', 'cpu', 'cuda', or 'mps'.

    Returns:
        torch.device for the component.
    """
    if config_override != "auto":
        return torch.device(config_override)

    if torch.cuda.is_available():
        return torch.device("cuda")

    if torch.backends.mps.is_available() and _MPS_COMPATIBLE.get(component, False):
        return torch.device("mps")

    return torch.device("cpu")


def get_device_str(component: str, config_override: str = "auto") -> str:
    """Get device as string — needed for WhisperX which uses strings, not torch.device."""
    return str(get_device(component, config_override))
