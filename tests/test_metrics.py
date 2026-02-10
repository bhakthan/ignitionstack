"""Tests for compound engineering metrics."""

from ignition.compound import (
    CompoundState,
    DebtItem,
    EngineeringPattern,
    PatternType,
    PlanningReport,
    ReviewReport,
    ReviewSeverity,
    SprintRetrospective,
    TechnicalDebtLedger,
)
from ignition.metrics import (
    compute_metrics,
    generate_metrics_report,
    save_metrics_report,
)


class TestComputeMetrics:
    def test_baseline_metrics(self):
        state = CompoundState(project_name="test")
        m = compute_metrics(state)
        assert m["project"] == "test"
        assert m["self_improvement"]["score"] == 50.0

    def test_improving_metrics(self):
        state = CompoundState(
            project_name="test",
            planning_score_trend=[60.0, 70.0, 80.0],
            debt_score_trend=[30.0, 20.0, 10.0],
        )
        # Add some review reports that pass
        for i in range(5):
            state.review_reports.append(
                ReviewReport(
                    iteration=i,
                    task_id=i,
                    task_title=f"T{i}",
                    passed=True,
                ),
            )
        m = compute_metrics(state)
        assert m["self_improvement"]["score"] > 50.0
        assert m["self_improvement"]["is_improving"] is True
        assert m["review"]["pass_rate"] == 100.0

    def test_declining_metrics(self):
        state = CompoundState(
            project_name="test",
            planning_score_trend=[80.0, 70.0, 50.0],
            debt_score_trend=[10.0, 20.0, 40.0],
        )
        m = compute_metrics(state)
        assert m["self_improvement"]["score"] < 50.0
        assert "planning-declining" in m["self_improvement"]["signals"]
        assert "debt-increasing" in m["self_improvement"]["signals"]


class TestGenerateReport:
    def test_generates_readable_report(self):
        state = CompoundState(
            project_name="test-project",
            current_sprint=3,
            total_iterations=30,
            planning_score_trend=[65.0, 75.0, 82.0],
            debt_score_trend=[25.0, 18.0, 12.0],
        )
        report = generate_metrics_report(state)
        assert "test-project" in report
        assert "Planning Quality" in report
        assert "Technical Debt" in report
        assert "Self-Improvement Score" in report

    def test_save_metrics_report(self, tmp_work_dir):
        state = CompoundState(project_name="test")
        path = save_metrics_report(state, tmp_work_dir)
        assert path.exists()
        assert path.name == "compound-metrics.md"
        content = path.read_text()
        assert "Compound Engineering Metrics" in content
