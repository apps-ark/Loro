"""FastAPI application factory."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.api.progress import progress_manager
from src.api.routes import audio, jobs, segments


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Store the event loop so the worker thread can schedule coroutines."""
    progress_manager.set_loop(asyncio.get_running_loop())
    yield


app = FastAPI(
    title="Interview Translator API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST routes
app.include_router(jobs.router)
app.include_router(audio.router)
app.include_router(segments.router)


# WebSocket for pipeline progress
@app.websocket("/api/jobs/{job_id}/ws")
async def websocket_progress(websocket: WebSocket, job_id: str):
    await progress_manager.connect(job_id, websocket)
    try:
        # Keep connection alive; client doesn't need to send anything,
        # but we read to detect disconnects.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        progress_manager.disconnect(job_id, websocket)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
