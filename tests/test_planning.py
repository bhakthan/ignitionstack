"""Tests for the planning quality stage."""

import json
from unittest.mock import MagicMock, patch

from ignition.compound import (
    CompoundState,
    PlanningDimension,
    PlanningReport,
    PlanningScore,
    TaskPlanQuality,
)
from ignition.stages.planning import (
    _parse_planning_report,
    enrich_tasks_from_planning,
    save_planning_report,
    validate_planning,
)


class TestParsePlanningReport:
    def test_parses_well_formed_response(self):
        data = {
            "assessments": [
                {
                    "task_id": 1,
                    "task_title": "Create health endpoint",
                    "scores": [
                        {"dimension": "completeness", "score": 0.9, "reasoning": "Good"},
                        {"dimension": "clarity", "score": 0.85, "reasoning": "Clear"},
                        {"dimension": "testability", "score": 0.8, "reasoning": "Testable"},
                        {"dimension": "scope", "score": 1.0, "reasoning": "Bounded"},
                        {"dimension": "dependencies", "score": 0.95, "reasoning": "Explicit"},
                    ],
                    "gaps": [],
                    "suggestions": [],
                    "definition_of_done": ["Endpoint returns 200"],
                },
            ],
            "blocking_gaps": [],
        }
        report = _parse_planning_report("test-project", data)
        assert len(report.task_assessments) == 1
        assert report.task_assessments[0].task_id == 1
        assert len(report.task_assessments[0].scores) == 5

    def test_handles_invalid_dimension(self):
        data = {
            "assessments": [
                {
                    "task_id": 1,
                    "task_title": "Test",
                    "scores": [
                        {"dimension": "nonexistent", "score": 0.5},
                        {"dimension": "clarity", "score": 0.8},
                    ],
                    "gaps": [],
                    "suggestions": [],
                    "definition_of_done": [],
                },
            ],
            "blocking_gaps": [],
        }
        report = _parse_planning_report("test", data)
        # Invalid dimension skipped, only clarity remains
        assert len(report.task_assessments[0].scores) == 1

    def test_clamps_out_of_range_scores(self):
        data = {
            "assessments": [
                {
                    "task_id": 1,
                    "task_title": "Test",
                    "scores": [
                        {"dimension": "completeness", "score": 1.5},
                        {"dimension": "clarity", "score": -0.3},
                    ],
                    "gaps": [],
                    "suggestions": [],
                    "definition_of_done": [],
                },
            ],
            "blocking_gaps": [],
        }
        report = _parse_planning_report("test", data)
        scores = {s.dimension: s.score for s in report.task_assessments[0].scores}
        assert scores[PlanningDimension.COMPLETENESS] == 1.0
        assert scores[PlanningDimension.CLARITY] == 0.0


class TestEnrichTasks:
    def test_enriches_low_scoring_tasks(self, sample_prd):
        report = PlanningReport(
            project_name="test",
            task_assessments=[
                TaskPlanQuality(
                    task_id=1,
                    task_title="Task 1",
                    scores=[
                        PlanningScore(
                            dimension=PlanningDimension.COMPLETENESS,
                            score=0.3,
                        ),
                    ],
                    suggestions=["Add error handling spec"],
                    definition_of_done=["Returns 200 on success"],
                    gaps=["Missing test plan"],
                ),
            ],
        )
        enriched = enrich_tasks_from_planning(sample_prd, report)
        task = next(t for t in enriched.tasks if t.id == 1)
        assert "Planning Enrichment" in task.description
        assert "Add error handling spec" in task.description
        assert "Returns 200 on success" in task.description
        assert "Missing test plan" in task.description

    def test_does_not_enrich_passing_tasks(self, sample_prd):
        original_desc = sample_prd.tasks[0].description
        report = PlanningReport(
            project_name="test",
            task_assessments=[
                TaskPlanQuality(
                    task_id=1,
                    task_title="Task 1",
                    scores=[
                        PlanningScore(
                            dimension=PlanningDimension.COMPLETENESS,
                            score=0.9,
                        ),
                    ],
                ),
            ],
        )
        enriched = enrich_tasks_from_planning(sample_prd, report)
        task = next(t for t in enriched.tasks if t.id == 1)
        assert task.description == original_desc


class TestSavePlanningReport:
    def test_saves_json(self, tmp_work_dir):
        report = PlanningReport(
            project_name="test",
            overall_score=85.0,
        )
        path = save_planning_report(report, tmp_work_dir)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["overall_score"] == 85.0


class TestValidatePlanning:
    @patch("ignition.stages.planning.get_client")
    @patch("ignition.stages.planning.chat_json")
    def test_validate_planning_e2e(
        self, mock_chat_json, mock_get_client, sample_prd, sample_config,
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_chat_json.return_value = json.dumps({
            "assessments": [
                {
                    "task_id": t.id,
                    "task_title": t.title,
                    "scores": [
                        {"dimension": "completeness", "score": 0.8},
                        {"dimension": "clarity", "score": 0.9},
                    ],
                    "gaps": [],
                    "suggestions": [],
                    "definition_of_done": ["Done"],
                }
                for t in sample_prd.tasks
            ],
            "blocking_gaps": [],
        })

        report = validate_planning(sample_prd, sample_config)
        assert len(report.task_assessments) == len(sample_prd.tasks)
        assert report.overall_score > 0
