"""Base class for pipeline steps with idempotency support."""

import abc
from pathlib import Path

from rich.console import Console

console = Console()


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

    def run(self, **kwargs):
        """Execute the step with idempotency check."""
        if not self.force and self.outputs_exist():
            console.print(f"  [dim]Skipping {self.name} — outputs already exist[/dim]")
            return

        console.print(f"  [bold cyan]Running {self.name}...[/bold cyan]")
        try:
            self.execute(**kwargs)
            console.print(f"  [bold green]{self.name} complete[/bold green]")
        except Exception:
            console.print(f"  [bold red]{self.name} failed — cleaning partial outputs[/bold red]")
            self.clean_outputs()
            raise

    @abc.abstractmethod
    def execute(self, **kwargs):
        """Implement the actual step logic."""
        ...
