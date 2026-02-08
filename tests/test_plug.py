"""Tests for the Plug scaffold stage — integration artifact generation."""

from pathlib import Path

import pytest

from ignition.config import IgnitionConfig
from ignition.models import PRD, DiscoveryResult, PlugManifest, Task, TaskCategory
from ignition.stages.scaffold.plug import scaffold_plug
from ignition.verify import verify_plug_output


@pytest.fixture
def plug_config(tmp_path: Path) -> IgnitionConfig:
    work = tmp_path / "plug-output"
    work.mkdir()
    return IgnitionConfig(
        openai_api_key="sk-test",
        model="gpt-4o",
        project_name="acme-service",
        azure_subscription_id="",
        azure_location="eastus2",
        iterations=5,
        work_dir=work,
        local_mode=True,
        plug_target=tmp_path / "existing-project",
    )


@pytest.fixture
def plug_discovery(tmp_path: Path) -> DiscoveryResult:
    return DiscoveryResult(
        target_path=str(tmp_path / "existing-project"),
        language="python",
        framework="fastapi",
        database="postgresql",
        auth="jwt",
        deployment="docker-compose",
        cicd="github-actions",
        api_endpoints=["GET /api/v1/health", "POST /api/v1/users"],
    )


@pytest.fixture
def plug_prd() -> PRD:
    return PRD(
        project_name="acme-service",
        description="Enhance existing CRM with AI agents.",
        domain="general",
        tasks=[
            Task(
                id=1,
                title="Add agent routing middleware",
                category=TaskCategory.BACKEND,
                description="Integrate agent middleware into existing FastAPI app.",
            ),
            Task(
                id=2,
                title="Create RAG connector",
                category=TaskCategory.AGENT,
                description="Wire Azure AI Search to existing PostgreSQL data.",
            ),
        ],
    )


class TestPlugScaffold:
    def test_generates_adapters(self, plug_prd, plug_discovery, plug_config):
        files = scaffold_plug(plug_prd, plug_discovery, plug_config)
        work = plug_config.work_dir
        assert (work / "adapters" / "agent_middleware.py").exists()
        assert (work / "adapters" / "rag_connector.py").exists()
        assert (work / "adapters" / "README.md").exists()
        assert any("agent_middleware" in f for f in files)

    def test_local_mode_generates_compose_override(
        self, plug_prd, plug_discovery, plug_config,
    ):
        plug_config.local_mode = True
        scaffold_plug(plug_prd, plug_discovery, plug_config)
        override = plug_config.work_dir / "infra-delta" / "docker-compose.override.yml"
        assert override.exists()
        content = override.read_text(encoding="utf-8")
        assert "redis" in content.lower() or "sidecar" in content.lower()

    def test_azure_mode_generates_bicep_delta(
        self, plug_prd, plug_discovery, plug_config,
    ):
        plug_config.local_mode = False
        scaffold_plug(plug_prd, plug_discovery, plug_config)
        delta = plug_config.work_dir / "infra-delta" / "delta.bicep"
        assert delta.exists()
        content = delta.read_text(encoding="utf-8")
        assert "searchServices" in content or "Search" in content

    def test_generates_db_delta(self, plug_prd, plug_discovery, plug_config):
        scaffold_plug(plug_prd, plug_discovery, plug_config)
        sql = plug_config.work_dir / "db-delta" / "001_agent_state.sql"
        assert sql.exists()
        content = sql.read_text(encoding="utf-8")
        assert "agent_conversations" in content
        assert "agent_messages" in content
        assert "agent_state" in content

    def test_generates_cicd_patch(self, plug_prd, plug_discovery, plug_config):
        scaffold_plug(plug_prd, plug_discovery, plug_config)
        yml = plug_config.work_dir / "cicd-patch" / "ai-steps.yml"
        assert yml.exists()
        content = yml.read_text(encoding="utf-8")
        assert "agent" in content.lower() or "deploy" in content.lower()

    def test_adapters_readme_contains_stack_info(
        self, plug_prd, plug_discovery, plug_config,
    ):
        scaffold_plug(plug_prd, plug_discovery, plug_config)
        readme = plug_config.work_dir / "adapters" / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "python" in content.lower()
        assert "fastapi" in content.lower()


class TestPlugManifest:
    def test_manifest_fields(self, plug_discovery):
        m = PlugManifest(
            files=["adapters/agent_middleware.py"],
            discovery=plug_discovery,
            adapter_framework="fastapi",
            infra_mode="docker-compose-override",
        )
        assert m.adapter_framework == "fastapi"
        assert m.infra_mode == "docker-compose-override"
        assert m.discovery is not None


class TestPlugConfig:
    def test_is_plug_mode(self, plug_config):
        assert plug_config.is_plug_mode is True

    def test_not_plug_mode_by_default(self, tmp_path: Path):
        config = IgnitionConfig(
            project_name="test",
            work_dir=tmp_path,
        )
        assert config.is_plug_mode is False


class TestVerifyPlug:
    def test_passes_with_all_files(self, plug_prd, plug_discovery, plug_config):
        from ignition.stages.scaffold.agents import scaffold_agents
        from ignition.stages.scaffold.ralph import scaffold_ralph
        from ignition.stages.scaffold.skills import scaffold_skills

        work = plug_config.work_dir
        # Generate plug artifacts
        scaffold_plug(plug_prd, plug_discovery, plug_config)
        scaffold_agents(plug_prd, plug_config)
        scaffold_ralph(plug_prd, plug_config)
        scaffold_skills(plug_prd, plug_config, discovery=plug_discovery)

        # Also need PRD.json, progress.txt, discovery.json
        from ignition.stages.discovery import save_discovery
        from ignition.stages.prd import init_progress, save_prd

        save_prd(plug_prd, work)
        init_progress(work, plug_prd)
        save_discovery(plug_discovery, work)

        issues = verify_plug_output(work)
        assert issues == [], f"Unexpected issues: {issues}"

    def test_reports_missing_files(self, tmp_path: Path):
        work = tmp_path / "empty-plug"
        work.mkdir()
        issues = verify_plug_output(work)
        assert len(issues) > 0
        assert any("Missing" in i for i in issues)
