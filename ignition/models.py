"""Core data models for the IgnitionStack pipeline."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Input types
# ---------------------------------------------------------------------------

class InputType(StrEnum):
    """Supported input file types."""

    TEXT = "text"
    PDF = "pdf"
    PPTX = "pptx"
    DOCX = "docx"
    IMAGE = "image"  # screenshot / photo


def detect_input_type(path: Path) -> InputType:
    """Detect input type from file extension."""
    ext = path.suffix.lower()
    mapping = {
        ".txt": InputType.TEXT,
        ".md": InputType.TEXT,
        ".pdf": InputType.PDF,
        ".pptx": InputType.PPTX,
        ".ppt": InputType.PPTX,
        ".docx": InputType.DOCX,
        ".doc": InputType.DOCX,
        ".png": InputType.IMAGE,
        ".jpg": InputType.IMAGE,
        ".jpeg": InputType.IMAGE,
        ".gif": InputType.IMAGE,
        ".webp": InputType.IMAGE,
    }
    return mapping.get(ext, InputType.TEXT)


# ---------------------------------------------------------------------------
# Decomposition: Tasks & the T/B/I/C test
# ---------------------------------------------------------------------------

class TaskCategory(StrEnum):
    """High-level category for a decomposed task."""

    INFRA = "infra"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    AGENT = "agent"
    CICD = "cicd"
    DOCS = "docs"
    TEST = "test"


class TaskStatus(StrEnum):
    """Lifecycle status of a task in the PRD."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class Task(BaseModel):
    """A single atomic task that passes the Decomposition Test (T/B/I/C)."""

    id: int = Field(description="Sequential task number (1-based)")
    title: str = Field(description="One-line summary of the task")
    category: TaskCategory
    description: str = Field(description="Detailed specification an LLM can implement from")
    dependencies: list[int] = Field(
        default_factory=list,
        description="IDs of tasks this depends on (empty = independent)",
    )
    status: TaskStatus = TaskStatus.PENDING

    # T/B/I/C validation metadata (set during decomposition)
    testable: bool = True
    bounded: bool = True
    independent: bool = True
    committable: bool = True

    @property
    def passes_tbic(self) -> bool:
        """Check if the task passes all four Decomposition Test gates."""
        return self.testable and self.bounded and self.independent and self.committable


class PRD(BaseModel):
    """
    Product Requirements Document — the prioritized task backlog
    produced by the Decompose + PRD stages.
    """

    project_name: str
    description: str = Field(description="High-level project description from parsed input")
    domain: str = Field(default="general", description="Domain (healthcare, finance, etc.)")
    tasks: list[Task] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra metadata (Azure region, model, constraints)",
    )

    @property
    def pending_tasks(self) -> list[Task]:
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]

    @property
    def next_task(self) -> Task | None:
        """Return the next actionable task (pending + all deps done)."""
        done_ids = {t.id for t in self.tasks if t.status == TaskStatus.DONE}
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                if all(dep in done_ids for dep in task.dependencies):
                    return task
        return None

    @property
    def progress_pct(self) -> float:
        if not self.tasks:
            return 0.0
        done = sum(1 for t in self.tasks if t.status == TaskStatus.DONE)
        return round(done / len(self.tasks) * 100, 1)


# ---------------------------------------------------------------------------
# Parsed requirements (output of Stage 2: Parse)
# ---------------------------------------------------------------------------

class ParsedRequirements(BaseModel):
    """Structured output from the Parser stage."""

    raw_text: str = Field(description="Original extracted text")
    summary: str = Field(description="LLM-generated one-paragraph summary")
    features: list[str] = Field(
        default_factory=list,
        description="Extracted feature list",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Non-functional requirements / constraints",
    )
    domain_hint: str = Field(
        default="general",
        description="Detected domain (healthcare, finance, etc.)",
    )
    actors: list[str] = Field(
        default_factory=list,
        description="Identified user roles / personas",
    )


# ---------------------------------------------------------------------------
# Scaffold output manifest
# ---------------------------------------------------------------------------

class ScaffoldManifest(BaseModel):
    """Tracks all files generated by the Scaffold stage."""

    files: list[str] = Field(default_factory=list, description="Relative paths of generated files")
    infra_template: str = Field(default="bicep", description="bicep | docker-compose")
    agent_framework: str = Field(default="microsoft-agent-framework")
    database_type: str = Field(default="cosmosdb")
    app_framework: str = Field(default="fastapi")
    frontend_framework: str = Field(default="react-vite")


# ---------------------------------------------------------------------------
# Ralph iteration result
# ---------------------------------------------------------------------------

class IterationResult(BaseModel):
    """Result of a single Ralph loop iteration."""

    iteration: int
    task_id: int
    task_title: str
    success: bool
    commit_hash: str = ""
    error: str = ""
    duration_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Discovery result (Plug Mode — Stage 0)
# ---------------------------------------------------------------------------

class DiscoveryResult(BaseModel):
    """Output of the Discovery stage — describes an existing project's stack."""

    target_path: str = Field(description="Absolute path to the scanned project")
    language: str = Field(default="unknown", description="Primary language")
    framework: str = Field(default="unknown", description="Detected web framework")
    database: str = Field(default="unknown", description="Detected database")
    auth: str = Field(default="unknown", description="Detected auth mechanism")
    deployment: str = Field(default="unknown", description="Deployment model")
    cicd: str = Field(default="unknown", description="CI/CD provider")
    api_endpoints: list[str] = Field(
        default_factory=list,
        description="Discovered API endpoints (METHOD /path)",
    )

    @property
    def stack_summary(self) -> str:
        """One-line summary of the detected stack."""
        parts = [self.language, self.framework, self.database]
        return " + ".join(p for p in parts if p != "unknown")


class PlugManifest(BaseModel):
    """Tracks all files generated by the Plug scaffold stage."""

    files: list[str] = Field(
        default_factory=list,
        description="Relative paths of generated plug files",
    )
    discovery: DiscoveryResult | None = None
    adapter_framework: str = Field(
        default="fastapi",
        description="Framework the adapter middleware targets",
    )
    infra_mode: str = Field(
        default="delta-bicep",
        description="delta-bicep | docker-compose-override",
    )

