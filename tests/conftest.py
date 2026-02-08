"""Shared test fixtures for IgnitionStack."""

from __future__ import annotations

from pathlib import Path

import pytest

from ignition.config import IgnitionConfig
from ignition.models import (
    PRD,
    ParsedRequirements,
    Task,
    TaskCategory,
)


@pytest.fixture
def tmp_work_dir(tmp_path: Path) -> Path:
    """Provide a temporary work directory."""
    work = tmp_path / "test-output"
    work.mkdir()
    return work


@pytest.fixture
def sample_config(tmp_work_dir: Path) -> IgnitionConfig:
    """Config with no real API keys — for unit tests only."""
    return IgnitionConfig(
        openai_api_key="sk-test-fake-key",
        model="gpt-4o",
        project_name="test-project",
        azure_subscription_id="",
        azure_location="eastus2",
        iterations=3,
        work_dir=tmp_work_dir,
        local_mode=True,
        tutorial_mode=False,
        verbose=False,
    )


@pytest.fixture
def sample_requirements() -> ParsedRequirements:
    return ParsedRequirements(
        raw_text="Build a patient intake portal for a hospital network.",
        summary="A patient intake portal with self-service registration, triage, and lab results.",
        features=[
            "Patient self-service registration",
            "Clinical triage agent",
            "Lab results RAG system",
            "Provider dashboard",
        ],
        constraints=["HIPAA compliance", "99.9% uptime SLA"],
        domain_hint="healthcare",
        actors=["Patient", "Nurse", "Physician", "Admin"],
    )


@pytest.fixture
def sample_tasks() -> list[Task]:
    return [
        Task(
            id=1,
            title="Create resource group Bicep module",
            category=TaskCategory.INFRA,
            description="Create rg.bicep that deploys an Azure resource group.",
            dependencies=[],
        ),
        Task(
            id=2,
            title="Create database Bicep module",
            category=TaskCategory.DATABASE,
            description="Create db.bicep for Cosmos DB.",
            dependencies=[1],
        ),
        Task(
            id=3,
            title="Create FastAPI health endpoint",
            category=TaskCategory.BACKEND,
            description="Create main.py with /health endpoint.",
            dependencies=[],
        ),
        Task(
            id=4,
            title="Create patient registration endpoint",
            category=TaskCategory.BACKEND,
            description="POST /api/v1/patients/register",
            dependencies=[2, 3],
        ),
        Task(
            id=5,
            title="Create React frontend scaffold",
            category=TaskCategory.FRONTEND,
            description="Vite + React + TypeScript setup.",
            dependencies=[],
        ),
    ]


@pytest.fixture
def sample_prd(sample_requirements: ParsedRequirements, sample_tasks: list[Task]) -> PRD:
    return PRD(
        project_name="meridian-portal",
        description=sample_requirements.summary,
        domain="healthcare",
        tasks=sample_tasks,
        metadata={"model": "gpt-4o", "iterations": 3},
    )


@pytest.fixture
def examples_dir() -> Path:
    """Path to the examples/ directory."""
    return Path(__file__).resolve().parent.parent / "examples"
