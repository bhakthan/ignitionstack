"""Stage 3.5 — Planning: validate task quality before execution."""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from ignition.compound import (
    PlanningDimension,
    PlanningQualityReport,
    TaskPlanQuality,
)
from ignition.config import IgnitionConfig
from ignition.llm import chat_json, get_client
from ignition.models import PRD, Task

PLANNING_SYSTEM = """\
You are a planning quality assessor for software engineering tasks.

Evaluate each task on these dimensions (score 0-100 each):

1. COMPLETENESS: Are all aspects of the task defined?
   - What needs to be done is clear
   - Expected inputs/outputs are specified
   - Edge cases are considered

2. CLARITY: Is the description unambiguous?
   - No vague terms ("improve", "better", "optimize" without metrics)
   - Technical specifics are included
   - No multiple interpretations possible

3. TESTABILITY: Can success be objectively verified?
   - Acceptance criteria are stated or inferrable
   - A test could be written for this
   - Done/not-done is binary, not subjective

4. SCOPE: Is the task appropriately bounded?
   - Single responsibility
   - Achievable in one iteration (<30 min)
   - Not trying to do too much

5. DEPENDENCIES: Are all dependencies identified?
   - Required tasks listed
   - External dependencies noted
   - No hidden assumptions

6. ACCEPTANCE: Are acceptance criteria clear?
   - Definition of done is explicit
   - Reviewer would know when to approve
   - No ambiguity about completion

For each task, provide:
- scores: object mapping dimension to score (0-100)
- overall_score: weighted average
- gaps: list of specific planning gaps found
- suggestions: how to improve the task definition
- passes_threshold: true if overall_score >= threshold

Respond with JSON:
{
  "assessments": [
    {
      "task_id": 1,
      "task_title": "...",
      "scores": {
        "completeness": 85,
        "clarity": 90,
        "testability": 75,
        "scope": 80,
        "dependencies": 70,
        "acceptance": 65
      },
      "overall_score": 77.5,
      "gaps": ["Missing acceptance criteria", "Vague 'optimize' without target"],
      "suggestions": ["Add specific performance target", "List edge cases"],
      "passes_threshold": true
    }
  ],
  "common_gaps": ["Most tasks lack explicit acceptance criteria"],
  "recommendations": ["Add Definition of Done to each task description"]
}
"""


def assess_planning_quality(
    prd: PRD,
    config: IgnitionConfig,
    client: OpenAI | None = None,
    threshold: float | None = None,
) -> PlanningQualityReport:
    """Assess planning quality for all tasks in the PRD."""
    if client is None:
        client = get_client(config)
    
    if threshold is None:
        threshold = config.planning_threshold
    
    # Build task summary for LLM
    task_summaries = []
    for task in prd.tasks:
        task_summaries.append({
            "id": task.id,
            "title": task.title,
            "category": task.category.value,
            "description": task.description,
            "dependencies": task.dependencies,
            "tbic": {
                "testable": task.testable,
                "bounded": task.bounded,
                "independent": task.independent,
                "committable": task.committable,
            },
        })
    
    user_msg = f"""Project: {prd.project_name}
Domain: {prd.domain}
Description: {prd.description}

Threshold for passing: {threshold}

Tasks to assess:
{json.dumps(task_summaries, indent=2)}

Assess each task's planning quality."""

    result = chat_json(
        client,
        model=config.model,
        system=PLANNING_SYSTEM,
        user=user_msg,
        max_tokens=8192,
    )
    data = json.loads(result)
    
    assessments: list[TaskPlanQuality] = []
    for a in data.get("assessments", []):
        assessments.append(
            TaskPlanQuality(
                task_id=a["task_id"],
                task_title=a.get("task_title", ""),
                scores=a.get("scores", {}),
                overall_score=a.get("overall_score", 0.0),
                gaps=a.get("gaps", []),
                suggestions=a.get("suggestions", []),
                passes_threshold=a.get("passes_threshold", False),
            )
        )
    
    # Calculate aggregate metrics
    passing = [a for a in assessments if a.passes_threshold]
    avg_score = (
        sum(a.overall_score for a in assessments) / len(assessments)
        if assessments else 0.0
    )
    
    return PlanningQualityReport(
        prd_name=prd.project_name,
        total_tasks=len(assessments),
        average_score=avg_score,
        passing_tasks=len(passing),
        failing_tasks=len(assessments) - len(passing),
        threshold=threshold,
        task_assessments=assessments,
        common_gaps=data.get("common_gaps", []),
        recommendations=data.get("recommendations", []),
    )


def assess_single_task(
    task: Task,
    config: IgnitionConfig,
    client: OpenAI | None = None,
    threshold: float | None = None,
) -> TaskPlanQuality:
    """Assess planning quality for a single task."""
    if client is None:
        client = get_client(config)
    
    if threshold is None:
        threshold = config.planning_threshold
    
    user_msg = f"""Assess this single task:

ID: {task.id}
Title: {task.title}
Category: {task.category.value}
Description: {task.description}
Dependencies: {task.dependencies}
T/B/I/C: testable={task.testable}, bounded={task.bounded}, independent={task.independent}, committable={task.committable}

Threshold for passing: {threshold}

Provide assessment in the same JSON format (just one assessment)."""

    result = chat_json(
        client,
        model=config.model,
        system=PLANNING_SYSTEM,
        user=user_msg,
        max_tokens=2048,
    )
    data = json.loads(result)
    
    assessments = data.get("assessments", [])
    if assessments:
        a = assessments[0]
        return TaskPlanQuality(
            task_id=a["task_id"],
            task_title=a.get("task_title", task.title),
            scores=a.get("scores", {}),
            overall_score=a.get("overall_score", 0.0),
            gaps=a.get("gaps", []),
            suggestions=a.get("suggestions", []),
            passes_threshold=a.get("passes_threshold", False),
        )
    
    # Fallback if no assessment returned
    return TaskPlanQuality(
        task_id=task.id,
        task_title=task.title,
        overall_score=0.0,
        gaps=["Assessment failed"],
        passes_threshold=False,
    )


def save_planning_report(report: PlanningQualityReport, work_dir: Path) -> Path:
    """Save the planning quality report to the work directory."""
    compound_dir = work_dir / ".compound"
    compound_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = compound_dir / "planning_report.json"
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return report_path


def load_planning_report(work_dir: Path) -> PlanningQualityReport | None:
    """Load a previously saved planning report."""
    report_path = work_dir / ".compound" / "planning_report.json"
    if report_path.exists():
        return PlanningQualityReport.model_validate_json(report_path.read_text(encoding="utf-8"))
    return None


def get_tasks_needing_improvement(
    report: PlanningQualityReport,
) -> list[TaskPlanQuality]:
    """Get tasks that failed the planning quality threshold."""
    return [a for a in report.task_assessments if not a.passes_threshold]


def generate_improvement_prompt(assessment: TaskPlanQuality) -> str:
    """Generate a prompt to improve a task's definition."""
    prompt_parts = [
        f"Task '{assessment.task_title}' (ID: {assessment.task_id}) needs improvement.",
        f"Current score: {assessment.overall_score:.1f}/100",
        "",
        "Gaps identified:",
    ]
    for gap in assessment.gaps:
        prompt_parts.append(f"  - {gap}")
    
    prompt_parts.extend(["", "Suggestions:"])
    for suggestion in assessment.suggestions:
        prompt_parts.append(f"  - {suggestion}")
    
    prompt_parts.extend([
        "",
        "Please revise the task description to address these gaps.",
    ])
    
    return "\n".join(prompt_parts)
