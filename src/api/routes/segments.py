"""Segments route: serve translated segments for a job."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.api.models import Segment
from src.api.storage import get_job
from src.utils.io import read_json

router = APIRouter(prefix="/api/jobs", tags=["segments"])


@router.get("/{job_id}/segments")
async def get_segments(job_id: str) -> list[Segment]:
    """Return translated segments for the player."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    workdir = Path(job.workdir)

    # Try translations.json first (has text_es), fall back to merged_segments.json
    translations_path = workdir / "translations.json"
    merged_path = workdir / "merged_segments.json"

    if translations_path.exists():
        data = read_json(translations_path)
    elif merged_path.exists():
        data = read_json(merged_path)
    else:
        raise HTTPException(404, "No segments found. Pipeline may not have completed.")

    segments = []
    for seg in data.get("segments", []):
        segments.append(Segment(
            start=seg.get("start", 0),
            end=seg.get("end", 0),
            duration=seg.get("duration", seg.get("end", 0) - seg.get("start", 0)),
            speaker=seg.get("speaker", "UNKNOWN"),
            text_en=seg.get("text_en", ""),
            text_es=seg.get("text_es", seg.get("text_en", "")),
        ))

    return segments
