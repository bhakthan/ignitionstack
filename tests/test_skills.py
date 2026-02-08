"""Tests for scaffold: Claude Skills generation (Anthropic spec)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ignition.config import IgnitionConfig
from ignition.models import DiscoveryResult
from ignition.stages.scaffold.skills import (
    _detect_domain,
    scaffold_skills,
)

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def plug_config(tmp_work_dir: Path) -> IgnitionConfig:
    """Config that simulates Plug Mode."""
    target = tmp_work_dir / "existing-project"
    target.mkdir()
    return IgnitionConfig(
        openai_api_key="sk-test-fake-key",
        model="gpt-4o",
        project_name="meridian-portal",
        azure_subscription_id="",
        azure_location="eastus2",
        iterations=3,
        work_dir=tmp_work_dir,
        local_mode=True,
        tutorial_mode=False,
        verbose=False,
        plug_target=target,
    )


@pytest.fixture
def sample_discovery(tmp_work_dir: Path) -> DiscoveryResult:
    return DiscoveryResult(
        target_path=str(tmp_work_dir / "existing-project"),
        language="python",
        framework="fastapi",
        database="postgresql",
        auth="jwt",
        deployment="docker",
        cicd="github-actions",
        api_endpoints=["GET /health", "POST /api/v1/patients"],
    )


# ------------------------------------------------------------------
# Domain detection
# ------------------------------------------------------------------


class TestDetectDomain:
    def test_returns_metadata_domain(self, sample_prd):
        sample_prd.metadata = {"domain": "finance"}
        assert _detect_domain(sample_prd) == "finance"

    def test_falls_back_to_name_match(self, sample_prd):
        sample_prd.metadata = {}
        sample_prd.project_name = "my-healthcare-app"
        assert _detect_domain(sample_prd) == "healthcare"

    def test_returns_general_for_unknown(self, sample_prd):
        sample_prd.metadata = {}
        sample_prd.project_name = "widget-maker"
        assert _detect_domain(sample_prd) == "general"

    def test_handles_oil_and_gas_hyphen(self, sample_prd):
        sample_prd.metadata = {}
        sample_prd.project_name = "oil-and-gas-monitor"
        assert _detect_domain(sample_prd) == "oil-and-gas"


# ------------------------------------------------------------------
# Scaffold mode (3 skills: ops, agent, data)
# ------------------------------------------------------------------


class TestScaffoldSkills:
    def test_generates_three_skills(self, sample_prd, sample_config):
        files = scaffold_skills(sample_prd, sample_config)
        assert len(files) == 3

    def test_skill_folders_are_kebab_case(self, sample_prd, sample_config):
        files = scaffold_skills(sample_prd, sample_config)
        for f in files:
            folder = f.split("/")[1]
            assert re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", folder), (
                f"Folder {folder} is not kebab-case"
            )

    def test_each_folder_has_skill_md(self, sample_prd, sample_config):
        scaffold_skills(sample_prd, sample_config)
        work = sample_config.ensure_work_dir()
        skills = work / "skills"
        skill_dirs = [d for d in skills.iterdir() if d.is_dir()]
        assert len(skill_dirs) == 3
        for d in skill_dirs:
            assert (d / "SKILL.md").exists()

    def test_skill_md_has_yaml_frontmatter(self, sample_prd, sample_config):
        scaffold_skills(sample_prd, sample_config)
        work = sample_config.ensure_work_dir()
        skills = work / "skills"
        for skill_dir in skills.iterdir():
            if not skill_dir.is_dir():
                continue
            content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            assert content.startswith("---"), (
                f"{skill_dir.name}/SKILL.md missing YAML frontmatter"
            )
            # Should close the frontmatter block
            parts = content.split("---")
            assert len(parts) >= 3, (
                f"{skill_dir.name}/SKILL.md has unclosed frontmatter"
            )

    def test_skill_md_contains_project_name(self, sample_prd, sample_config):
        scaffold_skills(sample_prd, sample_config)
        work = sample_config.ensure_work_dir()
        for skill_dir in (work / "skills").iterdir():
            if not skill_dir.is_dir():
                continue
            content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            assert sample_prd.project_name in content

    def test_creates_readme(self, sample_prd, sample_config):
        scaffold_skills(sample_prd, sample_config)
        work = sample_config.ensure_work_dir()
        readme = work / "skills" / "README.md"
        assert readme.exists()
        content = readme.read_text(encoding="utf-8")
        assert "Claude Skills" in content
        assert sample_prd.project_name in content

    def test_ops_skill_has_correct_name(self, sample_prd, sample_config):
        files = scaffold_skills(sample_prd, sample_config)
        ops_files = [f for f in files if "-ops/" in f]
        assert len(ops_files) == 1

    def test_agent_skill_has_correct_name(self, sample_prd, sample_config):
        files = scaffold_skills(sample_prd, sample_config)
        agent_files = [f for f in files if "-agent/" in f]
        assert len(agent_files) == 1

    def test_data_skill_has_correct_name(self, sample_prd, sample_config):
        files = scaffold_skills(sample_prd, sample_config)
        data_files = [f for f in files if "-data/" in f]
        assert len(data_files) == 1

    def test_no_integrate_skill_in_scaffold_mode(
        self, sample_prd, sample_config,
    ):
        files = scaffold_skills(sample_prd, sample_config)
        integrate = [f for f in files if "integrate" in f]
        assert len(integrate) == 0


# ------------------------------------------------------------------
# Plug mode (4 skills: ops, agent, data, integrate)
# ------------------------------------------------------------------


class TestPlugSkills:
    def test_generates_four_skills(
        self, sample_prd, plug_config, sample_discovery,
    ):
        files = scaffold_skills(
            sample_prd, plug_config, discovery=sample_discovery,
        )
        assert len(files) == 4

    def test_includes_integrate_skill(
        self, sample_prd, plug_config, sample_discovery,
    ):
        files = scaffold_skills(
            sample_prd, plug_config, discovery=sample_discovery,
        )
        integrate = [f for f in files if "integrate" in f]
        assert len(integrate) == 1

    def test_integrate_skill_mentions_framework(
        self, sample_prd, plug_config, sample_discovery,
    ):
        scaffold_skills(
            sample_prd, plug_config, discovery=sample_discovery,
        )
        work = plug_config.ensure_work_dir()
        integrate_dirs = [
            d for d in (work / "skills").iterdir()
            if d.is_dir() and "integrate" in d.name
        ]
        assert len(integrate_dirs) == 1
        content = (integrate_dirs[0] / "SKILL.md").read_text(encoding="utf-8")
        assert sample_discovery.framework in content.lower()

    def test_integrate_skill_references_language(
        self, sample_prd, plug_config, sample_discovery,
    ):
        scaffold_skills(
            sample_prd, plug_config, discovery=sample_discovery,
        )
        work = plug_config.ensure_work_dir()
        integrate_dirs = [
            d for d in (work / "skills").iterdir()
            if d.is_dir() and "integrate" in d.name
        ]
        content = (integrate_dirs[0] / "SKILL.md").read_text(encoding="utf-8")
        assert sample_discovery.language in content.lower()

    def test_plug_readme_mentions_integrate(
        self, sample_prd, plug_config, sample_discovery,
    ):
        scaffold_skills(
            sample_prd, plug_config, discovery=sample_discovery,
        )
        work = plug_config.ensure_work_dir()
        readme = work / "skills" / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "integrate" in content.lower()


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------


class TestSkillsEdgeCases:
    def test_idempotent_call(self, sample_prd, sample_config):
        """Calling scaffold_skills twice shouldn't fail."""
        files1 = scaffold_skills(sample_prd, sample_config)
        files2 = scaffold_skills(sample_prd, sample_config)
        assert files1 == files2

    def test_custom_project_name_in_folder(self, sample_prd, sample_config):
        sample_prd.project_name = "acme-widget"
        files = scaffold_skills(sample_prd, sample_config)
        for f in files:
            assert "acme-widget" in f
