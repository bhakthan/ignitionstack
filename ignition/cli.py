"""CLI entry point for IgnitionStack."""

from __future__ import annotations

import shutil
from pathlib import Path

import click
from rich.console import Console

from ignition import __version__
from ignition.config import IgnitionConfig

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="ignition")
def main():
    """IgnitionStack — Use Case → Production Azure Workload."""
    pass


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--project", "-p", required=True, help="Project name (kebab-case)")
@click.option("--region", default="eastus2", help="Azure region")
@click.option("--model", default=None, help="LLM model (default: gpt-4o or IGNITION_MODEL)")
@click.option("--iterations", default=20, type=int, help="Ralph loop iterations")
@click.option("--work-dir", default=None, type=click.Path(path_type=Path), help="Output directory")
@click.option("--local", is_flag=True, help="Docker Compose mode (no Azure)")
@click.option(
    "--plug", default=None,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Existing project to enhance (Plug Mode)",
)
@click.option("--tutorial", is_flag=True, help="Step-by-step guided mode")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(
    input_file: Path,
    project: str,
    region: str,
    model: str | None,
    iterations: int,
    work_dir: Path | None,
    local: bool,
    plug: Path | None,
    tutorial: bool,
    verbose: bool,
):
    """Run the full IgnitionStack pipeline on an input file."""
    config = IgnitionConfig(
        project_name=project,
        azure_location=region,
        iterations=iterations,
        local_mode=local,
        plug_target=plug,
        tutorial_mode=tutorial,
        verbose=verbose,
    )
    if model:
        config.model = model
    if work_dir:
        config.work_dir = work_dir

    from ignition.runner import IgnitionStackAgent

    agent = IgnitionStackAgent(config)

    # Attach tutorial runner if tutorial mode
    if tutorial:
        try:
            from ignition.tutorial import TutorialRunner

            agent.tutorial = TutorialRunner(console)
        except ImportError:
            console.print("[yellow]Tutorial module not available[/yellow]")

    agent.run(input_file)


@main.command()
@click.argument("work_dir", type=click.Path(exists=True, path_type=Path))
def verify(work_dir: Path):
    """Verify a generated project directory."""
    from ignition.stages.prd import load_prd
    from ignition.verify import verify_output

    try:
        prd = load_prd(work_dir)
    except FileNotFoundError:
        prd = None
        console.print("[yellow]No PRD.json found — running structural checks only[/yellow]")

    issues = verify_output(work_dir, prd, console=console)
    if issues:
        raise SystemExit(1)


EXAMPLE_DOMAINS = [
    "healthcare", "finance", "education", "oil-and-gas",
    "construction", "telco", "retail",
]


@main.command()
@click.argument("domain", type=click.Choice(EXAMPLE_DOMAINS))
@click.option("--dest", default=".", type=click.Path(path_type=Path), help="Destination directory")
def example(domain: str, dest: Path):
    """Copy a domain example to the current directory."""
    examples_dir = Path(__file__).resolve().parent.parent / "examples" / domain
    if not examples_dir.exists():
        console.print(f"[red]Example not found: {domain}[/red]")
        raise SystemExit(1)

    target = Path(dest) / domain
    shutil.copytree(str(examples_dir), str(target), dirs_exist_ok=True)
    console.print(f"[green]✅ Copied {domain} example to {target}[/green]")
    console.print(f"   Run: ignition run {target / 'use-case.txt'} --project my-{domain}-app")


@main.command()
def version():
    """Print version information."""
    console.print(f"IgnitionStack v{__version__}")


if __name__ == "__main__":
    main()
