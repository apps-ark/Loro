"""Pydantic models for the API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobCreate(BaseModel):
    max_speakers: int = Field(default=2, ge=1, le=10)


class YouTubeJobCreate(BaseModel):
    url: str
    max_speakers: int = Field(default=2, ge=1, le=10)


class Job(BaseModel):
    id: str
    filename: str
    input_path: str
    workdir: str
    status: JobStatus = JobStatus.pending
    current_step: str | None = None
    error: str | None = None
    source_url: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobResponse(BaseModel):
    id: str
    filename: str
    status: JobStatus
    current_step: str | None = None
    error: str | None = None
    created_at: str


class Segment(BaseModel):
    start: float
    end: float
    duration: float
    speaker: str
    text_en: str
    text_es: str
    start_es: float | None = None
    end_es: float | None = None
    duration_es: float | None = None


class WSMessage(BaseModel):
    type: str  # step_start, step_progress, step_complete, pipeline_complete, error
    step: str | None = None
    current: int | None = None
    total: int | None = None
    message: str | None = None
