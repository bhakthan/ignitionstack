"""Stage 1 — Input: accept and validate use-case files."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from ignition.models import InputType, detect_input_type

console = Console()


def validate_input(path: Path) -> InputType:
    """Validate the input file exists and return its detected type."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Expected a file, got directory: {path}")
    input_type = detect_input_type(path)
    console.print(f"  [dim]Detected input type:[/dim] [bold]{input_type.value}[/bold]")
    return input_type
