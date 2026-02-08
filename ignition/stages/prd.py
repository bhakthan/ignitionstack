"""Stage 4 — PRD Generator: build the prioritized task backlog."""

from __future__ import annotations

import json
from pathlib import Path

from ignition.config import IgnitionConfig
from ignition.models import PRD, ParsedRequirements, Task


def generate_prd(
    project_name: str,
    requirements: ParsedRequirements,
    tasks: list[Task],
    config: IgnitionConfig,
) -> PRD:
    """Assemble tasks into a PRD document."""
    prd = PRD(
        project_name=project_name,
        description=requirements.summary,
        domain=requirements.domain_hint,
        tasks=tasks,
        metadata={
            "azure_region": config.azure_location,
            "model": config.model,
            "iterations": config.iterations,
            "local_mode": config.local_mode,
            "features_count": len(requirements.features),
            "constraints": requirements.constraints,
        },
    )
    return prd


def save_prd(prd: PRD, work_dir: Path) -> Path:
    """Save PRD to JSON file in the work directory."""
    path = work_dir / "PRD.json"
    path.write_text(prd.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_prd(work_dir: Path) -> PRD:
    """Load PRD from the work directory."""
    path = work_dir / "PRD.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return PRD(**data)


def init_progress(work_dir: Path, prd: PRD) -> Path:
    """Initialize progress.txt — the agent's external memory."""
    path = work_dir / "progress.txt"
    lines = [
        f"# Progress Log — {prd.project_name}",
        f"# Tasks: {len(prd.tasks)}",
        f"# Domain: {prd.domain}",
        "",
        "## Iteration Log",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
