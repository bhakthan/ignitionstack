"""Stage 8.5 — Reflection: post-sprint learning and self-improvement.

Compound Engineering Principle: Codify knowledge so it's reusable.
This stage runs after all iterations in a sprint to:
  1. Analyze what patterns led to success or failure
  2. Build and update the pattern library (successful approaches)
  3. Flag anti-patterns (approaches that caused issues)
  4. Generate feed-forward context for the next sprint
  5. Produce a sprint retrospective

This is the heart of recursive self-improvement — each sprint's
reflection makes the next sprint's planning better.
"""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from ignition.compound import (
    CompoundState,
    EngineeringPattern,
    PatternType,
    SprintRetrospective,
)
from ignition.config import IgnitionConfig
from ignition.llm import chat_json, get_client
from ignition.models import PRD

REFLECTION_SYSTEM = """\
You are a compound engineering reflection analyst. After a sprint of
coding iterations, your job is to extract learnings that make the
next sprint better.

Analyze the sprint data and produce:

1. **Successes**: What went well? Which patterns worked?
2. **Failures**: What went wrong? What caused issues?
3. **Surprises**: Unexpected findings or insights?
4. **New patterns**: Approaches worth codifying for reuse
5. **Anti-patterns**: Approaches to avoid in future
6. **Planning improvements**: How to plan better next sprint
7. **Process improvements**: How to improve the overall process
8. **Knowledge gaps**: What we still need to learn

For patterns, provide:
  - A unique kebab-case id (e.g., "split-ui-components")
  - Whether it's a "success" or "anti_pattern"
  - A title and description
  - Context: when this pattern applies

{previous_patterns}

Respond with JSON:
{{
  "successes": ["...", "..."],
  "failures": ["...", "..."],
  "surprises": ["...", "..."],
  "new_patterns": [
    {{
      "id": "pattern-id",
      "pattern_type": "success|anti_pattern",
      "title": "Short name",
      "description": "What this pattern is and why it matters",
      "context": "When to apply this pattern"
    }}
  ],
  "reinforced_pattern_ids": ["existing-pattern-id"],
  "planning_improvements": ["...", "..."],
  "process_improvements": ["...", "..."],
  "knowledge_gaps": ["...", "..."]
}}
"""


def reflect_on_sprint(
    prd: PRD,
    config: IgnitionConfig,
    compound_state: CompoundState,
    client: OpenAI | None = None,
) -> SprintRetrospective:
    """Analyze the completed sprint and produce a retrospective.

    This is the recursive self-improvement engine. The retrospective's
    feed-forward data gets injected into the next sprint's planning,
    closing the compound engineering loop.
    """
    if client is None:
        client = get_client(config)

    # Build context about existing patterns
    pattern_ctx = ""
    if compound_state.pattern_library.patterns:
        existing = compound_state.pattern_library.patterns[:20]
        pattern_ctx = (
            "Existing patterns in the library (reinforce if seen again):\n"
            + "\n".join(
                f"- {p.id}: {p.title} ({p.pattern_type.value}, "
                f"seen {p.times_observed}x)"
                for p in existing
            )
        )

    system_prompt = REFLECTION_SYSTEM.format(
        previous_patterns=pattern_ctx or "No existing patterns yet.",
    )

    # Gather sprint data
    sprint_data = _build_sprint_summary(prd, compound_state)

    result = chat_json(
        client,
        model=config.model,
        system=system_prompt,
        user=sprint_data,
        max_tokens=4096,
    )

    data = json.loads(result)
    return _parse_retrospective(prd, compound_state, data)


def save_retrospective(
    retro: SprintRetrospective,
    work_dir: Path,
) -> Path:
    """Save sprint retrospective to work directory."""
    retro_dir = work_dir / ".ignition" / "retrospectives"
    retro_dir.mkdir(parents=True, exist_ok=True)
    path = retro_dir / f"sprint-{retro.sprint_number}.json"
    path.write_text(retro.model_dump_json(indent=2), encoding="utf-8")
    return path


def generate_feed_forward_prompt(
    compound_state: CompoundState,
) -> str:
    """Generate a prompt section that summarizes learnings for the next sprint.

    This is what makes the system recursively self-improving:
    knowledge from sprint N becomes context for sprint N+1's planning.
    """
    if not compound_state.feed_forward:
        return ""

    ff = compound_state.feed_forward
    lines = [
        "## Compound Engineering — Feed-Forward Context",
        "",
        f"Previous sprint completion rate: {ff.get('completion_rate', 'N/A')}%",
        "",
    ]

    if ff.get("planning_improvements"):
        lines.append("### Planning Improvements to Apply")
        for imp in ff["planning_improvements"]:
            lines.append(f"- {imp}")
        lines.append("")

    if ff.get("process_improvements"):
        lines.append("### Process Improvements to Apply")
        for imp in ff["process_improvements"]:
            lines.append(f"- {imp}")
        lines.append("")

    if ff.get("top_patterns"):
        lines.append("### Proven Patterns to Reuse")
        for p in ff["top_patterns"]:
            lines.append(f"- **{p['title']}**: {p['description']}")
        lines.append("")

    if ff.get("anti_patterns"):
        lines.append("### Anti-Patterns to Avoid")
        for p in ff["anti_patterns"]:
            lines.append(f"- **{p['title']}**: {p['description']}")
        lines.append("")

    if ff.get("knowledge_gaps"):
        lines.append("### Knowledge Gaps to Research")
        for gap in ff["knowledge_gaps"]:
            lines.append(f"- {gap}")
        lines.append("")

    debt_count = ff.get("open_debt_count", 0)
    if debt_count > 0:
        lines.append(
            f"### Technical Debt: {debt_count} open items "
            f"(score: {ff.get('debt_score', 0)})",
        )
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_sprint_summary(
    prd: PRD,
    state: CompoundState,
) -> str:
    """Build a text summary of the sprint for the reflection LLM."""
    from ignition.models import TaskStatus

    done = [t for t in prd.tasks if t.status == TaskStatus.DONE]
    pending = [t for t in prd.tasks if t.status == TaskStatus.PENDING]
    blocked = [t for t in prd.tasks if t.status == TaskStatus.BLOCKED]

    lines = [
        f"# Sprint {state.current_sprint} Summary",
        f"Project: {prd.project_name}",
        f"Domain: {prd.domain}",
        "",
        f"## Tasks: {len(done)}/{len(prd.tasks)} completed",
        "",
    ]

    if done:
        lines.append("### Completed Tasks")
        for t in done:
            lines.append(f"- [{t.id}] {t.title} ({t.category.value})")
        lines.append("")

    if pending:
        lines.append(f"### Still Pending: {len(pending)} tasks")
        lines.append("")

    if blocked:
        lines.append(f"### Blocked: {len(blocked)} tasks")
        for t in blocked:
            lines.append(f"- [{t.id}] {t.title} — deps: {t.dependencies}")
        lines.append("")

    # Review findings summary
    sprint_reviews = [
        r for r in state.review_reports
        if r.iteration > state.total_iterations - len(done)
    ]
    if sprint_reviews:
        total_findings = sum(len(r.findings) for r in sprint_reviews)
        blockers = sum(len(r.blockers) for r in sprint_reviews)
        warnings = sum(len(r.warnings) for r in sprint_reviews)
        lines.append(f"## Review Findings: {total_findings} total")
        lines.append(f"  - Blockers: {blockers}")
        lines.append(f"  - Warnings: {warnings}")
        lines.append("")

    # Debt summary
    lines.append(f"## Technical Debt Score: {state.debt_ledger.debt_score}")
    lines.append(f"  - Open items: {len(state.debt_ledger.open_items)}")
    lines.append(f"  - Resolved items: {len(state.debt_ledger.resolved_items)}")
    lines.append("")

    # Planning quality
    if state.planning_reports:
        last_plan = state.planning_reports[-1]
        lines.append(f"## Planning Quality: {last_plan.overall_score}/100")
        lines.append("")

    return "\n".join(lines)


def _parse_retrospective(
    prd: PRD,
    state: CompoundState,
    data: dict,
) -> SprintRetrospective:
    """Parse LLM JSON response into a SprintRetrospective."""
    from ignition.models import TaskStatus

    new_patterns = []
    for p in data.get("new_patterns", []):
        try:
            ptype = PatternType(p.get("pattern_type", "success"))
        except ValueError:
            ptype = PatternType.SUCCESS
        new_patterns.append(
            EngineeringPattern(
                id=p.get("id", f"pattern-{len(new_patterns) + 1}"),
                pattern_type=ptype,
                title=p.get("title", ""),
                description=p.get("description", ""),
                context=p.get("context", ""),
                first_seen_iteration=state.total_iterations,
                last_seen_iteration=state.total_iterations,
            ),
        )

    done_count = sum(1 for t in prd.tasks if t.status == TaskStatus.DONE)

    return SprintRetrospective(
        sprint_number=state.current_sprint,
        iterations_completed=state.total_iterations,
        tasks_completed=done_count,
        tasks_total=len(prd.tasks),
        successes=data.get("successes", []),
        failures=data.get("failures", []),
        surprises=data.get("surprises", []),
        new_patterns=new_patterns,
        reinforced_patterns=data.get("reinforced_pattern_ids", []),
        planning_improvements=data.get("planning_improvements", []),
        process_improvements=data.get("process_improvements", []),
        knowledge_gaps=data.get("knowledge_gaps", []),
    )
