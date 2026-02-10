"""Tests for compound engineering primitives."""

from ignition.compound import (
    CompoundState,
    DebtItem,
    EngineeringPattern,
    PatternLibrary,
    PatternType,
    PlanningDimension,
    PlanningReport,
    PlanningScore,
    ReviewFinding,
    ReviewReport,
    ReviewSeverity,
    SprintRetrospective,
    TaskPlanQuality,
    TechnicalDebtLedger,
)


class TestPlanningQuality:
    def test_task_plan_quality_aggregate_score(self):
        quality = TaskPlanQuality(
            task_id=1,
            task_title="Test task",
            scores=[
                PlanningScore(dimension=PlanningDimension.COMPLETENESS, score=0.8),
                PlanningScore(dimension=PlanningDimension.CLARITY, score=0.9),
                PlanningScore(dimension=PlanningDimension.TESTABILITY, score=0.7),
                PlanningScore(dimension=PlanningDimension.SCOPE, score=1.0),
                PlanningScore(dimension=PlanningDimension.DEPENDENCIES, score=0.8),
            ],
        )
        assert quality.aggregate_score == 84.0
        assert quality.passes is True

    def test_task_plan_quality_fails_below_threshold(self):
        quality = TaskPlanQuality(
            task_id=1,
            task_title="Weak task",
            scores=[
                PlanningScore(dimension=PlanningDimension.COMPLETENESS, score=0.3),
                PlanningScore(dimension=PlanningDimension.CLARITY, score=0.4),
            ],
        )
        assert quality.aggregate_score == 35.0
        assert quality.passes is False

    def test_empty_scores_return_zero(self):
        quality = TaskPlanQuality(task_id=1, task_title="No scores")
        assert quality.aggregate_score == 0.0
        assert quality.passes is False

    def test_planning_report_compute_overall(self):
        report = PlanningReport(
            project_name="test",
            task_assessments=[
                TaskPlanQuality(
                    task_id=1,
                    task_title="T1",
                    scores=[
                        PlanningScore(
                            dimension=PlanningDimension.COMPLETENESS, score=0.8,
                        ),
                    ],
                ),
                TaskPlanQuality(
                    task_id=2,
                    task_title="T2",
                    scores=[
                        PlanningScore(
                            dimension=PlanningDimension.COMPLETENESS, score=0.6,
                        ),
                    ],
                ),
            ],
        )
        report.compute_overall()
        # (80 + 60) / 2 = 70
        assert report.overall_score == 70.0


class TestReviewGate:
    def test_review_report_blockers(self):
        report = ReviewReport(
            iteration=1,
            task_id=1,
            task_title="Test",
            findings=[
                ReviewFinding(
                    category="technical-debt",
                    severity=ReviewSeverity.BLOCKER,
                    description="Critical issue",
                ),
                ReviewFinding(
                    category="quality",
                    severity=ReviewSeverity.WARNING,
                    description="Minor issue",
                ),
            ],
            technical_debt_score=30.0,
        )
        assert len(report.blockers) == 1
        assert len(report.warnings) == 1

    def test_review_evaluate_fails_on_blockers(self):
        report = ReviewReport(
            iteration=1,
            task_id=1,
            task_title="Test",
            findings=[
                ReviewFinding(
                    category="coupling",
                    severity=ReviewSeverity.BLOCKER,
                    description="Circular dep",
                ),
            ],
            technical_debt_score=10.0,
        )
        report.evaluate()
        assert report.passed is False

    def test_review_evaluate_passes_no_blockers(self):
        report = ReviewReport(
            iteration=1,
            task_id=1,
            task_title="Test",
            findings=[
                ReviewFinding(
                    category="quality",
                    severity=ReviewSeverity.INFO,
                    description="Could be better",
                ),
            ],
            technical_debt_score=10.0,
        )
        report.evaluate()
        assert report.passed is True

    def test_review_evaluate_fails_on_high_debt(self):
        report = ReviewReport(
            iteration=1,
            task_id=1,
            task_title="Test",
            findings=[],
            technical_debt_score=75.0,
        )
        report.evaluate()
        assert report.passed is False


class TestTechnicalDebt:
    def test_debt_ledger_scoring(self):
        ledger = TechnicalDebtLedger(
            items=[
                DebtItem(
                    id="d1",
                    category="hardcoded",
                    description="Hardcoded URL",
                    severity=ReviewSeverity.BLOCKER,
                    introduced_iteration=1,
                ),
                DebtItem(
                    id="d2",
                    category="missing-test",
                    description="No unit test",
                    severity=ReviewSeverity.WARNING,
                    introduced_iteration=1,
                ),
            ],
        )
        # blocker=10 + warning=3 = 13
        assert ledger.debt_score == 13.0
        assert len(ledger.open_items) == 2

    def test_debt_resolve(self):
        ledger = TechnicalDebtLedger(
            items=[
                DebtItem(
                    id="d1",
                    category="hardcoded",
                    description="Hardcoded URL",
                    severity=ReviewSeverity.BLOCKER,
                    introduced_iteration=1,
                ),
            ],
        )
        ledger.resolve("d1", iteration=3)
        assert len(ledger.open_items) == 0
        assert len(ledger.resolved_items) == 1
        assert ledger.debt_score == 0.0


class TestPatternLibrary:
    def test_add_pattern(self):
        lib = PatternLibrary()
        pattern = EngineeringPattern(
            id="split-ui",
            pattern_type=PatternType.SUCCESS,
            title="Split UI into components",
            description="Break UI tasks into component + logic + test",
        )
        lib.add_or_reinforce(pattern)
        assert len(lib.patterns) == 1
        assert len(lib.success_patterns) == 1

    def test_reinforce_pattern(self):
        lib = PatternLibrary()
        pattern = EngineeringPattern(
            id="split-ui",
            pattern_type=PatternType.SUCCESS,
            title="Split UI",
            description="Break UI tasks",
            times_observed=1,
        )
        lib.add_or_reinforce(pattern)
        lib.add_or_reinforce(
            EngineeringPattern(
                id="split-ui",
                pattern_type=PatternType.SUCCESS,
                title="Split UI",
                description="Break UI tasks",
                last_seen_iteration=5,
            ),
        )
        assert lib.patterns[0].times_observed == 2
        assert lib.patterns[0].last_seen_iteration == 5

    def test_top_patterns(self):
        lib = PatternLibrary()
        for i in range(15):
            lib.add_or_reinforce(
                EngineeringPattern(
                    id=f"p-{i}",
                    pattern_type=PatternType.SUCCESS,
                    title=f"Pattern {i}",
                    description=f"Desc {i}",
                    times_observed=i,
                ),
            )
        # top_patterns returns max 10
        assert len(lib.top_patterns) == 10
        # Most observed first
        assert lib.top_patterns[0].times_observed == 14


class TestCompoundState:
    def test_save_and_load(self, tmp_work_dir):
        state = CompoundState(project_name="test-proj", current_sprint=2)
        state.pattern_library.add_or_reinforce(
            EngineeringPattern(
                id="test-pattern",
                pattern_type=PatternType.SUCCESS,
                title="Test",
                description="A test pattern",
            ),
        )
        state.save(tmp_work_dir)

        loaded = CompoundState.load(tmp_work_dir)
        assert loaded.project_name == "test-proj"
        assert loaded.current_sprint == 2
        assert len(loaded.pattern_library.patterns) == 1

    def test_load_missing_returns_default(self, tmp_work_dir):
        state = CompoundState.load(tmp_work_dir)
        assert state.project_name == "unknown"
        assert state.current_sprint == 1

    def test_begin_sprint_builds_feed_forward(self):
        state = CompoundState(project_name="test", current_sprint=1)
        retro = SprintRetrospective(
            sprint_number=1,
            tasks_completed=5,
            tasks_total=10,
            planning_improvements=["Be more specific"],
            process_improvements=["Run tests first"],
        )
        state.end_sprint(retro)
        state.begin_sprint()
        assert state.current_sprint == 2
        assert state.feed_forward["last_sprint"] == 1
        assert state.feed_forward["completion_rate"] == 50.0
        assert "Be more specific" in state.feed_forward["planning_improvements"]

    def test_is_improving(self):
        state = CompoundState(
            project_name="test",
            planning_score_trend=[60.0, 70.0, 80.0],
            debt_score_trend=[30.0, 20.0, 10.0],
        )
        assert state.is_improving is True

    def test_is_not_improving(self):
        state = CompoundState(
            project_name="test",
            planning_score_trend=[80.0, 70.0, 60.0],
            debt_score_trend=[10.0, 20.0, 30.0],
        )
        assert state.is_improving is False

    def test_end_sprint_records_trends(self):
        state = CompoundState(project_name="test")
        planning_report = PlanningReport(
            project_name="test",
            overall_score=85.0,
        )
        state.planning_reports.append(planning_report)

        retro = SprintRetrospective(
            sprint_number=1,
            new_patterns=[
                EngineeringPattern(
                    id="new-p",
                    pattern_type=PatternType.SUCCESS,
                    title="New pattern",
                    description="Discovered during sprint",
                ),
            ],
        )
        state.end_sprint(retro)
        assert len(state.retrospectives) == 1
        assert len(state.pattern_library.patterns) == 1
        assert state.planning_score_trend == [85.0]
