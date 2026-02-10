"""Stage 3.5 — Planning: validate plan quality before execution.

Compound Engineering Principle: 80% of effort is in planning and review.
This stage evaluates each task's plan quality across five dimensions:
  - Completeness: Are acceptance criteria, test plans, and dependencies defined?
  - Clarity: Is the specification unambiguous for an LLM to implement?
  - Testability: Can success be objectively verified?
  - Scope: Is the task bounded to a single iteration?
  - Dependencies: Are inter-task dependencies explicit and acyclic?

Tasks that fail quality thresholds get enriched with suggestions before
proceeding to execution.
"""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from ignition.compound import (
    CompoundState,
    PlanningDimension,
    PlanningReport,
    PlanningScore,
    TaskPlanQuality,
)
from ignition.config import IgnitionConfig
from ignition.llm import chat_json, get_client
from ignition.models import PRD, Task

PLANNING_SYSTEM = """\
You are a compound engineering planning quality analyst.

Evaluate each task's plan against five dimensions (score 0.0–1.0):
  1. completeness — acceptance criteria, test plan, error handling defined?
  2. clarity — specification is unambiguous for an LLM agent to implement?
  3. testability — success can be verified by automated test or type check?
  4. scope — bounded to one iteration (<30 min of focused coding)?
  5. dependencies — inter-task deps are explicit, no hidden coupling?

For each task, also produce:
  - gaps: list of missing or unclear items
  - suggestions: specific improvements to make the plan better
  - definition_of_done: 2-4 concrete acceptance criteria

{feed_forward_context}

Respond with JSON:
{{
  "assessments": [
    {{
      "task_id": 1,
      "task_title": "...",
      "scores": [
        {{"dimension": "completeness", "score": 0.85, "reasoning": "..."}},
        {{"dimension": "clarity", "score": 0.9, "reasoning": "..."}},
        {{"dimension": "testability", "score": 0.7, "reasoning": "..."}},
        {{"dimension": "scope", "score": 1.0, "reasoning": "..."}},
        {{"dimension": "dependencies", "score": 0.8, "reasoning": "..."}}
      ],
      "gaps": ["Missing error handling spec", "No test plan"],
      "suggestions": ["Add expected HTTP status codes", "Define mock data"],
      "definition_of_done": ["Endpoint returns 200", "Unit test passes"]
    }}
  ],
  "blocking_gaps": ["List of project-level issues that must be resolved"]
}}
"""


def validate_planning(
    prd: PRD,
    config: IgnitionConfig,
    compound_state: CompoundState | None = None,
    client: OpenAI | None = None,
) -> PlanningReport:
    """Evaluate planning quality for all tasks in the PRD.

    Returns a PlanningReport with per-task scores and overall quality.
    """
    if client is None:
        client = get_client(config)

    # Build feed-forward context from previous sprints
    ff_context = ""
    if compound_state and compound_state.feed_forward:
        ff = compound_state.feed_forward
        ff_lines = ["Previous sprint learnings to incorporate:"]
        if ff.get("planning_improvements"):
            ff_lines.append(
                "Planning improvements: "
                + "; ".join(ff["planning_improvements"]),
            )
        if ff.get("top_patterns"):
            ff_lines.append(
                "Successful patterns: "
                + "; ".join(p["title"] for p in ff["top_patterns"]),
            )
        if ff.get("anti_patterns"):
            ff_lines.append(
                "Anti-patterns to avoid: "
                + "; ".join(p["title"] for p in ff["anti_patterns"]),
            )
        ff_context = "\n".join(ff_lines)

    system_prompt = PLANNING_SYSTEM.format(
        feed_forward_context=ff_context or "No previous sprint data available.",
    )

    tasks_json = json.dumps(
        [
            {
                "id": t.id,
                "title": t.title,
                "category": t.category.value,
                "description": t.description,
                "dependencies": t.dependencies,
                "testable": t.testable,
                "bounded": t.bounded,
            }
            for t in prd.tasks
        ],
        indent=2,
    )

    user_msg = f"""Project: {prd.project_name}
Domain: {prd.domain}
Description: {prd.description}

Tasks to evaluate:
{tasks_json}

Evaluate planning quality for each task."""

    result = chat_json(
        client,
        model=config.model,
        system=system_prompt,
        user=user_msg,
        max_tokens=8192,
    )

    data = json.loads(result)
    report = _parse_planning_report(prd.project_name, data)
    report.compute_overall()
    return report


def enrich_tasks_from_planning(
    prd: PRD,
    report: PlanningReport,
) -> PRD:
    """Enrich task descriptions with planning quality feedback.

    For tasks that score below 70, append the suggestions and
    definition of done to their description so the executing agent
    has better guidance.
    """
    assessment_map = {a.task_id: a for a in report.task_assessments}

    for task in prd.tasks:
        assessment = assessment_map.get(task.id)
        if assessment and not assessment.passes:
            enrichment = []
            if assessment.suggestions:
                enrichment.append(
                    "\n\n## Planning Enrichment (auto-generated)\n"
                    + "\n".join(f"- {s}" for s in assessment.suggestions),
                )
            if assessment.definition_of_done:
                enrichment.append(
                    "\n## Definition of Done\n"
                    + "\n".join(
                        f"- [ ] {d}" for d in assessment.definition_of_done
                    ),
                )
            if assessment.gaps:
                enrichment.append(
                    "\n## Gaps to Address\n"
                    + "\n".join(f"- ⚠️ {g}" for g in assessment.gaps),
                )
            task.description += "".join(enrichment)

    return prd


def save_planning_report(report: PlanningReport, work_dir: Path) -> Path:
    """Save planning report to the work directory."""
    path = work_dir / "planning-report.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Internal parsing
# ---------------------------------------------------------------------------


def _parse_planning_report(
    project_name: str,
    data: dict,
) -> PlanningReport:
    """Parse LLM JSON response into a PlanningReport."""
    assessments = []
    for a in data.get("assessments", []):
        scores = []
        for s in a.get("scores", []):
            try:
                dim = PlanningDimension(s["dimension"])
            except (ValueError, KeyError):
                continue
            scores.append(
                PlanningScore(
                    dimension=dim,
                    score=min(1.0, max(0.0, float(s.get("score", 0)))),
                    reasoning=s.get("reasoning", ""),
                ),
            )
        assessments.append(
            TaskPlanQuality(
                task_id=a.get("task_id", 0),
                task_title=a.get("task_title", ""),
                scores=scores,
                gaps=a.get("gaps", []),
                suggestions=a.get("suggestions", []),
                definition_of_done=a.get("definition_of_done", []),
            ),
        )

    return PlanningReport(
        project_name=project_name,
        task_assessments=assessments,
        blocking_gaps=data.get("blocking_gaps", []),
    )
