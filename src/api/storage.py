"""Lightweight JSON-file storage for jobs."""

from __future__ import annotations

import json
import shutil
import threading
from datetime import datetime
from pathlib import Path

from src.api.models import Job, JobStatus

# Project-level data directory
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
JOBS_FILE = DATA_DIR / "jobs.json"

_lock = threading.Lock()


def _read_all() -> dict[str, dict]:
    if not JOBS_FILE.exists():
        return {}
    with open(JOBS_FILE, "r") as f:
        return json.load(f)


def _write_all(data: dict[str, dict]):
    JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def create_job(job: Job) -> Job:
    with _lock:
        jobs = _read_all()
        jobs[job.id] = job.model_dump(mode="json")
        _write_all(jobs)
    return job


def get_job(job_id: str) -> Job | None:
    with _lock:
        jobs = _read_all()
    raw = jobs.get(job_id)
    if raw is None:
        return None
    return Job(**raw)


def list_jobs() -> list[Job]:
    with _lock:
        jobs = _read_all()
    result = [Job(**v) for v in jobs.values()]
    result.sort(key=lambda j: j.created_at, reverse=True)
    return result


def update_job(job_id: str, **fields) -> Job | None:
    with _lock:
        jobs = _read_all()
        if job_id not in jobs:
            return None
        jobs[job_id].update(fields)
        _write_all(jobs)
        return Job(**jobs[job_id])


def delete_job(job_id: str) -> bool:
    with _lock:
        jobs = _read_all()
        if job_id not in jobs:
            return False
        job_data = jobs.pop(job_id)
        _write_all(jobs)

    # Clean up files
    input_path = Path(job_data.get("input_path", ""))
    if input_path.exists():
        input_path.unlink(missing_ok=True)
    workdir = Path(job_data.get("workdir", ""))
    if workdir.exists():
        shutil.rmtree(workdir, ignore_errors=True)

    return True
