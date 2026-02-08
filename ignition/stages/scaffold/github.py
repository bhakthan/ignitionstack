"""Scaffold: GitHub repository creation."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ignition.config import IgnitionConfig
from ignition.models import PRD


def scaffold_github(prd: PRD, config: IgnitionConfig) -> list[str]:
    """Initialize git repo and optionally create GitHub remote."""
    work = config.ensure_work_dir()
    files: list[str] = []

    # .gitignore
    gitignore = work / ".gitignore"
    gitignore.write_text(
        """\
__pycache__/
*.py[cod]
.env
.venv/
node_modules/
dist/
.next/
.azure/
*.log
.coverage
htmlcov/
""",
        encoding="utf-8",
    )
    files.append(".gitignore")

    # Initialize git repo
    _run_git(work, "init")
    _run_git(work, "add", ".")
    _run_git(work, "commit", "-m", f"feat: initial scaffold for {prd.project_name}")

    # Create GitHub repo if token available
    if config.has_github:
        _create_github_repo(prd, config, work)

    return files


def _run_git(cwd: Path, *args: str) -> str:
    """Run a git command silently."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _create_github_repo(prd: PRD, config: IgnitionConfig, work: Path) -> None:
    """Create a GitHub repo using the gh CLI."""
    try:
        subprocess.run(
            [
                "gh",
                "repo",
                "create",
                prd.project_name,
                "--private",
                "--source",
                str(work),
                "--push",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # gh CLI not available — skip silently
