"""Interview Translator CLI — orchestrates the full EN→ES pipeline."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from src.config import apply_cli_overrides, ensure_workdir, load_config, validate_environment

console = Console()

STEPS_ORDER = ["asr", "diarize", "merge", "translate", "tts", "render"]


@click.command()
@click.option("--input", "input_audio", required=True, type=click.Path(exists=True),
              help="Input audio file (.mp3 or .wav)")
@click.option("--workdir", required=True, type=click.Path(),
              help="Working directory for intermediate outputs")
@click.option("--config", "config_path", default="configs/default.yaml",
              help="Path to YAML config file")
@click.option("--max-speakers", type=int, default=None,
              help="Max number of speakers (overrides config)")
@click.option("--force", is_flag=True, default=False,
              help="Re-run all steps even if outputs exist")
@click.option("--steps", multiple=True, type=click.Choice(STEPS_ORDER),
              help="Run only specific steps (default: all)")
def main(input_audio: str, workdir: str, config_path: str,
         max_speakers: int | None, force: bool, steps: tuple[str, ...]):
    """Translate an English interview to Spanish with voice preservation."""
    console.print(Panel.fit(
        "[bold]Interview Translator[/bold] — EN → ES con preservación de voz",
        border_style="cyan",
    ))

    # Load config
    config = load_config(config_path)
    config = apply_cli_overrides(config, max_speakers=max_speakers)

    # Validate environment
    env = validate_environment()

    # Ensure workdir
    work_path = ensure_workdir(workdir)
    input_path = str(Path(input_audio).resolve())

    console.print(f"  Input:   {input_path}")
    console.print(f"  Workdir: {work_path}")
    console.print()

    # Determine which steps to run
    active_steps = list(steps) if steps else STEPS_ORDER

    # Import and instantiate pipeline steps
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

    # Run pipeline
    for step_name in active_steps:
        step_cls = step_map[step_name]
        step = step_cls(workdir=work_path, config=config, force=force)
        try:
            step.run(input_audio=input_path)
        except Exception as e:
            console.print(f"\n[bold red]Pipeline failed at step '{step_name}':[/bold red] {e}")
            sys.exit(1)

    console.print()
    console.print(Panel.fit(
        "[bold green]Pipeline complete![/bold green]",
        border_style="green",
    ))

    # Show output summary
    rendered_wav = work_path / "rendered.wav"
    rendered_mp3 = work_path / "rendered.mp3"
    if rendered_wav.exists():
        console.print(f"  WAV: {rendered_wav}")
    if rendered_mp3.exists():
        console.print(f"  MP3: {rendered_mp3}")


if __name__ == "__main__":
    main()
