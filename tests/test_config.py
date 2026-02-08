"""Tests for configuration management."""

import os
from pathlib import Path

from ignition.config import IgnitionConfig


class TestIgnitionConfig:
    def test_defaults(self):
        config = IgnitionConfig()
        expected = os.environ.get("IGNITION_MODEL", "gpt-4o")
        assert config.model == expected
        assert config.azure_location == os.environ.get("AZURE_LOCATION", "eastus2")
        assert config.iterations == int(os.environ.get("IGNITION_ITERATIONS", "20"))
        assert config.local_mode is False
        assert config.tutorial_mode is False

    def test_has_azure_false_when_local(self):
        config = IgnitionConfig(
            azure_subscription_id="sub-123",
            local_mode=True,
        )
        assert config.has_azure is False

    def test_has_azure_true(self):
        config = IgnitionConfig(
            azure_subscription_id="sub-123",
            local_mode=False,
        )
        assert config.has_azure is True

    def test_has_azure_false_when_no_sub(self):
        config = IgnitionConfig(azure_subscription_id="", local_mode=False)
        assert config.has_azure is False

    def test_has_github(self):
        config = IgnitionConfig(github_token="ghp_xxx")
        assert config.has_github is True

    def test_ensure_work_dir(self, tmp_path: Path):
        work = tmp_path / "output"
        config = IgnitionConfig(work_dir=work)
        result = config.ensure_work_dir()
        assert result.exists()
        assert result == work
