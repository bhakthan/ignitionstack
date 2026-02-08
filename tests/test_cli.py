"""Tests for the CLI entry point."""

from click.testing import CliRunner

from ignition.cli import main


class TestCLI:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "IgnitionStack" in result.output

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "IgnitionStack" in result.output

    def test_run_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.output
        assert "--tutorial" in result.output
        assert "--local" in result.output

    def test_verify_missing_dir(self):
        runner = CliRunner()
        result = runner.invoke(main, ["verify", "/nonexistent/path"])
        assert result.exit_code != 0

    def test_example_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["example", "--help"])
        assert result.exit_code == 0
        assert "healthcare" in result.output
