"""Discovery stage — scans an existing project to detect its stack."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ignition.models import DiscoveryResult

# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _detect_language(root: Path) -> str:
    """Detect primary language from manifest files."""
    markers: list[tuple[str, str]] = [
        ("requirements.txt", "python"),
        ("pyproject.toml", "python"),
        ("setup.py", "python"),
        ("tsconfig.json", "typescript"),
        ("package.json", "javascript"),
        ("go.mod", "go"),
        ("Cargo.toml", "rust"),
        ("pom.xml", "java"),
        ("build.gradle", "java"),
        ("*.csproj", "csharp"),
        ("*.sln", "csharp"),
    ]
    for pattern, lang in markers:
        if "*" in pattern:
            if list(root.glob(pattern)):
                return lang
        elif (root / pattern).exists():
            return lang
    return "unknown"


def _detect_framework(root: Path, language: str) -> str:
    """Detect web framework from imports / config."""
    if language == "python":
        for src in root.rglob("*.py"):
            try:
                text = src.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "fastapi" in text.lower():
                return "fastapi"
            if "from flask" in text or "import flask" in text:
                return "flask"
            if "from django" in text or "import django" in text:
                return "django"

    if language in ("javascript", "typescript"):
        pkg_path = root / "package.json"
        if pkg_path.exists():
            try:
                pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
                deps = {
                    **pkg.get("dependencies", {}),
                    **pkg.get("devDependencies", {}),
                }
                if "next" in deps:
                    return "nextjs"
                if "express" in deps:
                    return "express"
                if "fastify" in deps:
                    return "fastify"
                if "@nestjs/core" in deps:
                    return "nestjs"
            except (json.JSONDecodeError, OSError):
                pass

    if language == "csharp":
        for csproj in root.rglob("*.csproj"):
            try:
                text = csproj.read_text(encoding="utf-8", errors="ignore")
                if "Microsoft.AspNetCore" in text:
                    return "aspnet"
                if "Microsoft.Azure.Functions" in text:
                    return "azure-functions"
            except OSError:
                continue

    if language == "java":
        for build in [root / "pom.xml", root / "build.gradle"]:
            if build.exists():
                try:
                    text = build.read_text(encoding="utf-8", errors="ignore")
                    if "spring-boot" in text:
                        return "spring-boot"
                except OSError:
                    pass

    return "unknown"


def _detect_database(root: Path) -> str:
    """Detect database from config files and connection strings."""
    patterns: list[tuple[str, str]] = [
        (r"cosmosdb|cosmos_db|CosmosClient", "cosmosdb"),
        (r"postgresql|postgres|psycopg|asyncpg", "postgresql"),
        (r"mysql|pymysql|MySql", "mysql"),
        (r"mongodb|pymongo|MongoClient", "mongodb"),
        (r"sqlite|sqlite3", "sqlite"),
        (r"sqlserver|mssql|pyodbc", "sqlserver"),
        (r"duckdb|DuckDB", "duckdb"),
    ]
    for src in _iter_source_files(root):
        try:
            text = src.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern, db in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return db
    return "unknown"


def _detect_auth(root: Path) -> str:
    """Detect auth mechanism from config and code."""
    patterns: list[tuple[str, str]] = [
        (r"azure.ad|azure_ad|AzureAD|msal", "azure-ad"),
        (r"cognito|aws.cognito", "cognito"),
        (r"auth0|Auth0", "auth0"),
        (r"firebase.auth|FirebaseAuth", "firebase"),
        (r"jwt|jsonwebtoken|jose|JWT", "jwt"),
        (r"oauth|OAuth|passport", "oauth"),
    ]
    for src in _iter_source_files(root):
        try:
            text = src.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern, auth in patterns:
            if re.search(pattern, text):
                return auth
    return "unknown"


def _detect_deployment(root: Path) -> str:
    """Detect deployment model from config files."""
    if list(root.rglob("*.bicep")):
        return "bicep"
    if list(root.rglob("*.tf")):
        return "terraform"
    if (root / "docker-compose.yml").exists() or (
        root / "docker-compose.yaml"
    ).exists():
        return "docker-compose"
    if list(root.rglob("Dockerfile")):
        return "docker"
    k8s = list(root.rglob("k8s/")) or list(root.rglob("kubernetes/"))
    if k8s:
        return "kubernetes"
    return "unknown"


def _detect_cicd(root: Path) -> str:
    """Detect CI/CD provider."""
    if (root / ".github" / "workflows").exists():
        return "github-actions"
    if (root / "azure-pipelines.yml").exists():
        return "azure-pipelines"
    if (root / "Jenkinsfile").exists():
        return "jenkins"
    if (root / ".gitlab-ci.yml").exists():
        return "gitlab-ci"
    if (root / ".circleci").exists():
        return "circleci"
    return "unknown"


def _detect_api_endpoints(root: Path, framework: str) -> list[str]:
    """Detect API endpoints from route decorators."""
    endpoints: list[str] = []
    route_patterns = [
        # FastAPI / Flask
        r'@\w+\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']',
        # Express
        r'\.\s*(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']',
        # ASP.NET
        r'\[Http(Get|Post|Put|Delete|Patch)\(\s*["\']?([^"\')\]]*)',
        # Spring Boot
        r'@(Get|Post|Put|Delete|Patch)Mapping\(\s*["\']?([^"\')\]]*)',
    ]
    for src in _iter_source_files(root):
        try:
            text = src.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in route_patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                method = match.group(1).upper()
                path = match.group(2).strip()
                if path:
                    endpoints.append(f"{method} {path}")
    # Deduplicate, cap at 50
    return list(dict.fromkeys(endpoints))[:50]


def _iter_source_files(root: Path):
    """Yield source files, skipping common junk directories."""
    skip = {
        "node_modules", ".venv", "venv", "__pycache__", ".git",
        "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
        "bin", "obj", "target", ".next", ".nuxt",
    }
    for child in root.rglob("*"):
        if any(part in skip for part in child.parts):
            continue
        if child.is_file() and child.suffix in (
            ".py", ".ts", ".js", ".cs", ".java", ".go", ".rs",
            ".json", ".yml", ".yaml", ".toml", ".cfg", ".ini",
            ".xml", ".gradle", ".env",
        ):
            yield child


# ---------------------------------------------------------------------------
# Main discovery entry point
# ---------------------------------------------------------------------------

def discover(target: Path) -> DiscoveryResult:
    """
    Scan an existing project directory and return a DiscoveryResult.

    This is Stage 0 in Plug Mode — it runs before Parse/Decompose to
    understand what already exists so the pipeline generates only additive
    integration artifacts.
    """
    target = target.resolve()
    if not target.is_dir():
        msg = f"Plug target must be a directory: {target}"
        raise FileNotFoundError(msg)

    language = _detect_language(target)
    framework = _detect_framework(target, language)
    database = _detect_database(target)
    auth = _detect_auth(target)
    deployment = _detect_deployment(target)
    cicd = _detect_cicd(target)
    endpoints = _detect_api_endpoints(target, framework)

    return DiscoveryResult(
        target_path=str(target),
        language=language,
        framework=framework,
        database=database,
        auth=auth,
        deployment=deployment,
        cicd=cicd,
        api_endpoints=endpoints,
    )


def save_discovery(result: DiscoveryResult, work_dir: Path) -> Path:
    """Write discovery.json into the work directory."""
    work_dir.mkdir(parents=True, exist_ok=True)
    dest = work_dir / "discovery.json"
    dest.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return dest
