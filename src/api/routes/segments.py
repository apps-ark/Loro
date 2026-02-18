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

    # Load timeline map if available (has start_es/end_es)
    timeline_map = None
    timeline_map_path = workdir / "timeline_map.json"
    if timeline_map_path.exists():
        timeline_map = read_json(timeline_map_path)

    segments = []
    for i, seg in enumerate(data.get("segments", [])):
        start = seg.get("start", 0)
        end = seg.get("end", 0)

        # Merge ES timestamps from timeline map by index
        start_es = None
        end_es = None
        duration_es = None
        if timeline_map and i < len(timeline_map.get("segments", [])):
            tm_seg = timeline_map["segments"][i]
            start_es = tm_seg.get("start_es")
            end_es = tm_seg.get("end_es")
            if start_es is not None and end_es is not None:
                duration_es = round(end_es - start_es, 3)

        segments.append(Segment(
            start=start,
            end=end,
            duration=seg.get("duration", end - start),
            speaker=seg.get("speaker", "UNKNOWN"),
            text_en=seg.get("text_en", ""),
            text_es=seg.get("text_es", seg.get("text_en", "")),
            start_es=start_es,
            end_es=end_es,
            duration_es=duration_es,
        ))

    return segments
