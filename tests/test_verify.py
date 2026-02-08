"""Tests for the verification module."""

from pathlib import Path

from ignition.models import PRD, Task, TaskCategory
from ignition.verify import verify_output


class TestVerifyOutput:
    def test_empty_dir_has_issues(self, tmp_path: Path):
        issues = verify_output(tmp_path)
        assert len(issues) > 0

    def test_complete_dir_passes(self, tmp_path: Path, sample_prd):
        """Set up a minimal valid output directory."""
        # Create expected files
        (tmp_path / "PRD.json").write_text("{}")
        (tmp_path / "progress.txt").write_text("# Progress")
        (tmp_path / "ralph.sh").write_text("#!/bin/bash")
        (tmp_path / "ralph.ps1").write_text("# PowerShell")
        (tmp_path / "infra").mkdir()
        (tmp_path / "infra" / "main.bicep").write_text("// bicep")
        (tmp_path / "agents").mkdir()
        (tmp_path / "agents" / "agent-config.json").write_text("{}")
        (tmp_path / "db" / "migrations").mkdir(parents=True)
        (tmp_path / "db" / "migrations" / "001_initial.sql").write_text("-- sql")
        (tmp_path / "app" / "backend").mkdir(parents=True)
        (tmp_path / "app" / "backend" / "main.py").write_text("# python")
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        (tmp_path / ".github" / "workflows" / "ci-cd.yml").write_text("name: CI")

        issues = verify_output(tmp_path)
        assert issues == []

    def test_docker_compose_alternative(self, tmp_path: Path):
        """Docker compose mode doesn't need infra/ dir."""
        (tmp_path / "PRD.json").write_text("{}")
        (tmp_path / "progress.txt").write_text("")
        (tmp_path / "ralph.sh").write_text("")
        (tmp_path / "ralph.ps1").write_text("")
        (tmp_path / "docker-compose.yml").write_text("")
        (tmp_path / "agents").mkdir()
        (tmp_path / "agents" / "agent-config.json").write_text("{}")
        (tmp_path / "db" / "migrations").mkdir(parents=True)
        (tmp_path / "db" / "migrations" / "001_initial.sql").write_text("")
        (tmp_path / "app" / "backend").mkdir(parents=True)
        (tmp_path / "app" / "backend" / "main.py").write_text("")
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        (tmp_path / ".github" / "workflows" / "ci-cd.yml").write_text("")

        issues = verify_output(tmp_path)
        assert issues == []

    def test_few_tasks_flagged(self, tmp_path: Path):
        prd = PRD(
            project_name="tiny",
            description="test",
            tasks=[
                Task(id=1, title="t1", category=TaskCategory.BACKEND, description="x"),
            ],
        )
        issues = verify_output(tmp_path, prd)
        assert any("only 1 tasks" in i for i in issues)
