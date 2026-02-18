"""WebSocket connection manager for broadcasting pipeline progress."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket


class ProgressManager:
    """Manages WebSocket connections per job and broadcasts progress events."""

    def __init__(self):
        # job_id -> set of active WebSocket connections
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, job_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[job_id].add(ws)

    def disconnect(self, job_id: str, ws: WebSocket):
        self._connections[job_id].discard(ws)
        if not self._connections[job_id]:
            del self._connections[job_id]

    async def _broadcast(self, job_id: str, message: dict):
        """Send a message to all WebSocket clients watching a job."""
        data = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for ws in self._connections.get(job_id, set()):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(job_id, ws)

    def broadcast_sync(self, job_id: str, message: dict):
        """Thread-safe broadcast callable from the pipeline worker thread."""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._broadcast(job_id, message),
            self._loop,
        )


# Singleton instance
progress_manager = ProgressManager()
