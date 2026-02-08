"""Scaffold: Microsoft Agent Framework configuration."""

from __future__ import annotations

import json

from ignition.config import IgnitionConfig
from ignition.models import PRD


def scaffold_agents(prd: PRD, config: IgnitionConfig) -> list[str]:
    """Generate agent configuration files."""
    work = config.ensure_work_dir()
    agents_dir = work / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Determine agent roles from task categories + domain
    agent_roles = _derive_agent_roles(prd)

    agent_config = {
        "$schema": "https://aka.ms/agent-framework/config-schema",
        "project": prd.project_name,
        "framework": "microsoft-agent-framework",
        "model": config.model,
        "agents": agent_roles,
        "orchestration": {
            "pattern": "router",
            "max_concurrent": 3,
            "timeout_seconds": 120,
        },
        "memory": {
            "type": "conversation",
            "max_tokens": 8192,
        },
        "tools": [
            {"name": "azure_ai_search", "enabled": config.has_azure},
            {"name": "file_system", "enabled": True},
            {"name": "code_interpreter", "enabled": True},
        ],
    }

    dest = agents_dir / "agent-config.json"
    dest.write_text(json.dumps(agent_config, indent=2), encoding="utf-8")
    return [str(dest.relative_to(work))]


def _derive_agent_roles(prd: PRD) -> list[dict]:
    """Create agent role definitions from PRD context."""
    roles = [
        {
            "name": "planner",
            "description": f"Plans and coordinates tasks for the {prd.domain} domain",
            "type": "assistant",
            "instructions": (
                f"You are a senior planner for {prd.project_name}. "
                "Break down user requests into actionable steps and delegate to specialist agents."
            ),
        },
        {
            "name": "coder",
            "description": "Implements features, writes code, and fixes bugs",
            "type": "assistant",
            "instructions": (
                "You are a senior developer. Write clean, tested, production-quality code. "
                "Always include error handling and type hints."
            ),
        },
        {
            "name": "reviewer",
            "description": "Reviews code quality, security, and best practices",
            "type": "assistant",
            "instructions": (
                "You are a code reviewer. Check for security issues, performance problems, "
                "and adherence to project conventions. Be specific and constructive."
            ),
        },
    ]

    # Add domain-specific agents
    domain_agents = {
        "healthcare": {
            "name": "compliance-checker",
            "description": "Validates HIPAA compliance and healthcare data handling",
            "type": "assistant",
            "instructions": (
                "You ensure all code and data handling complies with HIPAA regulations. "
                "Flag any PHI exposure risks."
            ),
        },
        "finance": {
            "name": "risk-analyst",
            "description": "Validates financial calculations and regulatory compliance",
            "type": "assistant",
            "instructions": (
                "You verify financial calculations, risk models, and regulatory compliance. "
                "Flag any issues with data accuracy or audit requirements."
            ),
        },
        "education": {
            "name": "pedagogy-advisor",
            "description": "Ensures educational best practices and accessibility",
            "type": "assistant",
            "instructions": (
                "You review content for pedagogical soundness, accessibility compliance (WCAG), "
                "and learner experience quality."
            ),
        },
        "oil-and-gas": {
            "name": "safety-inspector",
            "description": "Reviews safety protocols and equipment monitoring logic",
            "type": "assistant",
            "instructions": (
                "You validate safety monitoring logic, alert thresholds, and compliance with "
                "industry safety standards (API, OSHA)."
            ),
        },
        "construction": {
            "name": "site-safety-inspector",
            "description": (
                "Validates OSHA compliance, daily safety checklists, and BIM integration"
            ),
            "type": "assistant",
            "instructions": (
                "You ensure all construction workflows comply with OSHA regulations, "
                "validate BIM integration via IFC standards, and review safety protocols."
            ),
        },
        "telco": {
            "name": "network-diagnostician",
            "description": (
                "Correlates network alarms and identifies root cause across RAN/transport/core"
            ),
            "type": "assistant",
            "instructions": (
                "You analyze network events, correlate alarms to identify root cause, "
                "and recommend self-healing actions for known fault patterns."
            ),
        },
        "retail": {
            "name": "demand-planner",
            "description": "Forecasts demand and optimizes inventory across locations",
            "type": "assistant",
            "instructions": (
                "You forecast demand at SKU-location granularity, recommend replenishment, "
                "and flag dead stock or overstock situations across the retail network."
            ),
        },
    }

    if prd.domain in domain_agents:
        roles.append(domain_agents[prd.domain])

    return roles
