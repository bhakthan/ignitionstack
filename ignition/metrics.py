"""Compound Engineering Metrics — track trends and generate reports.

Provides actionable metrics across sprints:
  - Planning quality trend (should increase)
  - Technical debt trend (should decrease or stabilize)
  - Review gate pass rate (should increase)
  - Pattern library growth (should grow)
  - Sprint velocity (tasks completed per sprint)
  - Self-improvement score (composite health metric)
"""

from __future__ import annotations

from pathlib import Path

from ignition.compound import CompoundState


def compute_metrics(state: CompoundState) -> dict:
    """Compute all compound engineering metrics from state."""
    return {
        "project": state.project_name,
        "current_sprint": state.current_sprint,
        "total_iterations": state.total_iterations,
        "planning": _planning_metrics(state),
        "debt": _debt_metrics(state),
        "review": _review_metrics(state),
        "patterns": _pattern_metrics(state),
        "velocity": _velocity_metrics(state),
        "self_improvement": _self_improvement_score(state),
    }


def generate_metrics_report(state: CompoundState) -> str:
    """Generate a human-readable metrics report."""
    m = compute_metrics(state)
    lines = [
        f"# Compound Engineering Metrics — {m['project']}",
        f"Sprint {m['current_sprint']} | {m['total_iterations']} total iterations",
        "",
        "## Planning Quality",
        f"  Current score: {m['planning']['current_score']}/100",
        f"  Trend: {m['planning']['trend']}",
        f"  Tasks below threshold: {m['planning']['below_threshold']}",
        "",
        "## Technical Debt",
        f"  Current score: {m['debt']['current_score']}",
        f"  Trend: {m['debt']['trend']}",
        f"  Open items: {m['debt']['open_items']}",
        f"  Resolved items: {m['debt']['resolved_items']}",
        f"  Resolution rate: {m['debt']['resolution_rate']}%",
        "",
        "## Review Gates",
        f"  Total reviews: {m['review']['total_reviews']}",
        f"  Pass rate: {m['review']['pass_rate']}%",
        f"  Blocker count: {m['review']['blocker_count']}",
        "",
        "## Pattern Library",
        f"  Total patterns: {m['patterns']['total']}",
        f"  Success patterns: {m['patterns']['success_count']}",
        f"  Anti-patterns: {m['patterns']['anti_pattern_count']}",
        f"  Most reinforced: {m['patterns']['most_reinforced']}",
        "",
        "## Velocity",
        f"  Tasks per sprint: {m['velocity']['tasks_per_sprint']}",
        f"  Completion rate: {m['velocity']['completion_rate']}%",
        "",
        "## Self-Improvement Score",
        f"  Score: {m['self_improvement']['score']}/100",
        f"  Is improving: {'Yes' if m['self_improvement']['is_improving'] else 'No'}",
        f"  Signals: {', '.join(m['self_improvement']['signals'])}",
        "",
    ]
    return "\n".join(lines)


def save_metrics_report(state: CompoundState, work_dir: Path) -> Path:
    """Save metrics report to the work directory."""
    report = generate_metrics_report(state)
    path = work_dir / "compound-metrics.md"
    path.write_text(report, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Internal metric computations
# ---------------------------------------------------------------------------


def _planning_metrics(state: CompoundState) -> dict:
    trend_data = state.planning_score_trend
    current = trend_data[-1] if trend_data else 0.0
    trend = _trend_label(trend_data)

    below = 0
    if state.planning_reports:
        last = state.planning_reports[-1]
        below = sum(
            1 for a in last.task_assessments if not a.passes
        )

    return {
        "current_score": current,
        "trend": trend,
        "trend_data": trend_data,
        "below_threshold": below,
    }


def _debt_metrics(state: CompoundState) -> dict:
    ledger = state.debt_ledger
    open_count = len(ledger.open_items)
    resolved_count = len(ledger.resolved_items)
    total = len(ledger.items)
    resolution_rate = (
        round(resolved_count / total * 100, 1) if total > 0 else 100.0
    )

    return {
        "current_score": ledger.debt_score,
        "trend": _trend_label(state.debt_score_trend, lower_is_better=True),
        "trend_data": state.debt_score_trend,
        "open_items": open_count,
        "resolved_items": resolved_count,
        "resolution_rate": resolution_rate,
    }


def _review_metrics(state: CompoundState) -> dict:
    reviews = state.review_reports
    total = len(reviews)
    passed = sum(1 for r in reviews if r.passed)
    blockers = sum(len(r.blockers) for r in reviews)

    return {
        "total_reviews": total,
        "pass_rate": round(passed / total * 100, 1) if total > 0 else 100.0,
        "blocker_count": blockers,
    }


def _pattern_metrics(state: CompoundState) -> dict:
    lib = state.pattern_library
    most_reinforced = ""
    if lib.top_patterns:
        top = lib.top_patterns[0]
        most_reinforced = f"{top.title} ({top.times_observed}x)"

    return {
        "total": len(lib.patterns),
        "success_count": len(lib.success_patterns),
        "anti_pattern_count": len(lib.anti_patterns),
        "most_reinforced": most_reinforced or "none yet",
    }


def _velocity_metrics(state: CompoundState) -> dict:
    retros = state.retrospectives
    if not retros:
        return {"tasks_per_sprint": 0, "completion_rate": 0.0}

    last = retros[-1]
    avg = round(
        sum(r.tasks_completed for r in retros) / len(retros), 1,
    )
    return {
        "tasks_per_sprint": avg,
        "completion_rate": last.completion_rate,
    }


def _self_improvement_score(state: CompoundState) -> dict:
    """Composite score (0–100) measuring whether the system is improving."""
    signals = []
    score = 50.0  # baseline

    # Planning trend
    if len(state.planning_score_trend) >= 2:
        if state.planning_score_trend[-1] > state.planning_score_trend[-2]:
            score += 15
            signals.append("planning-improving")
        elif state.planning_score_trend[-1] < state.planning_score_trend[-2]:
            score -= 15
            signals.append("planning-declining")

    # Debt trend
    if len(state.debt_score_trend) >= 2:
        if state.debt_score_trend[-1] < state.debt_score_trend[-2]:
            score += 15
            signals.append("debt-decreasing")
        elif state.debt_score_trend[-1] > state.debt_score_trend[-2]:
            score -= 15
            signals.append("debt-increasing")

    # Review pass rate
    reviews = state.review_reports
    if reviews:
        pass_rate = sum(1 for r in reviews if r.passed) / len(reviews)
        if pass_rate >= 0.8:
            score += 10
            signals.append("high-review-pass-rate")
        elif pass_rate < 0.5:
            score -= 10
            signals.append("low-review-pass-rate")

    # Pattern library growing
    if len(state.pattern_library.patterns) >= 5:
        score += 10
        signals.append("pattern-library-growing")

    score = max(0.0, min(100.0, score))

    return {
        "score": round(score, 1),
        "is_improving": state.is_improving,
        "signals": signals or ["baseline"],
    }


def _trend_label(
    data: list[float],
    *,
    lower_is_better: bool = False,
) -> str:
    """Label a trend as improving, declining, or stable."""
    if len(data) < 2:
        return "insufficient-data"
    diff = data[-1] - data[-2]
    threshold = 2.0  # ignore small fluctuations
    if abs(diff) < threshold:
        return "stable"
    if lower_is_better:
        return "improving" if diff < 0 else "declining"
    return "improving" if diff > 0 else "declining"
