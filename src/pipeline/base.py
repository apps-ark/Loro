"""Base class for pipeline steps with idempotency support."""

import abc
from pathlib import Path
from typing import Any, Callable

from rich.console import Console

console = Console()

# Type alias for progress callbacks.
# Signature: callback(event: dict) -> None
# Events have a "type" key: "step_start", "step_progress", "step_complete",
# "step_skipped", "error".
ProgressCallback = Callable[[dict[str, Any]], None]


class PipelineStep(abc.ABC):
    """Abstract base for all pipeline steps.

    Each step:
    - Has a name and output file(s)
    - Checks if output already exists (idempotent)
    - Cleans up partial outputs on failure
    """

    name: str = "base"
    output_files: list[str] = []

    def __init__(self, workdir: Path, config: dict, force: bool = False):
        self.workdir = workdir
        self.config = config
        self.force = force

    def outputs_exist(self) -> bool:
        """Check if all expected outputs already exist."""
        return all((self.workdir / f).exists() for f in self.output_files)

    def clean_outputs(self):
        """Remove partial outputs on failure."""
        for f in self.output_files:
            path = self.workdir / f
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path, ignore_errors=True)

    def _emit(self, callback: ProgressCallback | None, event: dict[str, Any]):
        """Safely emit a progress event if callback is provided."""
        if callback is not None:
            try:
                callback(event)
            except Exception:
                pass  # Never let callback errors break the pipeline

    def run(self, progress_callback: ProgressCallback | None = None, **kwargs):
        """Execute the step with idempotency check."""
        if not self.force and self.outputs_exist():
            console.print(f"  [dim]Skipping {self.name} — outputs already exist[/dim]")
            self._emit(progress_callback, {
                "type": "step_skipped", "step": self.name,
            })
            return

        console.print(f"  [bold cyan]Running {self.name}...[/bold cyan]")
        self._emit(progress_callback, {"type": "step_start", "step": self.name})
        try:
            self.execute(progress_callback=progress_callback, **kwargs)
            console.print(f"  [bold green]{self.name} complete[/bold green]")
            self._emit(progress_callback, {
                "type": "step_complete", "step": self.name,
            })
        except Exception as exc:
            console.print(f"  [bold red]{self.name} failed — cleaning partial outputs[/bold red]")
            self._emit(progress_callback, {
                "type": "error", "step": self.name,
                "message": str(exc),
            })
            self.clean_outputs()
            raise

    @abc.abstractmethod
    def execute(self, **kwargs):
        """Implement the actual step logic."""
        ...
