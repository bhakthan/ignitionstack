"""Tests for the Discovery stage — project stack detection."""

from pathlib import Path

import pytest

from ignition.models import DiscoveryResult
from ignition.stages.discovery import (
    discover,
    save_discovery,
)


class TestDiscoveryLanguage:
    def test_detects_python(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("fastapi\n")
        result = discover(tmp_path)
        assert result.language == "python"

    def test_detects_typescript(self, tmp_path: Path):
        (tmp_path / "tsconfig.json").write_text("{}")
        (tmp_path / "package.json").write_text('{"dependencies":{}}')
        result = discover(tmp_path)
        assert result.language == "typescript"

    def test_detects_javascript(self, tmp_path: Path):
        (tmp_path / "package.json").write_text('{"dependencies":{}}')
        result = discover(tmp_path)
        assert result.language == "javascript"

    def test_detects_csharp(self, tmp_path: Path):
        (tmp_path / "MyApp.csproj").write_text("<Project></Project>")
        result = discover(tmp_path)
        assert result.language == "csharp"

    def test_detects_java(self, tmp_path: Path):
        (tmp_path / "pom.xml").write_text("<project></project>")
        result = discover(tmp_path)
        assert result.language == "java"

    def test_unknown_for_empty_dir(self, tmp_path: Path):
        result = discover(tmp_path)
        assert result.language == "unknown"


class TestDiscoveryFramework:
    def test_detects_fastapi(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("fastapi\n")
        src = tmp_path / "main.py"
        src.write_text("from fastapi import FastAPI\napp = FastAPI()\n")
        result = discover(tmp_path)
        assert result.framework == "fastapi"

    def test_detects_flask(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("flask\n")
        src = tmp_path / "app.py"
        src.write_text("from flask import Flask\napp = Flask(__name__)\n")
        result = discover(tmp_path)
        assert result.framework == "flask"

    def test_detects_express(self, tmp_path: Path):
        pkg = {"dependencies": {"express": "^4.18"}}
        (tmp_path / "package.json").write_text(
            __import__("json").dumps(pkg)
        )
        result = discover(tmp_path)
        assert result.framework == "express"

    def test_detects_nextjs(self, tmp_path: Path):
        pkg = {"dependencies": {"next": "^14"}}
        (tmp_path / "package.json").write_text(
            __import__("json").dumps(pkg)
        )
        result = discover(tmp_path)
        assert result.framework == "nextjs"

    def test_detects_spring_boot(self, tmp_path: Path):
        (tmp_path / "pom.xml").write_text(
            "<project><dependency>spring-boot-starter</dependency></project>"
        )
        result = discover(tmp_path)
        assert result.framework == "spring-boot"


class TestDiscoveryDatabase:
    def test_detects_postgresql(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("psycopg2\n")
        src = tmp_path / "db.py"
        src.write_text("import asyncpg\nconn = asyncpg.connect('postgresql://...')\n")
        result = discover(tmp_path)
        assert result.database == "postgresql"

    def test_detects_mongodb(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("pymongo\n")
        src = tmp_path / "db.py"
        src.write_text("from pymongo import MongoClient\n")
        result = discover(tmp_path)
        assert result.database == "mongodb"


class TestDiscoveryDeployment:
    def test_detects_bicep(self, tmp_path: Path):
        infra = tmp_path / "infra"
        infra.mkdir()
        (infra / "main.bicep").write_text("targetScope = 'subscription'\n")
        result = discover(tmp_path)
        assert result.deployment == "bicep"

    def test_detects_terraform(self, tmp_path: Path):
        (tmp_path / "main.tf").write_text("provider \"azurerm\" {}\n")
        result = discover(tmp_path)
        assert result.deployment == "terraform"

    def test_detects_docker_compose(self, tmp_path: Path):
        (tmp_path / "docker-compose.yml").write_text("services:\n  app:\n    image: node\n")
        result = discover(tmp_path)
        assert result.deployment == "docker-compose"


class TestDiscoveryCICD:
    def test_detects_github_actions(self, tmp_path: Path):
        wf = tmp_path / ".github" / "workflows"
        wf.mkdir(parents=True)
        (wf / "ci.yml").write_text("name: CI\non: push\n")
        result = discover(tmp_path)
        assert result.cicd == "github-actions"

    def test_detects_azure_pipelines(self, tmp_path: Path):
        (tmp_path / "azure-pipelines.yml").write_text("trigger: main\n")
        result = discover(tmp_path)
        assert result.cicd == "azure-pipelines"


class TestDiscoveryAuth:
    def test_detects_jwt(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("pyjwt\n")
        src = tmp_path / "auth.py"
        src.write_text("import jwt\ntoken = jwt.decode(...)\n")
        result = discover(tmp_path)
        assert result.auth == "jwt"

    def test_detects_azure_ad(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("msal\n")
        src = tmp_path / "auth.py"
        src.write_text("import msal\napp = msal.ConfidentialClientApplication(...)\n")
        result = discover(tmp_path)
        assert result.auth == "azure-ad"


class TestDiscoveryEndpoints:
    def test_detects_fastapi_routes(self, tmp_path: Path):
        (tmp_path / "requirements.txt").write_text("fastapi\n")
        src = tmp_path / "main.py"
        src.write_text(
            'from fastapi import FastAPI\n'
            'app = FastAPI()\n'
            '@app.get("/api/v1/health")\n'
            'def health(): return {"ok": True}\n'
            '@app.post("/api/v1/users")\n'
            'def create_user(): pass\n'
        )
        result = discover(tmp_path)
        assert "GET /api/v1/health" in result.api_endpoints
        assert "POST /api/v1/users" in result.api_endpoints


class TestDiscoverySave:
    def test_saves_discovery_json(self, tmp_path: Path):
        result = DiscoveryResult(
            target_path=str(tmp_path),
            language="python",
            framework="fastapi",
        )
        dest = save_discovery(result, tmp_path / "output")
        assert dest.exists()
        assert "python" in dest.read_text(encoding="utf-8")


class TestDiscoveryResult:
    def test_stack_summary(self):
        r = DiscoveryResult(
            target_path="/fake",
            language="python",
            framework="fastapi",
            database="postgresql",
        )
        assert r.stack_summary == "python + fastapi + postgresql"

    def test_stack_summary_unknowns_excluded(self):
        r = DiscoveryResult(target_path="/fake", language="python")
        assert r.stack_summary == "python"

    def test_raises_for_nonexistent_dir(self):
        with pytest.raises(FileNotFoundError):
            discover(Path("/nonexistent/path/that/does/not/exist"))
