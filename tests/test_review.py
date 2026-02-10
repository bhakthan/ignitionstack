"""Tests for the review gate stage."""

import json
from unittest.mock import MagicMock, patch

from ignition.compound import CompoundState, ReviewSeverity
from ignition.models import Task, TaskCategory
from ignition.stages.review import (
    _parse_review_report,
    apply_review_to_state,
    save_review_report,
)


class TestParseReviewReport:
    def test_parses_findings(self):
        task = Task(
            id=1,
            title="Test task",
            category=TaskCategory.BACKEND,
            description="Test",
        )
        data = {
            "findings": [
                {
                    "category": "technical-debt",
                    "severity": "blocker",
                    "description": "Hardcoded DB URL",
                    "location": "config.py",
                    "suggestion": "Use env variable",
                },
                {
                    "category": "quality",
                    "severity": "info",
                    "description": "Could add docstring",
                },
            ],
            "technical_debt_score": 35.0,
            "passed": False,
        }
        report = _parse_review_report(task, 1, data)
        assert len(report.findings) == 2
        assert len(report.blockers) == 1
        assert report.technical_debt_score == 35.0
        # Has blockers so should not pass
        assert report.passed is False

    def test_handles_invalid_severity(self):
        task = Task(
            id=1,
            title="Test",
            category=TaskCategory.BACKEND,
            description="Test",
        )
        data = {
            "findings": [
                {
                    "category": "quality",
                    "severity": "nonexistent",
                    "description": "Something",
                },
            ],
            "technical_debt_score": 0,
        }
        report = _parse_review_report(task, 1, data)
        assert report.findings[0].severity == ReviewSeverity.INFO


class TestApplyReviewToState:
    def test_adds_debt_items(self):
        state = CompoundState(project_name="test")
        from ignition.compound import ReviewFinding, ReviewReport

        report = ReviewReport(
            iteration=1,
            task_id=1,
            task_title="Test",
            findings=[
                ReviewFinding(
                    category="technical-debt",
                    severity=ReviewSeverity.WARNING,
                    description="Missing test",
                ),
                ReviewFinding(
                    category="quality",
                    severity=ReviewSeverity.INFO,
                    description="Naming",
                ),
            ],
        )
        apply_review_to_state(report, state)
        assert len(state.review_reports) == 1
        # Only warning (not info) should become debt
        assert len(state.debt_ledger.items) == 1
        assert state.debt_ledger.items[0].category == "technical-debt"


class TestSaveReviewReport:
    def test_saves_to_reviews_dir(self, tmp_work_dir):
        from ignition.compound import ReviewReport

        report = ReviewReport(
            iteration=3,
            task_id=1,
            task_title="Test",
            technical_debt_score=15.0,
        )
        path = save_review_report(report, tmp_work_dir)
        assert path.exists()
        assert "review-iter-3" in path.name
        data = json.loads(path.read_text())
        assert data["iteration"] == 3
