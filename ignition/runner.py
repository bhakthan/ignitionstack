"""IgnitionStack Runner — orchestrates the full 7-stage pipeline."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ignition.config import IgnitionConfig
from ignition.models import (
    PRD,
    IterationResult,
    PlugManifest,
    ScaffoldManifest,
)
from ignition.stages.decomposer import decompose
from ignition.stages.discovery import discover, save_discovery
from ignition.stages.input import validate_input
from ignition.stages.parser import parse
from ignition.stages.prd import generate_prd, init_progress, save_prd
from ignition.stages.scaffold.agents import scaffold_agents
from ignition.stages.scaffold.app import scaffold_app
from ignition.stages.scaffold.bicep import scaffold_infra
from ignition.stages.scaffold.cicd import scaffold_cicd
from ignition.stages.scaffold.database import scaffold_database
from ignition.stages.scaffold.github import scaffold_github
from ignition.stages.scaffold.plug import scaffold_plug
from ignition.stages.scaffold.ralph import scaffold_ralph

console = Console()


class IgnitionStackAgent:
    """
    The IgnitionStack Agent — runs the complete pipeline:

      Input → Parse → Decompose → PRD → Scaffold → Ralph → Production
    """

    def __init__(self, config: IgnitionConfig):
        self.config = config
        self.tutorial: object | None = None  # set if tutorial mode

    def run(self, input_path: Path) -> Path:
        """Execute the full pipeline and return the work directory."""
        if self.config.is_plug_mode:
            return self.run_plug(input_path)
        return self._run_scaffold(input_path)

    # ------------------------------------------------------------------
    # Plug Mode pipeline
    # ------------------------------------------------------------------

    def run_plug(self, input_path: Path) -> Path:
        """
        Execute the Plug pipeline — additive integration into an existing project.

        Discover → Parse → Decompose → PRD → Plug Scaffold → Ralph → Verify
        """
        config = self.config
        assert config.plug_target is not None
        # Default work dir for plug mode sits beside the target project
        if str(config.work_dir) == "./ignition-output":
            config.work_dir = config.plug_target.parent / "ignition-plug"
        work = config.ensure_work_dir()

        console.print(
            Panel(
                f"[bold magenta]IgnitionStack — Plug Mode[/bold magenta]\n"
                f"Target: [bold]{config.plug_target}[/bold]\n"
                f"Project: [bold]{config.project_name}[/bold]\n"
                f"Model: {config.model}\n"
                f"Mode: {'Local (Docker)' if config.local_mode else 'Azure'}",
                title="🔌 Plug",
                border_style="magenta",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Stage 0: Discovery
            task = progress.add_task(
                "Stage 0/7 — Discovering existing stack...", total=None,
            )
            self._tutorial_before("discovery")
            discovery_result = discover(config.plug_target)
            save_discovery(discovery_result, work)
            self._tutorial_after(
                "discovery",
                extra=f"Detected: {discovery_result.stack_summary}",
            )
            progress.update(task, completed=True)

            # Stage 1: Input
            task = progress.add_task(
                "Stage 1/7 — Validating input...", total=None,
            )
            self._tutorial_before("input")
            input_type = validate_input(input_path)
            self._tutorial_after("input")
            progress.update(task, completed=True)

            # Stage 2: Parse
            task = progress.add_task(
                "Stage 2/7 — Parsing requirements...", total=None,
            )
            self._tutorial_before("parse")
            requirements = parse(input_path, input_type, config)
            self._tutorial_after(
                "parse",
                extra=f"Found {len(requirements.features)} features",
            )
            progress.update(task, completed=True)

            # Stage 3: Decompose (filtered to additive tasks)
            task = progress.add_task(
                "Stage 3/7 — Decomposing additive tasks...", total=None,
            )
            self._tutorial_before("decompose")
            tasks = decompose(requirements, config)
            self._tutorial_after(
                "decompose",
                extra=(
                    f"{len(tasks)} atomic tasks "
                    "(integration-only, additive)"
                ),
            )
            progress.update(task, completed=True)

            # Stage 4: PRD
            task = progress.add_task(
                "Stage 4/7 — Building PRD...", total=None,
            )
            self._tutorial_before("prd")
            prd = generate_prd(
                config.project_name, requirements, tasks, config,
            )
            prd.metadata["plug_mode"] = True
            prd.metadata["discovery"] = discovery_result.model_dump()
            prd_path = save_prd(prd, work)
            init_progress(work, prd)
            self._tutorial_after("prd", extra=f"Saved {prd_path.name}")
            progress.update(task, completed=True)

            # Stage 5: Plug Scaffold
            task = progress.add_task(
                "Stage 5/7 — Scaffolding plug artifacts...", total=None,
            )
            self._tutorial_before("plug_scaffold")
            plug_manifest = self._plug_scaffold(prd, discovery_result)
            self._tutorial_after(
                "plug_scaffold",
                extra=f"Generated {len(plug_manifest.files)} files",
            )
            progress.update(task, completed=True)

            # Stage 6: Ralph Loop
            task = progress.add_task(
                f"Stage 6/7 — Ralph Loop (×{config.iterations})...",
                total=None,
            )
            self._tutorial_before("ralph")
            results = self._ralph_loop(prd, work)
            self._tutorial_after(
                "ralph",
                extra=(
                    f"{sum(1 for r in results if r.success)}"
                    f"/{len(results)} iterations succeeded"
                ),
            )
            progress.update(task, completed=True)

            # Stage 7: Verify
            task = progress.add_task(
                "Stage 7/7 — Verifying output...", total=None,
            )
            self._tutorial_before("verify")
            self._verify_plug(work)
            self._tutorial_after("verify")
            progress.update(task, completed=True)

        console.print()
        console.print(
            Panel(
                f"[bold green]✅ Plug pipeline complete![/bold green]\n\n"
                f"Output: [bold]{work}[/bold]\n"
                f"Target: {config.plug_target}\n"
                f"Files: {len(plug_manifest.files)} generated\n\n"
                f"Next steps:\n"
                f"  1. Review generated adapters in {work}\n"
                f"  2. Copy into your project or run ralph.sh\n"
                f"  3. cd {work} && bash ralph.sh",
                title="🔌 Plug Complete",
                border_style="green",
            )
        )

        return work

    def _plug_scaffold(self, prd, discovery_result):
        """Run plug-specific scaffold sub-stages."""

        config = self.config
        all_files: list[str] = []

        # Core plug artifacts
        all_files.extend(scaffold_plug(prd, discovery_result, config))

        # Agents config (tuned to existing service)
        all_files.extend(scaffold_agents(prd, config))

        # Ralph scripts (scoped to plug dir)
        all_files.extend(scaffold_ralph(prd, config))

        return PlugManifest(
            files=all_files,
            discovery=discovery_result,
            adapter_framework=discovery_result.framework,
            infra_mode=(
                "docker-compose-override"
                if config.local_mode
                else "delta-bicep"
            ),
        )

    def _verify_plug(self, work: Path) -> None:
        """Basic verification of plug output."""
        from ignition.verify import verify_plug_output

        verify_plug_output(work, console=console)

    # ------------------------------------------------------------------
    # Full Scaffold Mode pipeline (original)
    # ------------------------------------------------------------------

    def _run_scaffold(self, input_path: Path) -> Path:
        """Execute the full scaffold pipeline and return the work directory."""
        config = self.config
        work = config.ensure_work_dir()

        console.print(
            Panel(
                f"[bold cyan]IgnitionStack Agent[/bold cyan]\n"
                f"Project: [bold]{config.project_name}[/bold]\n"
                f"Model: {config.model}\n"
                f"Mode: {'Local (Docker)' if config.local_mode else 'Azure'}\n"
                f"Tutorial: {'On' if config.tutorial_mode else 'Off'}",
                title="🚀 Ignition",
                border_style="cyan",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Stage 1: Input
            task = progress.add_task("Stage 1/7 — Validating input...", total=None)
            self._tutorial_before("input")
            input_type = validate_input(input_path)
            self._tutorial_after("input")
            progress.update(task, completed=True)

            # Stage 2: Parse
            task = progress.add_task("Stage 2/7 — Parsing requirements...", total=None)
            self._tutorial_before("parse")
            requirements = parse(input_path, input_type, config)
            self._tutorial_after("parse", extra=f"Found {len(requirements.features)} features")
            progress.update(task, completed=True)

            # Stage 3: Decompose
            task = progress.add_task("Stage 3/7 — Decomposing into tasks...", total=None)
            self._tutorial_before("decompose")
            tasks = decompose(requirements, config)
            self._tutorial_after(
                "decompose",
                extra=f"Generated {len(tasks)} atomic tasks (T/B/I/C validated)",
            )
            progress.update(task, completed=True)

            # Stage 4: PRD
            task = progress.add_task("Stage 4/7 — Building PRD...", total=None)
            self._tutorial_before("prd")
            prd = generate_prd(config.project_name, requirements, tasks, config)
            prd_path = save_prd(prd, work)
            init_progress(work, prd)
            self._tutorial_after("prd", extra=f"Saved {prd_path.name}")
            progress.update(task, completed=True)

            # Stage 5: Scaffold
            task = progress.add_task("Stage 5/7 — Scaffolding project...", total=None)
            self._tutorial_before("scaffold")
            manifest = self._scaffold(prd)
            self._tutorial_after(
                "scaffold",
                extra=f"Generated {len(manifest.files)} files",
            )
            progress.update(task, completed=True)

            # Stage 6: Ralph Loop
            task = progress.add_task(
                f"Stage 6/7 — Ralph Loop (×{config.iterations})...",
                total=None,
            )
            self._tutorial_before("ralph")
            results = self._ralph_loop(prd, work)
            self._tutorial_after(
                "ralph",
                extra=f"{sum(1 for r in results if r.success)}/{len(results)} iterations succeeded",
            )
            progress.update(task, completed=True)

            # Stage 7: Verify
            task = progress.add_task("Stage 7/7 — Verifying output...", total=None)
            self._tutorial_before("verify")
            self._verify(work, prd)
            self._tutorial_after("verify")
            progress.update(task, completed=True)

        console.print()
        console.print(
            Panel(
                f"[bold green]✅ Pipeline complete![/bold green]\n\n"
                f"Output: [bold]{work}[/bold]\n"
                f"Tasks: {prd.progress_pct}% complete ({len(prd.tasks)} total)\n"
                f"Files: {len(manifest.files)} generated\n\n"
                f"Next steps:\n"
                f"  cd {work}\n"
                f"  {'bash ralph.sh' if not config.local_mode else 'docker compose up'}",
                title="🏁 Done",
                border_style="green",
            )
        )

        return work

    def _scaffold(self, prd: PRD) -> ScaffoldManifest:
        """Run all scaffold sub-stages."""
        config = self.config
        all_files: list[str] = []

        all_files.extend(scaffold_infra(prd, config))
        all_files.extend(scaffold_agents(prd, config))
        all_files.extend(scaffold_database(prd, config))
        all_files.extend(scaffold_app(prd, config))
        all_files.extend(scaffold_cicd(prd, config))
        all_files.extend(scaffold_ralph(prd, config))

        # GitHub init (git + optional remote)
        try:
            all_files.extend(scaffold_github(prd, config))
        except Exception:
            pass  # git not available — continue

        return ScaffoldManifest(
            files=all_files,
            infra_template="docker-compose" if config.local_mode else "bicep",
        )

    def _ralph_loop(self, prd: PRD, work: Path) -> list[IterationResult]:
        """
        Execute the Ralph loop.

        In this template, we generate the ralph scripts and log placeholder iterations.
        The actual ralph.sh/ps1 is meant to be run separately by the learner.
        """
        results: list[IterationResult] = []

        # Log that Ralph scripts are ready
        progress_file = work / "progress.txt"
        with open(progress_file, "a", encoding="utf-8") as f:
            f.write("\n## Ralph Loop — Ready\n")
            f.write("- Scripts generated: ralph.sh, ralph.ps1\n")
            f.write(f"- Configured iterations: {self.config.iterations}\n")
            f.write(f"- Model: {self.config.model}\n")
            f.write("\nRun `bash ralph.sh` or `.\\ralph.ps1` to start the loop.\n")

        # Return a single "setup" result
        results.append(
            IterationResult(
                iteration=0,
                task_id=0,
                task_title="Ralph loop scripts generated",
                success=True,
                duration_seconds=0.0,
            )
        )

        return results

    def _verify(self, work: Path, prd: PRD) -> None:
        """Basic verification of generated output."""
        from ignition.verify import verify_output

        verify_output(work, prd, console=console)

    def _tutorial_before(self, stage: str) -> None:
        """Show tutorial explanation before a stage (if tutorial mode)."""
        if self.config.tutorial_mode and self.tutorial:
            try:
                self.tutorial.before_stage(stage)  # type: ignore[attr-defined]
            except Exception:
                pass

    def _tutorial_after(self, stage: str, extra: str = "") -> None:
        """Show tutorial explanation after a stage (if tutorial mode)."""
        if self.config.tutorial_mode and self.tutorial:
            try:
                self.tutorial.after_stage(stage, extra)  # type: ignore[attr-defined]
            except Exception:
                pass
