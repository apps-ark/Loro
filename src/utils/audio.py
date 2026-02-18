"""Audio loading, normalization, segmentation, and time-stretching utilities."""

import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf


def load_audio(path: str | Path, sr: int = 16000) -> np.ndarray:
    """Load audio file and resample to target sample rate.

    Uses ffmpeg for format conversion, then soundfile for reading.
    Returns mono float32 numpy array.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    # Convert to WAV via ffmpeg for broad format support
    tmp_wav = path.parent / f".tmp_{path.stem}_{sr}.wav"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(path),
                "-ar", str(sr), "-ac", "1", "-f", "wav",
                str(tmp_wav),
            ],
            capture_output=True,
            check=True,
        )
        audio, _ = sf.read(tmp_wav, dtype="float32")
    finally:
        if tmp_wav.exists():
            tmp_wav.unlink()

    return audio


def normalize_lufs(audio: np.ndarray, sr: int, target_lufs: float = -16.0) -> np.ndarray:
    """Normalize audio to target LUFS loudness."""
    import pyloudnorm as pyln

    meter = pyln.Meter(sr)
    current_lufs = meter.integrated_loudness(audio)

    if np.isinf(current_lufs):
        return audio

    return pyln.normalize.loudness(audio, current_lufs, target_lufs)


def extract_segment(audio: np.ndarray, sr: int, start: float, end: float) -> np.ndarray:
    """Extract a time segment from audio array."""
    start_sample = int(start * sr)
    end_sample = int(end * sr)
    return audio[start_sample:end_sample]


def time_stretch(audio: np.ndarray, sr: int, target_duration: float,
                 min_rate: float = 0.7, max_rate: float = 1.5) -> np.ndarray:
    """Time-stretch audio to fit a target duration.

    Uses librosa for stretching. If the required rate is outside
    [min_rate, max_rate], truncates or pads with silence instead.
    """
    current_duration = len(audio) / sr
    if current_duration <= 0:
        return np.zeros(int(target_duration * sr), dtype=np.float32)

    rate = current_duration / target_duration

    if rate < min_rate or rate > max_rate:
        # Rate too extreme — truncate or pad
        target_samples = int(target_duration * sr)
        if len(audio) >= target_samples:
            return audio[:target_samples]
        else:
            padded = np.zeros(target_samples, dtype=np.float32)
            padded[: len(audio)] = audio
            return padded

    import librosa
    stretched = librosa.effects.time_stretch(audio, rate=rate)
    # Ensure exact length
    target_samples = int(target_duration * sr)
    if len(stretched) >= target_samples:
        return stretched[:target_samples]
    padded = np.zeros(target_samples, dtype=np.float32)
    padded[: len(stretched)] = stretched
    return padded


def resample(audio: np.ndarray, sr_orig: int, sr_target: int) -> np.ndarray:
    """Resample audio from sr_orig to sr_target."""
    if sr_orig == sr_target:
        return audio
    import librosa
    return librosa.resample(audio, orig_sr=sr_orig, target_sr=sr_target)


def save_wav(audio: np.ndarray, path: str | Path, sr: int):
    """Save numpy array as WAV file."""
    sf.write(str(path), audio, sr)


def export_mp3(wav_path: str | Path, mp3_path: str | Path, quality: int = 2):
    """Export WAV to MP3 using ffmpeg."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(wav_path),
            "-codec:a", "libmp3lame", "-qscale:a", str(quality),
            str(mp3_path),
        ],
        capture_output=True,
        check=True,
    )
