"""Job management routes: create, list, detail, delete."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from src.api.models import Job, JobResponse, JobStatus, YouTubeJobCreate
from src.api.storage import create_job, delete_job, get_job, list_jobs, DATA_DIR
from src.api.worker import start_pipeline
from src.api.youtube import is_valid_youtube_url
from src.config import ensure_workdir, load_config, validate_environment

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        filename=job.filename,
        status=job.status,
        current_step=job.current_step,
        error=job.error,
        created_at=str(job.created_at),
    )


@router.post("", status_code=201)
async def create(
    file: UploadFile = File(...),
    max_speakers: int = Form(default=2),
) -> JobResponse:
    """Upload an audio file and start the translation pipeline."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    job_id = uuid.uuid4().hex[:12]
    filename = file.filename

    # Save uploaded file
    input_dir = DATA_DIR / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    input_path = input_dir / f"{job_id}_{filename}"

    content = await file.read()
    input_path.write_bytes(content)

    # Setup workdir
    workdir = DATA_DIR / "work" / job_id
    ensure_workdir(str(workdir))

    # Create job record
    job = Job(
        id=job_id,
        filename=filename,
        input_path=str(input_path),
        workdir=str(workdir),
        status=JobStatus.pending,
    )
    create_job(job)

    # Load config and start pipeline in background
    config = load_config("configs/default.yaml")
    if max_speakers:
        config["diarization"]["max_speakers"] = max_speakers

    validate_environment()
    start_pipeline(job_id, str(input_path), str(workdir), config)

    return _job_to_response(job)


@router.post("/youtube", status_code=201)
async def create_from_youtube(body: YouTubeJobCreate) -> JobResponse:
    """Create a job from a YouTube URL. Audio is downloaded in background."""
    if not is_valid_youtube_url(body.url):
        raise HTTPException(400, "URL de YouTube no valida")

    job_id = uuid.uuid4().hex[:12]

    input_dir = DATA_DIR / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    # yt-dlp will append .wav via postprocessor
    input_path = input_dir / f"{job_id}_youtube"

    workdir = DATA_DIR / "work" / job_id
    ensure_workdir(str(workdir))

    job = Job(
        id=job_id,
        filename=body.url,
        input_path=str(input_path),
        workdir=str(workdir),
        status=JobStatus.pending,
        source_url=body.url,
    )
    create_job(job)

    config = load_config("configs/default.yaml")
    if body.max_speakers:
        config["diarization"]["max_speakers"] = body.max_speakers

    validate_environment()
    start_pipeline(job_id, str(input_path), str(workdir), config, youtube_url=body.url)

    return _job_to_response(job)


@router.get("")
async def list_all() -> list[JobResponse]:
    """List all jobs."""
    return [_job_to_response(j) for j in list_jobs()]


@router.get("/{job_id}")
async def detail(job_id: str) -> JobResponse:
    """Get job details."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    return _job_to_response(job)


@router.delete("/{job_id}")
async def remove(job_id: str):
    """Delete a job and its artifacts."""
    if not delete_job(job_id):
        raise HTTPException(404, f"Job {job_id} not found")
    return {"ok": True}
