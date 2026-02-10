"""Tests for the reflection/compound stage."""

import json
from unittest.mock import MagicMock, patch

from ignition.compound import (
    CompoundState,
    EngineeringPattern,
    PatternType,
    SprintRetrospective,
)
from ignition.stages.reflection import (
    _parse_retrospective,
    generate_feed_forward_prompt,
    save_retrospective,
)


class TestParseRetrospective:
    def test_parses_llm_response(self, sample_prd):
        state = CompoundState(project_name="test", total_iterations=5)
        data = {
            "successes": ["Good decomposition", "Tests caught issues early"],
            "failures": ["Missed integration test"],
            "surprises": ["Database migration was easier than expected"],
            "new_patterns": [
                {
                    "id": "test-first",
                    "pattern_type": "success",
                    "title": "Test-first approach",
                    "description": "Writing tests before implementation",
                    "context": "All backend tasks",
                },
                {
                    "id": "skip-integration",
                    "pattern_type": "anti_pattern",
                    "title": "Skipping integration tests",
                    "description": "Led to runtime errors",
                    "context": "Multi-service tasks",
                },
            ],
            "reinforced_pattern_ids": [],
            "planning_improvements": ["Add integration test step"],
            "process_improvements": ["Run smoke test after each iteration"],
            "knowledge_gaps": ["Need to learn about caching strategies"],
        }
        retro = _parse_retrospective(sample_prd, state, data)
        assert len(retro.successes) == 2
        assert len(retro.failures) == 1
        assert len(retro.new_patterns) == 2
        assert retro.new_patterns[0].pattern_type == PatternType.SUCCESS
        assert retro.new_patterns[1].pattern_type == PatternType.ANTI_PATTERN
        assert "Add integration test step" in retro.planning_improvements


class TestGenerateFeedForward:
    def test_empty_feed_forward(self):
        state = CompoundState(project_name="test")
        prompt = generate_feed_forward_prompt(state)
        assert prompt == ""

    def test_generates_prompt_from_state(self):
        state = CompoundState(
            project_name="test",
            feed_forward={
                "last_sprint": 1,
                "completion_rate": 75.0,
                "planning_improvements": ["Be more specific about error handling"],
                "process_improvements": ["Run tests first"],
                "top_patterns": [
                    {"title": "Test-first", "description": "Write tests before code"},
                ],
                "anti_patterns": [
                    {"title": "Skip integration", "description": "Causes runtime errors"},
                ],
                "knowledge_gaps": ["Caching strategies"],
                "open_debt_count": 3,
                "debt_score": 15.0,
            },
        )
        prompt = generate_feed_forward_prompt(state)
        assert "Feed-Forward Context" in prompt
        assert "Be more specific about error handling" in prompt
        assert "Test-first" in prompt
        assert "Skip integration" in prompt
        assert "Caching strategies" in prompt
        assert "3 open items" in prompt


class TestSaveRetrospective:
    def test_saves_to_retrospectives_dir(self, tmp_work_dir):
        retro = SprintRetrospective(
            sprint_number=2,
            tasks_completed=8,
            tasks_total=10,
            successes=["Good velocity"],
        )
        path = save_retrospective(retro, tmp_work_dir)
        assert path.exists()
        assert "sprint-2" in path.name
        data = json.loads(path.read_text())
        assert data["sprint_number"] == 2
        assert data["tasks_completed"] == 8


class TestSprintRetrospective:
    def test_completion_rate(self):
        retro = SprintRetrospective(
            sprint_number=1,
            tasks_completed=7,
            tasks_total=10,
        )
        assert retro.completion_rate == 70.0

    def test_completion_rate_zero_tasks(self):
        retro = SprintRetrospective(sprint_number=1)
        assert retro.completion_rate == 0.0
