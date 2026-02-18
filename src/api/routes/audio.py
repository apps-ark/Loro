"""Audio streaming routes with Range header support."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from src.api.storage import get_job

router = APIRouter(prefix="/api/jobs", tags=["audio"])

# Map track names to files
TRACK_FILES = {
    "original": None,  # Uses job.input_path
    "translated": "rendered.mp3",
}

MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}


def _get_audio_path(job_id: str, track: str) -> Path:
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    if track == "original":
        path = Path(job.input_path)
    elif track == "translated":
        # Try mp3 first, then wav
        workdir = Path(job.workdir)
        path = workdir / "rendered.mp3"
        if not path.exists():
            path = workdir / "rendered.wav"
    else:
        raise HTTPException(400, f"Unknown track: {track}")

    if not path.exists():
        raise HTTPException(404, f"Audio file not found for track '{track}'")

    return path


@router.get("/{job_id}/audio/{track}")
async def stream_audio(job_id: str, track: str, request: Request):
    """Stream audio with HTTP Range support for seeking."""
    path = _get_audio_path(job_id, track)
    file_size = path.stat().st_size
    suffix = path.suffix.lower()
    content_type = MIME_TYPES.get(suffix, "application/octet-stream")

    range_header = request.headers.get("range")

    if not range_header:
        return FileResponse(
            str(path),
            media_type=content_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            },
        )

    # Parse Range: bytes=start-end
    try:
        range_spec = range_header.replace("bytes=", "")
        parts = range_spec.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
    except (ValueError, IndexError):
        raise HTTPException(416, "Invalid range header")

    if start >= file_size or end >= file_size:
        raise HTTPException(416, "Range not satisfiable")

    chunk_size = end - start + 1

    def iter_file():
        with open(path, "rb") as f:
            f.seek(start)
            remaining = chunk_size
            while remaining > 0:
                read_size = min(remaining, 64 * 1024)
                data = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data

    return StreamingResponse(
        iter_file(),
        status_code=206,
        media_type=content_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(chunk_size),
        },
    )
