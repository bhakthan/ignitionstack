"""Compound Engineering Metrics — tracking and reporting."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ignition.compound import (
    CompoundMetrics,
    CompoundSession,
    DebtReport,
    MetricsHistory,
    PlanningQualityReport,
    ReviewGateResult,
)
from ignition.config import IgnitionConfig


def compute_metrics(
    session: CompoundSession,
    iteration: int,
    planning_report: PlanningQualityReport | None = None,
    review_results: list[ReviewGateResult] | None = None,
    debt_report: DebtReport | None = None,
) -> CompoundMetrics:
    """Compute compound engineering metrics for an iteration."""
    metrics = CompoundMetrics(
        project_name=session.project_name,
        timestamp=datetime.now(),
        iteration=iteration,
    )
    
    # Planning metrics
    if planning_report:
        metrics.planning_quality_score = planning_report.average_score
        metrics.tasks_passing_planning_threshold = planning_report.passing_tasks
    
    # Review metrics
    if review_results:
        passed = sum(1 for r in review_results if r.overall_passed)
        metrics.review_gate_pass_rate = (
            passed / len(review_results) * 100 if review_results else 0.0
        )
        metrics.average_review_score = (
            sum(r.overall_score for r in review_results) / len(review_results)
            if review_results else 0.0
        )
    
    # Debt metrics
    if debt_report:
        metrics.technical_debt_score = debt_report.debt_score
        metrics.debt_items_total = debt_report.total_items
        metrics.debt_items_resolved = sum(
            1 for item in debt_report.items if item.resolved
        )
        metrics.debt_trend = debt_report.trend
    
    # Self-improvement metrics
    metrics.patterns_learned = len(session.pattern_library)
    metrics.success_patterns = sum(
        1 for p in session.pattern_library if p.pattern_type.value == "success"
    )
    metrics.anti_patterns = sum(
        1 for p in session.pattern_library if p.pattern_type.value == "anti"
    )
    
    # Compute overall compound score
    metrics.compute_compound_score()
    
    return metrics


def update_metrics_history(
    session: CompoundSession,
    metrics: CompoundMetrics,
) -> None:
    """Add metrics snapshot to session history."""
    session.metrics_history.snapshots.append(metrics)
    session.last_updated = datetime.now()


def get_metrics_trend(
    history: MetricsHistory,
    metric_name: str,
    window: int = 5,
) -> dict:
    """Get trend analysis for a specific metric."""
    if len(history.snapshots) < 2:
        return {
            "trend": "insufficient_data",
            "current": None,
            "previous": None,
            "change": None,
        }
    
    recent = history.snapshots[-window:]
    values = [getattr(s, metric_name, 0) for s in recent]
    
    current = values[-1]
    previous = values[0]
    change = current - previous
    
    return {
        "trend": history.trend(metric_name, window),
        "current": current,
        "previous": previous,
        "change": change,
        "values": values,
    }


def generate_metrics_summary(metrics: CompoundMetrics) -> str:
    """Generate a human-readable metrics summary."""
    lines = [
        f"## Compound Engineering Metrics — Iteration {metrics.iteration}",
        f"Timestamp: {metrics.timestamp.isoformat()}",
        "",
        "### Overall Score",
        f"**Compound Score: {metrics.compound_score:.1f}/100**",
        "",
        "### Planning Quality",
        f"- Average Score: {metrics.planning_quality_score:.1f}/100",
        f"- Tasks Passing: {metrics.tasks_passing_planning_threshold}",
        "",
        "### Review Gates",
        f"- Pass Rate: {metrics.review_gate_pass_rate:.1f}%",
        f"- Average Score: {metrics.average_review_score:.1f}/100",
        "",
        "### Technical Debt",
        f"- Debt Score: {metrics.technical_debt_score:.1f} (target: <10)",
        f"- Total Items: {metrics.debt_items_total}",
        f"- Resolved: {metrics.debt_items_resolved}",
        f"- Trend: {metrics.debt_trend}",
        "",
        "### Self-Improvement",
        f"- Patterns Learned: {metrics.patterns_learned}",
        f"- Success Patterns: {metrics.success_patterns}",
        f"- Anti-Patterns: {metrics.anti_patterns}",
    ]
    
    return "\n".join(lines)


def generate_dashboard_html(
    session: CompoundSession,
    config: IgnitionConfig,
) -> str:
    """Generate an HTML dashboard for compound engineering metrics."""
    latest = session.metrics_history.latest
    if not latest:
        return "<html><body><h1>No metrics data yet</h1></body></html>"
    
    # Get trends
    trends = {
        "compound_score": get_metrics_trend(session.metrics_history, "compound_score"),
        "planning_quality_score": get_metrics_trend(session.metrics_history, "planning_quality_score"),
        "technical_debt_score": get_metrics_trend(session.metrics_history, "technical_debt_score"),
    }
    
    # Build pattern summary
    success_patterns = [p for p in session.pattern_library if p.pattern_type.value == "success"]
    anti_patterns = [p for p in session.pattern_library if p.pattern_type.value == "anti"]
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Compound Engineering Dashboard - {session.project_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; text-align: center; padding: 20px; margin: 10px; background: #f8f9fa; border-radius: 8px; }}
        .metric-value {{ font-size: 36px; font-weight: bold; color: #3498db; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .trend-up {{ color: #27ae60; }}
        .trend-down {{ color: #e74c3c; }}
        .trend-stable {{ color: #f39c12; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; }}
        .pattern-success {{ border-left: 4px solid #27ae60; }}
        .pattern-anti {{ border-left: 4px solid #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Compound Engineering Dashboard</h1>
        <p>Project: <strong>{session.project_name}</strong> | Last Updated: {session.last_updated.strftime("%Y-%m-%d %H:%M")}</p>
        
        <div class="card">
            <h2>Overall Health</h2>
            <div class="metric">
                <div class="metric-value">{latest.compound_score:.0f}</div>
                <div class="metric-label">Compound Score</div>
            </div>
            <div class="metric">
                <div class="metric-value">{latest.planning_quality_score:.0f}</div>
                <div class="metric-label">Planning Quality</div>
            </div>
            <div class="metric">
                <div class="metric-value">{latest.review_gate_pass_rate:.0f}%</div>
                <div class="metric-label">Review Pass Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value {_debt_class(latest.technical_debt_score)}">{latest.technical_debt_score:.1f}</div>
                <div class="metric-label">Debt Score</div>
            </div>
        </div>
        
        <div class="card">
            <h2>Technical Debt</h2>
            <p>Total Items: {latest.debt_items_total} | Resolved: {latest.debt_items_resolved} | Trend: <span class="trend-{latest.debt_trend}">{latest.debt_trend.upper()}</span></p>
        </div>
        
        <div class="card">
            <h2>Learned Patterns</h2>
            <h3>✅ Success Patterns ({len(success_patterns)})</h3>
            <table>
                <tr><th>Pattern</th><th>Category</th><th>Confidence</th><th>Observed</th></tr>
                {"".join(f"<tr class='pattern-success'><td>{p.description}</td><td>{p.category}</td><td>{p.confidence:.0%}</td><td>{p.times_observed}x</td></tr>" for p in success_patterns[:5])}
            </table>
            
            <h3>⚠️ Anti-Patterns ({len(anti_patterns)})</h3>
            <table>
                <tr><th>Pattern</th><th>Category</th><th>Observed</th></tr>
                {"".join(f"<tr class='pattern-anti'><td>{p.description}</td><td>{p.category}</td><td>{p.times_observed}x</td></tr>" for p in anti_patterns[:5])}
            </table>
        </div>
        
        <div class="card">
            <h2>Iteration History</h2>
            <table>
                <tr><th>Iteration</th><th>Compound Score</th><th>Planning</th><th>Review</th><th>Debt</th></tr>
                {"".join(f"<tr><td>{m.iteration}</td><td>{m.compound_score:.0f}</td><td>{m.planning_quality_score:.0f}</td><td>{m.average_review_score:.0f}</td><td>{m.technical_debt_score:.1f}</td></tr>" for m in session.metrics_history.snapshots[-10:])}
            </table>
        </div>
    </div>
</body>
</html>"""
    
    return html


def _debt_class(score: float) -> str:
    """Get CSS class for debt score."""
    if score < 5:
        return "trend-up"
    elif score < 15:
        return "trend-stable"
    return "trend-down"


def save_metrics(metrics: CompoundMetrics, work_dir: Path) -> Path:
    """Save metrics snapshot."""
    compound_dir = work_dir / ".compound" / "metrics"
    compound_dir.mkdir(parents=True, exist_ok=True)
    
    path = compound_dir / f"metrics_iter_{metrics.iteration}.json"
    path.write_text(metrics.model_dump_json(indent=2), encoding="utf-8")
    return path


def save_dashboard(session: CompoundSession, config: IgnitionConfig, work_dir: Path) -> Path:
    """Save the HTML dashboard."""
    compound_dir = work_dir / ".compound"
    compound_dir.mkdir(parents=True, exist_ok=True)
    
    html = generate_dashboard_html(session, config)
    path = compound_dir / "dashboard.html"
    path.write_text(html, encoding="utf-8")
    return path


def load_metrics_history(work_dir: Path) -> list[CompoundMetrics]:
    """Load all metrics snapshots."""
    metrics_dir = work_dir / ".compound" / "metrics"
    if not metrics_dir.exists():
        return []
    
    metrics: list[CompoundMetrics] = []
    for path in sorted(metrics_dir.glob("metrics_iter_*.json")):
        metrics.append(
            CompoundMetrics.model_validate_json(path.read_text(encoding="utf-8"))
        )
    return metrics


def append_to_progress(work_dir: Path, metrics: CompoundMetrics) -> None:
    """Append metrics summary to progress.txt."""
    progress_file = work_dir / "progress.txt"
    
    summary = f"""
## Compound Engineering Metrics — Iteration {metrics.iteration}
- Compound Score: {metrics.compound_score:.1f}/100
- Planning Quality: {metrics.planning_quality_score:.1f}/100
- Review Pass Rate: {metrics.review_gate_pass_rate:.1f}%
- Debt Score: {metrics.technical_debt_score:.1f} ({metrics.debt_trend})
- Patterns Learned: {metrics.patterns_learned} (success: {metrics.success_patterns}, anti: {metrics.anti_patterns})
"""
    
    with open(progress_file, "a", encoding="utf-8") as f:
        f.write(summary)
