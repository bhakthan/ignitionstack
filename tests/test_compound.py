"""Tests for compound engineering module."""

from datetime import datetime

import pytest

from ignition.compound import (
    CompoundMetrics,
    CompoundSession,
    DebtCategory,
    DebtReport,
    DebtSeverity,
    IterationReflection,
    LearnedPattern,
    MetricsHistory,
    PatternType,
    PlanningDimension,
    PlanningQualityReport,
    ReviewCheckResult,
    ReviewCheckType,
    ReviewGateResult,
    TaskPlanQuality,
    TechnicalDebt,
)


class TestTechnicalDebt:
    """Tests for TechnicalDebt model."""

    def test_create_debt_item(self):
        debt = TechnicalDebt(
            id="debt-1",
            category=DebtCategory.TODO_FIXME,
            severity=DebtSeverity.LOW,
            file_path="src/main.py",
            line_number=42,
            description="TODO: implement error handling",
            suggested_fix="Add try/except block",
            iteration_found=1,
        )
        assert debt.id == "debt-1"
        assert debt.category == DebtCategory.TODO_FIXME
        assert debt.severity == DebtSeverity.LOW
        assert debt.resolved is False

    def test_debt_report(self):
        items = [
            TechnicalDebt(
                id="debt-1",
                category=DebtCategory.TODO_FIXME,
                severity=DebtSeverity.LOW,
                file_path="a.py",
                description="TODO",
            ),
            TechnicalDebt(
                id="debt-2",
                category=DebtCategory.HARDCODED,
                severity=DebtSeverity.MEDIUM,
                file_path="b.py",
                description="Magic number",
            ),
        ]
        report = DebtReport(
            total_items=2,
            by_severity={"low": 1, "medium": 1},
            by_category={"todo_fixme": 1, "hardcoded": 1},
            debt_score=4.0,
            items=items,
            trend="stable",
        )
        assert report.total_items == 2
        assert report.debt_score == 4.0


class TestPlanningQuality:
    """Tests for planning quality models."""

    def test_task_plan_quality(self):
        quality = TaskPlanQuality(
            task_id=1,
            task_title="Create API endpoint",
            scores={
                "completeness": 85,
                "clarity": 90,
                "testability": 75,
            },
            overall_score=83.3,
            gaps=["Missing acceptance criteria"],
            suggestions=["Add clear done criteria"],
            passes_threshold=True,
        )
        assert quality.task_id == 1
        assert quality.overall_score == 83.3
        assert quality.passes_threshold is True

    def test_planning_quality_report(self):
        report = PlanningQualityReport(
            prd_name="test-project",
            total_tasks=10,
            average_score=75.0,
            passing_tasks=7,
            failing_tasks=3,
            threshold=70.0,
        )
        assert report.passing_tasks == 7
        assert report.average_score == 75.0


class TestReviewGate:
    """Tests for review gate models."""

    def test_review_check_result(self):
        check = ReviewCheckResult(
            check_type=ReviewCheckType.CODE_QUALITY,
            passed=True,
            score=85.0,
            findings=["Minor: long function in api.py"],
        )
        assert check.passed is True
        assert check.score == 85.0

    def test_review_gate_result_compute(self):
        checks = [
            ReviewCheckResult(
                check_type=ReviewCheckType.CODE_QUALITY,
                passed=True,
                score=80.0,
            ),
            ReviewCheckResult(
                check_type=ReviewCheckType.TEST_COVERAGE,
                passed=True,
                score=70.0,
            ),
        ]
        gate = ReviewGateResult(
            iteration=1,
            task_id=1,
            task_title="Test task",
            checks=checks,
        )
        gate.compute_result()
        assert gate.overall_passed is True
        assert gate.overall_score == 75.0

    def test_review_gate_blocking_failure(self):
        checks = [
            ReviewCheckResult(
                check_type=ReviewCheckType.SECURITY,
                passed=False,
                score=0.0,
                findings=["Hardcoded password detected"],
                blocking=True,
            ),
        ]
        gate = ReviewGateResult(
            iteration=1,
            task_id=1,
            task_title="Test task",
            checks=checks,
        )
        gate.compute_result()
        assert gate.overall_passed is False
        assert "Hardcoded password detected" in gate.blocking_issues


class TestLearnedPatterns:
    """Tests for self-improvement models."""

    def test_learned_pattern(self):
        pattern = LearnedPattern(
            id="pattern-1",
            pattern_type=PatternType.SUCCESS,
            category="backend",
            description="Test-first development",
            context="When implementing new API endpoints",
            confidence=0.8,
        )
        assert pattern.pattern_type == PatternType.SUCCESS
        assert pattern.confidence == 0.8

    def test_iteration_reflection(self):
        reflection = IterationReflection(
            iteration=5,
            task_id=10,
            task_title="Implement auth",
            success=True,
            what_worked=["Good task breakdown", "Clear acceptance criteria"],
            what_failed=[],
        )
        assert reflection.success is True
        assert len(reflection.what_worked) == 2


class TestCompoundMetrics:
    """Tests for metrics models."""

    def test_compute_compound_score(self):
        metrics = CompoundMetrics(
            project_name="test",
            planning_quality_score=80.0,
            average_review_score=75.0,
            technical_debt_score=5.0,
            patterns_learned=10,
            success_patterns=7,
            anti_patterns=3,
        )
        score = metrics.compute_compound_score()
        assert score > 0
        assert score <= 100

    def test_metrics_history_trend(self):
        history = MetricsHistory(project_name="test")
        for i in range(5):
            metrics = CompoundMetrics(
                project_name="test",
                iteration=i,
                compound_score=60 + i * 5,  # Increasing
            )
            history.snapshots.append(metrics)
        
        trend = history.trend("compound_score")
        assert trend == "improving"


class TestCompoundSession:
    """Tests for session management."""

    def test_create_session(self):
        session = CompoundSession(project_name="my-project")
        assert session.project_name == "my-project"
        assert len(session.pattern_library) == 0

    def test_add_pattern(self):
        session = CompoundSession(project_name="test")
        pattern = LearnedPattern(
            id="p1",
            pattern_type=PatternType.SUCCESS,
            category="backend",
            description="Use dependency injection",
        )
        session.add_pattern(pattern)
        assert len(session.pattern_library) == 1

    def test_get_patterns_for_category(self):
        session = CompoundSession(project_name="test")
        session.pattern_library = [
            LearnedPattern(
                id="p1",
                pattern_type=PatternType.SUCCESS,
                category="backend",
                description="Pattern 1",
                confidence=0.9,
            ),
            LearnedPattern(
                id="p2",
                pattern_type=PatternType.ANTI,
                category="backend",
                description="Pattern 2",
                confidence=0.7,
            ),
            LearnedPattern(
                id="p3",
                pattern_type=PatternType.SUCCESS,
                category="frontend",
                description="Pattern 3",
                confidence=0.8,
            ),
        ]
        
        backend_success = session.get_patterns_for_category("backend", PatternType.SUCCESS)
        assert len(backend_success) == 1
        assert backend_success[0].id == "p1"
