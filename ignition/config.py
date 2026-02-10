"""Configuration management for IgnitionStack."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


class IgnitionConfig(BaseModel):
    """Runtime configuration — populated from .env, CLI flags, or defaults."""

    # LLM — OpenAI direct
    openai_api_key: str = Field(default_factory=lambda: _env("OPENAI_API_KEY"))
    openai_base_url: str = Field(default_factory=lambda: _env("OPENAI_BASE_URL"))
    model: str = Field(default_factory=lambda: _env("IGNITION_MODEL", "gpt-4o"))

    # LLM — Azure AI Foundry (takes precedence over plain OpenAI when set)
    azure_foundry_endpoint: str = Field(
        default_factory=lambda: _env("AZURE_FOUNDRY_ENDPOINT")
    )
    azure_foundry_api_key: str = Field(
        default_factory=lambda: _env("AZURE_FOUNDRY_API_KEY")
    )

    # Azure
    azure_subscription_id: str = Field(default_factory=lambda: _env("AZURE_SUBSCRIPTION_ID"))
    azure_location: str = Field(default_factory=lambda: _env("AZURE_LOCATION", "eastus2"))

    # GitHub
    github_token: str = Field(default_factory=lambda: _env("GITHUB_TOKEN"))

    # Pipeline
    project_name: str = "my-project"
    iterations: int = Field(
        default_factory=lambda: int(_env("IGNITION_ITERATIONS", "20"))
    )
    work_dir: Path = Field(
        default_factory=lambda: Path(_env("IGNITION_WORK_DIR", "./ignition-output"))
    )
    local_mode: bool = False
    tutorial_mode: bool = False
    compound_mode: bool = False  # compound engineering (plan → review → compound)
    verbose: bool = False
    plug_target: Path | None = None  # existing project to enhance (Plug Mode)

    # Compound Engineering settings
    compound_mode: bool = False  # enable compound engineering features
    planning_threshold: float = Field(
        default_factory=lambda: float(_env("IGNITION_PLANNING_THRESHOLD", "70.0"))
    )
    review_threshold: float = Field(
        default_factory=lambda: float(_env("IGNITION_REVIEW_THRESHOLD", "70.0"))
    )
    debt_threshold: float = Field(
        default_factory=lambda: float(_env("IGNITION_DEBT_THRESHOLD", "10.0"))
    )
    compound_data_dir: Path | None = None  # persistent compound data location

    @property
    def has_foundry(self) -> bool:
        """True when Azure AI Foundry credentials are configured."""
        return bool(self.azure_foundry_endpoint and self.azure_foundry_api_key)

    @property
    def has_azure(self) -> bool:
        return bool(self.azure_subscription_id) and not self.local_mode

    @property
    def has_github(self) -> bool:
        return bool(self.github_token)

    @property
    def is_plug_mode(self) -> bool:
        return self.plug_target is not None

    @property
    def is_compound_mode(self) -> bool:
        return self.compound_mode

    def ensure_work_dir(self) -> Path:
        """Create and return the work directory."""
        self.work_dir.mkdir(parents=True, exist_ok=True)
        return self.work_dir

    def ensure_compound_dir(self) -> Path:
        """Create and return the compound data directory."""
        if self.compound_data_dir is None:
            self.compound_data_dir = self.work_dir / ".compound"
        self.compound_data_dir.mkdir(parents=True, exist_ok=True)
        return self.compound_data_dir
