"""Tests for domain examples — verifies all example files exist and are valid."""

from pathlib import Path

import pytest

DOMAINS = ["healthcare", "finance", "education", "oil-and-gas", "construction", "telco", "retail"]


class TestExamples:
    @pytest.mark.parametrize("domain", DOMAINS)
    def test_use_case_exists(self, examples_dir: Path, domain: str):
        f = examples_dir / domain / "use-case.txt"
        assert f.exists(), f"Missing: examples/{domain}/use-case.txt"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_readme_exists(self, examples_dir: Path, domain: str):
        f = examples_dir / domain / "README.md"
        assert f.exists(), f"Missing: examples/{domain}/README.md"

    @pytest.mark.parametrize("domain", DOMAINS)
    def test_use_case_has_content(self, examples_dir: Path, domain: str):
        f = examples_dir / domain / "use-case.txt"
        content = f.read_text(encoding="utf-8")
        assert len(content) > 200, f"examples/{domain}/use-case.txt too short"
        # Should mention features
        assert "Feature" in content or "feature" in content or "##" in content
