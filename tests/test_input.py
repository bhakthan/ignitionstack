"""Tests for the input validation stage."""

from pathlib import Path

import pytest

from ignition.models import InputType
from ignition.stages.input import validate_input


class TestValidateInput:
    def test_valid_text_file(self, tmp_path: Path):
        f = tmp_path / "use-case.txt"
        f.write_text("Build a portal")
        result = validate_input(f)
        assert result == InputType.TEXT

    def test_valid_pdf_file(self, tmp_path: Path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4")
        result = validate_input(f)
        assert result == InputType.PDF

    def test_missing_file_raises(self, tmp_path: Path):
        f = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            validate_input(f)

    def test_directory_raises(self, tmp_path: Path):
        with pytest.raises(IsADirectoryError):
            validate_input(tmp_path)
