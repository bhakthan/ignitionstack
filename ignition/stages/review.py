"""Stage 7.5 — Review Gate: catch issues before they compound.

Compound Engineering Principle: Review captures issues AND learnings.
This stage runs after each Ralph iteration to evaluate:
  - Technical debt introduced (hardcoded values, missing tests, TODOs)
  - Coupling / dependency issues
  - Code quality signals
  - Alignment with the plan (did the iteration achieve what was planned?)

The review gate can block a commit if blockers are found, or allow it
through with warnings that get tracked in the debt ledger.
"""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from ignition.compound import (
    CompoundState,
    DebtItem,
    ReviewFinding,
    ReviewReport,
    ReviewSeverity,
)
from ignition.config import IgnitionConfig
from ignition.llm import chat_json, get_client
from ignition.models import Task

REVIEW_SYSTEM = """\
You are a compound engineering review gate. Your job is to review
the output of a coding iteration and identify issues before they compound.

Evaluate the implementation against these categories:
  1. technical-debt — hardcoded values, TODOs, missing error handling
  2. test-coverage — missing unit tests, untested edge cases
  3. coupling — tight coupling between components, circular dependencies
  4. alignment — does the implementation match the plan?
  5. quality — code smells, naming, documentation gaps

For each finding, assign severity:
  - blocker: must fix before proceeding (breaks other tasks)
  - warning: should fix soon (accumulates debt)
  - info: nice to have (improves quality)

Also provide:
  - technical_debt_score: 0-100 (0=pristine, 100=critical debt)
  - passed: true if no blockers and debt_score < 50

{pattern_context}

Respond with JSON:
{{
  "findings": [
    {{
      "category": "technical-debt|test-coverage|coupling|alignment|quality",
      "severity": "blocker|warning|info",
      "description": "What the issue is",
      "location": "file or component reference",
      "suggestion": "How to fix it"
    }}
  ],
  "technical_debt_score": 25,
  "passed": true,
  "debt_items": [
    {{
      "id": "debt-001",
      "category": "hardcoded-value",
      "description": "Database URL hardcoded in config",
      "severity": "warning"
    }}
  ]
}}
"""


def review_iteration(
    task: Task,
    iteration: int,
    work_dir: Path,
    config: IgnitionConfig,
    compound_state: CompoundState | None = None,
    client: OpenAI | None = None,
) -> ReviewReport:
    """Review the output of a single Ralph iteration.

    Reads the current state of the work directory and evaluates
    the implementation against the task plan.
    """
    if client is None:
        client = get_client(config)

    pattern_context = ""
    if compound_state:
        anti = compound_state.pattern_library.anti_patterns[:5]
        if anti:
            pattern_context = (
                "Known anti-patterns to watch for:\n"
                + "\n".join(f"- {p.title}: {p.description}" for p in anti)
            )

    system_prompt = REVIEW_SYSTEM.format(
        pattern_context=pattern_context or "No anti-patterns recorded yet.",
    )

    # Gather context about what was implemented
    context_parts = [
        f"Task #{task.id}: {task.title}",
        f"Description: {task.description}",
        f"Iteration: {iteration}",
    ]

    # Read progress file for recent changes
    progress_file = work_dir / "progress.txt"
    if progress_file.exists():
        progress = progress_file.read_text(encoding="utf-8")
        # Take last 2000 chars to stay in context window
        context_parts.append(f"Recent progress:\n{progress[-2000:]}")

    user_msg = "\n\n".join(context_parts)

    result = chat_json(
        client,
        model=config.model,
        system=system_prompt,
        user=user_msg,
        max_tokens=4096,
    )

    data = json.loads(result)
    return _parse_review_report(task, iteration, data)


def apply_review_to_state(
    report: ReviewReport,
    state: CompoundState,
) -> None:
    """Apply review findings to the compound state.

    - Track new debt items in the ledger
    - Update debt score trends
    - Record the review report
    """
    state.review_reports.append(report)

    # Add new debt items
    for finding in report.findings:
        if finding.severity in (ReviewSeverity.BLOCKER, ReviewSeverity.WARNING):
            debt_id = f"debt-{state.current_sprint}-{report.iteration}-{len(state.debt_ledger.items) + 1}"
            state.debt_ledger.add(
                DebtItem(
                    id=debt_id,
                    category=finding.category,
                    description=finding.description,
                    severity=finding.severity,
                    introduced_iteration=report.iteration,
                    task_id=report.task_id,
                ),
            )


def save_review_report(report: ReviewReport, work_dir: Path) -> Path:
    """Save review report to the work directory."""
    reports_dir = work_dir / ".ignition" / "reviews"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"review-iter-{report.iteration}.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Internal parsing
# ---------------------------------------------------------------------------


def _parse_review_report(
    task: Task,
    iteration: int,
    data: dict,
) -> ReviewReport:
    """Parse LLM JSON response into a ReviewReport."""
    findings = []
    for f in data.get("findings", []):
        try:
            severity = ReviewSeverity(f.get("severity", "info"))
        except ValueError:
            severity = ReviewSeverity.INFO
        findings.append(
            ReviewFinding(
                category=f.get("category", "quality"),
                severity=severity,
                description=f.get("description", ""),
                location=f.get("location", ""),
                suggestion=f.get("suggestion", ""),
            ),
        )

    report = ReviewReport(
        iteration=iteration,
        task_id=task.id,
        task_title=task.title,
        findings=findings,
        technical_debt_score=float(data.get("technical_debt_score", 0)),
    )
    report.evaluate()

    # Override with LLM's assessment if provided
    if "passed" in data:
        report.passed = bool(data["passed"]) and len(report.blockers) == 0

    return report
