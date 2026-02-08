"""Verification — checks that the scaffolded output is structurally valid."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from ignition.models import PRD


def verify_output(
    work_dir: Path,
    prd: PRD | None = None,
    *,
    console: Console | None = None,
) -> list[str]:
    """
    Verify the generated output directory.

    Returns a list of issues (empty = all checks passed).
    """
    if console is None:
        console = Console()

    issues: list[str] = []

    # Check core files exist
    expected_files = [
        "PRD.json",
        "progress.txt",
        "ralph.sh",
        "ralph.ps1",
    ]
    for fname in expected_files:
        if not (work_dir / fname).exists():
            issues.append(f"Missing: {fname}")

    # Check infrastructure
    if (work_dir / "infra").exists():
        if not (work_dir / "infra" / "main.bicep").exists():
            issues.append("Missing: infra/main.bicep")
    elif (work_dir / "docker-compose.yml").exists():
        pass  # local mode — OK
    else:
        issues.append("Missing: infra/ directory or docker-compose.yml")

    # Check agents
    if not (work_dir / "agents" / "agent-config.json").exists():
        issues.append("Missing: agents/agent-config.json")

    # Check database
    if not (work_dir / "db" / "migrations" / "001_initial.sql").exists():
        issues.append("Missing: db/migrations/001_initial.sql")

    # Check app
    if not (work_dir / "app" / "backend" / "main.py").exists():
        issues.append("Missing: app/backend/main.py")

    # Check CI/CD
    if not (work_dir / ".github" / "workflows" / "ci-cd.yml").exists():
        issues.append("Missing: .github/workflows/ci-cd.yml")

    # PRD validation
    if prd:
        if len(prd.tasks) < 5:
            issues.append(f"PRD has only {len(prd.tasks)} tasks (expected 30-50)")
        failing = [t for t in prd.tasks if not t.passes_tbic]
        if failing:
            issues.append(f"{len(failing)} tasks fail T/B/I/C test")

    # Report
    if issues:
        console.print(f"\n  [yellow]⚠️  {len(issues)} issue(s) found:[/yellow]")
        for issue in issues:
            console.print(f"    [dim]•[/dim] {issue}")
    else:
        console.print("  [green]✅ All verification checks passed[/green]")

    return issues


def verify_plug_output(
    work_dir: Path,
    *,
    console: Console | None = None,
) -> list[str]:
    """
    Verify the generated plug output directory.

    Returns a list of issues (empty = all checks passed).
    """
    if console is None:
        console = Console()

    issues: list[str] = []

    # Core plug files
    expected = [
        "PRD.json",
        "progress.txt",
        "discovery.json",
        "ralph.sh",
        "ralph.ps1",
    ]
    for fname in expected:
        if not (work_dir / fname).exists():
            issues.append(f"Missing: {fname}")

    # Adapters
    adapters = work_dir / "adapters"
    if adapters.exists():
        for f in ["agent_middleware.py", "rag_connector.py"]:
            if not (adapters / f).exists():
                issues.append(f"Missing: adapters/{f}")
    else:
        issues.append("Missing: adapters/ directory")

    # Infra delta
    infra = work_dir / "infra-delta"
    if infra.exists():
        has_bicep = (infra / "delta.bicep").exists()
        has_compose = (infra / "docker-compose.override.yml").exists()
        if not has_bicep and not has_compose:
            issues.append(
                "Missing: infra-delta/delta.bicep or "
                "docker-compose.override.yml"
            )
    else:
        issues.append("Missing: infra-delta/ directory")

    # DB delta
    if not (work_dir / "db-delta" / "001_agent_state.sql").exists():
        issues.append("Missing: db-delta/001_agent_state.sql")

    # CI/CD patch
    if not (work_dir / "cicd-patch" / "ai-steps.yml").exists():
        issues.append("Missing: cicd-patch/ai-steps.yml")

    # Agents
    if not (work_dir / "agents" / "agent-config.json").exists():
        issues.append("Missing: agents/agent-config.json")

    # Report
    if issues:
        console.print(f"\n  [yellow]\u26a0\ufe0f  {len(issues)} issue(s):[/yellow]")
        for issue in issues:
            console.print(f"    [dim]\u2022[/dim] {issue}")
    else:
        console.print(
            "  [green]\u2705 All plug verification checks passed[/green]"
        )

    return issues
