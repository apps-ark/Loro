"""YouTube audio download utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

# Matches youtube.com/watch?v=..., youtu.be/..., youtube.com/shorts/...
_YT_RE = re.compile(
    r"^(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)"
    r"[\w-]{11}"
)

MAX_DURATION_SECONDS = 4 * 60 * 60  # 4 hours


def is_valid_youtube_url(url: str) -> bool:
    """Check whether *url* looks like a valid YouTube video URL."""
    return bool(_YT_RE.match(url))


def download_audio(
    url: str,
    output_path: Path,
    progress_callback: Callable[[dict], None] | None = None,
) -> tuple[Path, str]:
    """Download audio from a YouTube URL as WAV.

    Parameters
    ----------
    url:
        YouTube video URL.
    output_path:
        Base path for the output file (without extension).
        yt-dlp will append ``.wav`` via the postprocessor.
    progress_callback:
        Optional callback that receives progress dicts with
        ``step``, ``current``, and ``total`` keys.

    Returns
    -------
    tuple[Path, str]
        ``(path_to_wav, video_title)``

    Raises
    ------
    ValueError
        If *url* is not a valid YouTube URL.
    RuntimeError
        If the download or conversion fails.
    """
    import yt_dlp

    if not is_valid_youtube_url(url):
        raise ValueError(f"URL de YouTube no valida: {url}")

    # Pre-check duration without downloading
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        raise RuntimeError(f"No se pudo obtener info del video: {exc}") from exc

    duration = info.get("duration") or 0
    if duration > MAX_DURATION_SECONDS:
        raise ValueError(
            f"El video dura {duration // 60} minutos, maximo permitido: "
            f"{MAX_DURATION_SECONDS // 60} minutos"
        )

    title: str = info.get("title", "YouTube video")

    # Build yt-dlp hook for progress reporting
    def _progress_hook(d: dict) -> None:
        if progress_callback is None:
            return
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = int(downloaded / total * 100)
            else:
                pct = 0
            progress_callback({
                "type": "step_progress",
                "step": "download",
                "current": pct,
                "total": 100,
            })

    output_template = str(output_path)  # yt-dlp adds extension

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [_progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as exc:
        raise RuntimeError(f"Error al descargar audio de YouTube: {exc}") from exc

    wav_path = Path(f"{output_path}.wav")
    if not wav_path.exists():
        raise RuntimeError(
            f"La descarga finalizó pero no se encontró el archivo: {wav_path}"
        )

    return wav_path, title
