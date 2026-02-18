"""Background worker that runs the pipeline for a job."""

from __future__ import annotations

import threading
import traceback
from pathlib import Path

from src.api.models import JobStatus
from src.api.progress import progress_manager
from src.api.storage import update_job


STEPS_ORDER = ["asr", "diarize", "merge", "translate", "tts", "render"]


def _run_pipeline(
    job_id: str,
    input_path: str,
    workdir: str,
    config: dict,
    youtube_url: str | None = None,
):
    """Execute the full pipeline in the current thread.

    Updates job status and broadcasts progress via WebSocket.
    """
    from src.pipeline.asr import ASRStep
    from src.pipeline.diarize import DiarizeStep
    from src.pipeline.merge import MergeStep
    from src.pipeline.translate import TranslateStep
    from src.pipeline.tts import TTSStep
    from src.pipeline.render import RenderStep

    step_map = {
        "asr": ASRStep,
        "diarize": DiarizeStep,
        "merge": MergeStep,
        "translate": TranslateStep,
        "tts": TTSStep,
        "render": RenderStep,
    }

    work_path = Path(workdir)

    def make_callback(jid: str):
        """Create a progress_callback bound to this job_id."""
        def callback(event: dict):
            progress_manager.broadcast_sync(jid, event)
            # Also update current_step in storage
            if event.get("type") == "step_start":
                update_job(jid, current_step=event.get("step"))
        return callback

    progress_callback = make_callback(job_id)

    try:
        update_job(job_id, status=JobStatus.processing)

        # YouTube download pre-step
        if youtube_url:
            from src.api.youtube import download_audio

            progress_callback({"type": "step_start", "step": "download"})
            wav_path, video_title = download_audio(
                youtube_url,
                Path(input_path),
                progress_callback=progress_callback,
            )
            input_path = str(wav_path)
            update_job(job_id, input_path=input_path, filename=video_title)
            progress_callback({"type": "step_complete", "step": "download"})

        for step_name in STEPS_ORDER:
            step_cls = step_map[step_name]
            step = step_cls(workdir=work_path, config=config, force=False)
            step.run(progress_callback=progress_callback, input_audio=input_path)

        update_job(job_id, status=JobStatus.completed, current_step=None)
        progress_manager.broadcast_sync(job_id, {"type": "pipeline_complete"})

    except Exception as exc:
        tb = traceback.format_exc()
        error_msg = f"{exc}\n{tb}"
        update_job(job_id, status=JobStatus.failed, error=error_msg, current_step=None)
        progress_manager.broadcast_sync(job_id, {
            "type": "error",
            "message": str(exc),
        })


def start_pipeline(
    job_id: str,
    input_path: str,
    workdir: str,
    config: dict,
    youtube_url: str | None = None,
):
    """Launch the pipeline in a background daemon thread."""
    t = threading.Thread(
        target=_run_pipeline,
        args=(job_id, input_path, workdir, config, youtube_url),
        daemon=True,
        name=f"pipeline-{job_id}",
    )
    t.start()
    return t
