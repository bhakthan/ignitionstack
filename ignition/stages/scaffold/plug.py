"""Scaffold: Plug Mode — generates additive integration artifacts."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ignition.config import IgnitionConfig
from ignition.models import PRD, DiscoveryResult

TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "templates"
)


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
    )


def scaffold_plug(
    prd: PRD,
    discovery: DiscoveryResult,
    config: IgnitionConfig,
) -> list[str]:
    """Generate all plug integration artifacts."""
    work = config.ensure_work_dir()
    files: list[str] = []

    files.extend(_scaffold_adapters(prd, discovery, work))
    files.extend(_scaffold_infra_delta(prd, discovery, config, work))
    files.extend(_scaffold_db_delta(prd, discovery, work))
    files.extend(_scaffold_cicd_patch(prd, discovery, work))

    return files


# ---------------------------------------------------------------------------
# Adapters — middleware + RAG connector
# ---------------------------------------------------------------------------

def _scaffold_adapters(
    prd: PRD, discovery: DiscoveryResult, work: Path,
) -> list[str]:
    """Generate adapter middleware appropriate for the detected framework."""
    adapters_dir = work / "adapters"
    adapters_dir.mkdir(parents=True, exist_ok=True)
    files: list[str] = []

    env = _get_jinja_env()
    ctx = {
        "project_name": prd.project_name,
        "domain": prd.domain,
        "framework": discovery.framework,
        "language": discovery.language,
        "auth": discovery.auth,
        "endpoints": discovery.api_endpoints,
    }

    # Agent middleware
    try:
        tpl = env.get_template("plug/agent_middleware.py.j2")
        dest = adapters_dir / "agent_middleware.py"
        dest.write_text(tpl.render(**ctx), encoding="utf-8")
    except Exception:
        dest = adapters_dir / "agent_middleware.py"
        dest.write_text(
            _inline_agent_middleware(prd, discovery), encoding="utf-8",
        )
    files.append(str(dest.relative_to(work)))

    # RAG connector
    try:
        tpl = env.get_template("plug/rag_connector.py.j2")
        dest = adapters_dir / "rag_connector.py"
        dest.write_text(tpl.render(**ctx), encoding="utf-8")
    except Exception:
        dest = adapters_dir / "rag_connector.py"
        dest.write_text(
            _inline_rag_connector(prd, discovery), encoding="utf-8",
        )
    files.append(str(dest.relative_to(work)))

    # Integration README
    dest = adapters_dir / "README.md"
    dest.write_text(
        _adapters_readme(prd, discovery), encoding="utf-8",
    )
    files.append(str(dest.relative_to(work)))

    return files


# ---------------------------------------------------------------------------
# Infrastructure delta
# ---------------------------------------------------------------------------

def _scaffold_infra_delta(
    prd: PRD,
    discovery: DiscoveryResult,
    config: IgnitionConfig,
    work: Path,
) -> list[str]:
    """Generate incremental infra (Bicep delta or docker-compose override)."""
    infra_dir = work / "infra-delta"
    infra_dir.mkdir(parents=True, exist_ok=True)
    files: list[str] = []
    env = _get_jinja_env()

    ctx = {
        "project_name": prd.project_name,
        "location": config.azure_location,
        "domain": prd.domain,
        "existing_deployment": discovery.deployment,
    }

    if config.local_mode:
        # Docker Compose override
        try:
            tpl = env.get_template(
                "plug/docker-compose.override.yml.j2",
            )
            content = tpl.render(**ctx)
        except Exception:
            content = _inline_compose_override(prd)
        dest = infra_dir / "docker-compose.override.yml"
        dest.write_text(content, encoding="utf-8")
        files.append(str(dest.relative_to(work)))
    else:
        # Bicep delta
        try:
            tpl = env.get_template("plug/delta.bicep.j2")
            content = tpl.render(**ctx)
        except Exception:
            content = _inline_delta_bicep(prd, config)
        dest = infra_dir / "delta.bicep"
        dest.write_text(content, encoding="utf-8")
        files.append(str(dest.relative_to(work)))

    return files


# ---------------------------------------------------------------------------
# Database delta
# ---------------------------------------------------------------------------

def _scaffold_db_delta(
    prd: PRD, discovery: DiscoveryResult, work: Path,
) -> list[str]:
    """Generate additive database migration for agent state."""
    db_dir = work / "db-delta"
    db_dir.mkdir(parents=True, exist_ok=True)

    env = _get_jinja_env()
    ctx = {
        "project_name": prd.project_name,
        "domain": prd.domain,
        "database": discovery.database,
    }

    try:
        tpl = env.get_template("plug/001_agent_state.sql.j2")
        content = tpl.render(**ctx)
    except Exception:
        content = _inline_agent_state_sql(prd)

    dest = db_dir / "001_agent_state.sql"
    dest.write_text(content, encoding="utf-8")
    return [str(dest.relative_to(work))]


# ---------------------------------------------------------------------------
# CI/CD patch
# ---------------------------------------------------------------------------

def _scaffold_cicd_patch(
    prd: PRD, discovery: DiscoveryResult, work: Path,
) -> list[str]:
    """Generate CI/CD steps to merge into existing pipeline."""
    cicd_dir = work / "cicd-patch"
    cicd_dir.mkdir(parents=True, exist_ok=True)

    env = _get_jinja_env()
    ctx = {
        "project_name": prd.project_name,
        "domain": prd.domain,
        "cicd": discovery.cicd,
    }

    try:
        tpl = env.get_template("plug/ai-steps.yml.j2")
        content = tpl.render(**ctx)
    except Exception:
        content = _inline_ai_steps(prd, discovery)

    dest = cicd_dir / "ai-steps.yml"
    dest.write_text(content, encoding="utf-8")
    return [str(dest.relative_to(work))]


# ===================================================================
# Inline fallback generators (when Jinja2 templates are not found)
# ===================================================================

def _inline_agent_middleware(prd: PRD, disc: DiscoveryResult) -> str:
    name = prd.project_name
    return f'''\
"""Agent Middleware — routes requests to AI agents for {name}.

Drop this into your existing {disc.framework} application to add
agent-powered endpoints alongside your current API surface.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AgentRouter:
    """Lightweight router that delegates to Microsoft Agent Framework."""

    def __init__(self, agent_config_path: str = "agents/agent-config.json"):
        self.config = self._load_config(agent_config_path)

    @staticmethod
    def _load_config(path: str) -> dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Agent config not found at %s — using defaults", path)
            return {{"agents": []}}

    async def route(self, intent: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Route a request to the appropriate agent."""
        # TODO: integrate with Microsoft Agent Framework SDK
        return {{
            "status": "routed",
            "intent": intent,
            "agent": self._pick_agent(intent),
            "payload": payload,
        }}

    def _pick_agent(self, intent: str) -> str:
        """Select the best agent for the given intent."""
        agents = self.config.get("agents", [])
        if not agents:
            return "default"
        return agents[0].get("name", "default")


# --- Framework-specific integration helpers ---

def fastapi_mount(app):
    """Mount agent routes on an existing FastAPI app."""
    from fastapi import Request

    router_instance = AgentRouter()

    @app.post("/api/v1/agents/route")
    async def agent_route(request: Request):
        body = await request.json()
        return await router_instance.route(
            body.get("intent", ""), body.get("payload", {{}}),
        )

    @app.get("/api/v1/agents/health")
    async def agent_health():
        return {{"status": "ok", "agents": len(router_instance.config.get("agents", []))}}


def express_mount():
    """Return snippet for Express.js integration."""
    return """
// Add to your Express app:
// const agentRouter = require('./adapters/agent_middleware');
// app.use('/api/v1/agents', agentRouter);
"""
'''


def _inline_rag_connector(prd: PRD, disc: DiscoveryResult) -> str:
    name = prd.project_name
    return f'''\
"""RAG Connector — bridges your existing data to Azure AI Search for {name}.

This module indexes your existing database content into Azure AI Search,
enabling agentic retrieval-augmented generation over your domain data.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RAGConnector:
    """Connects existing data sources to Azure AI Search for RAG."""

    def __init__(
        self,
        search_endpoint: str = "",
        search_key: str = "",
        index_name: str = "{prd.project_name}-index",
    ):
        self.search_endpoint = search_endpoint
        self.search_key = search_key
        self.index_name = index_name

    async def index_records(self, records: list[dict[str, Any]]) -> int:
        """Index records from the existing database into AI Search."""
        # TODO: implement with azure-search-documents SDK
        logger.info("Indexing %d records into %s", len(records), self.index_name)
        return len(records)

    async def search(self, query: str, top: int = 5) -> list[dict[str, Any]]:
        """Semantic search over indexed content."""
        # TODO: implement with azure-search-documents SDK
        logger.info("Searching '%s' in %s", query, self.index_name)
        return []

    async def hybrid_search(
        self, query: str, filters: dict[str, Any] | None = None, top: int = 5,
    ) -> list[dict[str, Any]]:
        """Hybrid search (keyword + vector) with optional filters."""
        # TODO: implement with azure-search-documents SDK
        return []
'''


def _adapters_readme(prd: PRD, disc: DiscoveryResult) -> str:
    return f"""\
# Adapters — {prd.project_name}

Integration adapters generated by IgnitionStack Plug Mode.

## Detected Stack

| Component | Detected |
|-----------|----------|
| Language  | {disc.language} |
| Framework | {disc.framework} |
| Database  | {disc.database} |
| Auth      | {disc.auth} |

## Files

| File | Purpose |
|------|---------|
| `agent_middleware.py` | Agent routing middleware — mount on your existing app |
| `rag_connector.py`   | RAG pipeline connecting your data to Azure AI Search |

## Integration Steps

1. Copy `agent_middleware.py` into your project
2. Mount the agent routes on your existing app
3. Configure `agents/agent-config.json` with your model and API keys
4. Copy `rag_connector.py` and wire it to your database
5. Run the Ralph loop to implement remaining tasks
"""


def _inline_compose_override(prd: PRD) -> str:
    name = prd.project_name.replace("-", "_")
    usage = (
        "docker compose -f docker-compose.yml "
        "-f ignition-plug/infra-delta/docker-compose.override.yml up"
    )
    return f"""\
# Docker Compose Override \u2014 AI sidecar for {prd.project_name}
# Usage: {usage}
services:
  ai-search:
    image: mcr.microsoft.com/azure-cognitive-services/textanalytics/healthcare:latest
    ports:
      - "5001:5000"
    environment:
      - EULA=accept

  redis-agent-state:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  agent-sidecar:
    build:
      context: ../adapters
      dockerfile: Dockerfile
    depends_on:
      - redis-agent-state
    environment:
      - REDIS_URL=redis://redis-agent-state:6379
      - PROJECT_NAME={name}
"""


def _inline_delta_bicep(prd: PRD, config: IgnitionConfig) -> str:
    return f"""\
// delta.bicep — Incremental AI resources for {prd.project_name}
// Deploy alongside your existing infrastructure.
// az deployment group create --resource-group <rg> --template-file delta.bicep

targetScope = 'resourceGroup'

param location string = '{config.azure_location}'
param projectName string = '{prd.project_name}'

// --- Microsoft Foundry Workspace ---
resource aiWorkspace 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {{
  name: '${{projectName}}-ai'
  location: location
  kind: 'hub'
  identity: {{ type: 'SystemAssigned' }}
  properties: {{}}
}}

// --- Azure AI Search (agentic RAG) ---
resource search 'Microsoft.Search/searchServices@2024-03-01-preview' = {{
  name: '${{projectName}}-search'
  location: location
  sku: {{ name: 'basic' }}
  properties: {{
    replicaCount: 1
    partitionCount: 1
  }}
}}

// --- Key Vault entries for AI keys ---
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' existing = {{
  name: '${{projectName}}-kv'
}}

resource aiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {{
  parent: kv
  name: 'ai-search-key'
  properties: {{
    value: search.listAdminKeys().primaryKey
  }}
}}

// --- Application Insights (agent telemetry) ---
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {{
  name: '${{projectName}}-ai-insights'
  location: location
  kind: 'web'
  properties: {{
    Application_Type: 'web'
  }}
}}
"""


def _inline_agent_state_sql(prd: PRD) -> str:
    return f"""\
-- Agent State Migration — {prd.project_name}
-- Additive tables for agent conversation history and state management.
-- Run this AFTER your existing migrations.

CREATE TABLE IF NOT EXISTS agent_conversations (
    id              SERIAL PRIMARY KEY,
    session_id      UUID NOT NULL DEFAULT gen_random_uuid(),
    agent_name      VARCHAR(100) NOT NULL,
    user_id         VARCHAR(255),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{{}}'::jsonb
);

CREATE TABLE IF NOT EXISTS agent_messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES agent_conversations(id),
    role            VARCHAR(20) NOT NULL CHECK (role IN ('user','assistant','system','tool')),
    content         TEXT NOT NULL,
    tool_calls      JSONB,
    tokens_used     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_state (
    id              SERIAL PRIMARY KEY,
    agent_name      VARCHAR(100) NOT NULL,
    state_key       VARCHAR(255) NOT NULL,
    state_value     JSONB NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (agent_name, state_key)
);

CREATE INDEX IF NOT EXISTS idx_conversations_session
    ON agent_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON agent_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_state_lookup
    ON agent_state(agent_name, state_key);
"""


def _inline_ai_steps(prd: PRD, disc: DiscoveryResult) -> str:
    return f"""\
# AI Integration Steps — merge into your existing CI/CD pipeline
# Detected CI/CD: {disc.cicd}
#
# Copy these steps into your workflow file.

name: ai-integration

# Add these steps to your existing build job:
steps:
  - name: Deploy AI Infrastructure
    if: github.ref == 'refs/heads/main'
    run: |
      az deployment group create \\
        --resource-group ${{{{ env.RESOURCE_GROUP }}}} \\
        --template-file ignition-plug/infra-delta/delta.bicep

  - name: Run Agent State Migration
    run: |
      psql "${{{{ secrets.DATABASE_URL }}}}" \\
        -f ignition-plug/db-delta/001_agent_state.sql

  - name: Test Agent Endpoints
    run: |
      curl -sf http://localhost:8000/api/v1/agents/health

  - name: Index Data for RAG
    run: |
      python -m adapters.rag_connector --index
"""
