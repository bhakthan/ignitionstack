"""Tests for the parser stage (text extraction only — no LLM calls)."""

from pathlib import Path

from ignition.models import InputType
from ignition.stages.parser import extract_raw_text


class TestExtractRawText:
    def test_extract_text_file(self, tmp_path: Path):
        f = tmp_path / "use-case.txt"
        f.write_text("Build a patient intake portal.", encoding="utf-8")
        result = extract_raw_text(f, InputType.TEXT)
        assert "patient intake portal" in result

    def test_extract_text_preserves_newlines(self, tmp_path: Path):
        content = "Line 1\nLine 2\nLine 3"
        f = tmp_path / "multi.txt"
        f.write_text(content, encoding="utf-8")
        result = extract_raw_text(f, InputType.TEXT)
        assert result == content
