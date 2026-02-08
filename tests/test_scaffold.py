"""Tests for scaffold stages (Bicep, agents, database, app, CI/CD, Ralph)."""

import json

from ignition.stages.scaffold.agents import scaffold_agents
from ignition.stages.scaffold.app import scaffold_app
from ignition.stages.scaffold.bicep import scaffold_infra
from ignition.stages.scaffold.cicd import scaffold_cicd
from ignition.stages.scaffold.database import scaffold_database
from ignition.stages.scaffold.ralph import scaffold_ralph


class TestScaffoldInfra:
    def test_local_mode_generates_docker_compose(self, sample_prd, sample_config):
        sample_config.local_mode = True
        files = scaffold_infra(sample_prd, sample_config)
        assert any("docker-compose" in f for f in files)
        dc = sample_config.work_dir / "docker-compose.yml"
        assert dc.exists()

    def test_azure_mode_generates_bicep(self, sample_prd, sample_config):
        sample_config.local_mode = False
        files = scaffold_infra(sample_prd, sample_config)
        assert any("main.bicep" in f for f in files)


class TestScaffoldAgents:
    def test_generates_agent_config(self, sample_prd, sample_config):
        files = scaffold_agents(sample_prd, sample_config)
        assert len(files) == 1
        config_path = sample_config.work_dir / "agents" / "agent-config.json"
        assert config_path.exists()
        data = json.loads(config_path.read_text())
        assert data["project"] == "meridian-portal"
        assert data["framework"] == "microsoft-agent-framework"
        # Healthcare domain should add compliance-checker
        agent_names = [a["name"] for a in data["agents"]]
        assert "planner" in agent_names
        assert "coder" in agent_names
        assert "compliance-checker" in agent_names

    def test_finance_domain_gets_risk_analyst(self, sample_prd, sample_config):
        sample_prd.domain = "finance"
        scaffold_agents(sample_prd, sample_config)
        config_path = sample_config.work_dir / "agents" / "agent-config.json"
        data = json.loads(config_path.read_text())
        agent_names = [a["name"] for a in data["agents"]]
        assert "risk-analyst" in agent_names


class TestScaffoldDatabase:
    def test_generates_migration_and_seed(self, sample_prd, sample_config):
        files = scaffold_database(sample_prd, sample_config)
        assert len(files) == 2
        migration = sample_config.work_dir / "db" / "migrations" / "001_initial.sql"
        assert migration.exists()
        content = migration.read_text()
        assert "CREATE TABLE" in content


class TestScaffoldApp:
    def test_generates_backend_files(self, sample_prd, sample_config):
        scaffold_app(sample_prd, sample_config)
        backend_main = sample_config.work_dir / "app" / "backend" / "main.py"
        assert backend_main.exists()

    def test_generates_frontend_files(self, sample_prd, sample_config):
        scaffold_app(sample_prd, sample_config)
        pkg = sample_config.work_dir / "app" / "frontend" / "package.json"
        assert pkg.exists()


class TestScaffoldCICD:
    def test_generates_workflow(self, sample_prd, sample_config):
        scaffold_cicd(sample_prd, sample_config)
        wf = sample_config.work_dir / ".github" / "workflows" / "ci-cd.yml"
        assert wf.exists()


class TestScaffoldRalph:
    def test_generates_both_scripts(self, sample_prd, sample_config):
        scaffold_ralph(sample_prd, sample_config)
        assert sample_config.work_dir / "ralph.sh"
        assert sample_config.work_dir / "ralph.ps1"
        sh_content = (sample_config.work_dir / "ralph.sh").read_text(encoding="utf-8")
        assert "ITERATIONS=3" in sh_content  # matches config.iterations
