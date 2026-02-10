"""Stage 7.5 — Review: validation gate before committing iteration results."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from ignition.compound import (
    DebtCategory,
    DebtSeverity,
    DebtReport,
    ReviewCheckResult,
    ReviewCheckType,
    ReviewGateResult,
    TechnicalDebt,
)
from ignition.config import IgnitionConfig
from ignition.llm import chat_json, get_client
from ignition.models import Task

REVIEW_SYSTEM = """\
You are a code review expert focused on identifying technical debt and quality issues.

Analyze the provided code changes and identify:

1. CODE QUALITY issues:
   - Poor naming conventions
   - Functions that are too long (>50 lines)
   - High cyclomatic complexity
   - Inconsistent formatting

2. TECHNICAL DEBT items:
   - TODO/FIXME comments
   - Hardcoded values (magic numbers, hardcoded strings)
   - Code duplication
   - Missing error handling
   - Tight coupling between modules

3. TESTING gaps:
   - Untested code paths
   - Missing edge case handling
   - No integration tests for new features

4. DOCUMENTATION issues:
   - Missing docstrings
   - Outdated comments
   - No README updates for new features

5. SECURITY concerns:
   - Hardcoded credentials
   - SQL injection risks
   - Unvalidated inputs

For each issue, provide:
- category: code_smell|hardcoded|missing_test|todo_fixme|duplication|coupling|documentation|dependency
- severity: low|medium|high|critical
- file_path: where the issue is
- line_number: if applicable
- description: what the issue is
- suggested_fix: how to address it

Respond with JSON:
{
  "checks": {
    "code_quality": {"passed": true, "score": 85, "findings": ["..."]},
    "test_coverage": {"passed": false, "score": 60, "findings": ["Missing tests for error handler"]},
    "debt_scan": {"passed": true, "score": 75, "findings": ["2 TODO comments found"]},
    "documentation": {"passed": true, "score": 90, "findings": []}
  },
  "debt_items": [
    {
      "category": "todo_fixme",
      "severity": "medium",
      "file_path": "src/api.py",
      "line_number": 42,
      "description": "TODO comment: implement error retry",
      "suggested_fix": "Implement exponential backoff retry logic"
    }
  ],
  "overall_score": 77.5,
  "blocking_issues": [],
  "warnings": ["Consider adding integration tests"]
}
"""


def run_review_gate(
    iteration: int,
    task: Task,
    changed_files: list[str],
    file_contents: dict[str, str],
    config: IgnitionConfig,
    client: OpenAI | None = None,
) -> ReviewGateResult:
    """Run the review gate on changed files for an iteration."""
    if client is None:
        client = get_client(config)
    
    # Build file summary for LLM
    file_summary = []
    for file_path in changed_files:
        content = file_contents.get(file_path, "")
        # Truncate very large files
        if len(content) > 5000:
            content = content[:5000] + "\n... (truncated)"
        file_summary.append(f"=== {file_path} ===\n{content}")
    
    user_msg = f"""Review the following code changes for iteration {iteration}.

Task: {task.title} (ID: {task.id})
Category: {task.category.value}
Description: {task.description}

Changed files:
{chr(10).join(file_summary)}

Perform a thorough review focusing on technical debt and quality."""

    result = chat_json(
        client,
        model=config.model,
        system=REVIEW_SYSTEM,
        user=user_msg,
        max_tokens=4096,
    )
    data = json.loads(result)
    
    # Build check results
    checks: list[ReviewCheckResult] = []
    checks_data = data.get("checks", {})
    
    for check_type in ReviewCheckType:
        check_data = checks_data.get(check_type.value, {})
        checks.append(
            ReviewCheckResult(
                check_type=check_type,
                passed=check_data.get("passed", True),
                score=check_data.get("score", 100.0),
                findings=check_data.get("findings", []),
                blocking=check_data.get("severity") == "critical",
            )
        )
    
    gate_result = ReviewGateResult(
        iteration=iteration,
        task_id=task.id,
        task_title=task.title,
        timestamp=datetime.now(),
        checks=checks,
        blocking_issues=data.get("blocking_issues", []),
        warnings=data.get("warnings", []),
    )
    gate_result.compute_result()
    
    return gate_result


def extract_debt_items(
    review_result: ReviewGateResult,
    raw_data: dict,
    iteration: int,
) -> list[TechnicalDebt]:
    """Extract technical debt items from review data."""
    debt_items: list[TechnicalDebt] = []
    
    for item in raw_data.get("debt_items", []):
        debt_items.append(
            TechnicalDebt(
                id=f"debt-{iteration}-{len(debt_items)+1}",
                category=DebtCategory(item.get("category", "code_smell")),
                severity=DebtSeverity(item.get("severity", "low")),
                file_path=item.get("file_path", "unknown"),
                line_number=item.get("line_number"),
                description=item.get("description", ""),
                suggested_fix=item.get("suggested_fix", ""),
                iteration_found=iteration,
            )
        )
    
    return debt_items


def scan_for_debt_patterns(file_path: Path, content: str) -> list[TechnicalDebt]:
    """Scan file content for common debt patterns (static analysis)."""
    debt_items: list[TechnicalDebt] = []
    lines = content.split("\n")
    
    for i, line in enumerate(lines, 1):
        # TODO/FIXME comments
        if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
            debt_items.append(
                TechnicalDebt(
                    id=f"static-{file_path.name}-{i}",
                    category=DebtCategory.TODO_FIXME,
                    severity=DebtSeverity.LOW,
                    file_path=str(file_path),
                    line_number=i,
                    description=f"Found marker in comment: {line.strip()[:80]}",
                    suggested_fix="Address the TODO/FIXME or create a tracked issue",
                )
            )
        
        # Hardcoded numbers (magic numbers)
        if re.search(r"(?<![a-zA-Z_])(?<![\d.])[0-9]+(?![a-zA-Z_\d.])(?!.*(?:=|:))", line):
            # Skip common acceptable numbers
            if not re.search(r"\b(0|1|2|100|200|404|500)\b", line):
                debt_items.append(
                    TechnicalDebt(
                        id=f"static-magic-{file_path.name}-{i}",
                        category=DebtCategory.HARDCODED,
                        severity=DebtSeverity.LOW,
                        file_path=str(file_path),
                        line_number=i,
                        description="Possible magic number detected",
                        suggested_fix="Consider extracting to a named constant",
                    )
                )
    
    return debt_items


def compute_debt_score(debt_items: list[TechnicalDebt]) -> float:
    """Compute weighted technical debt score."""
    severity_weights = {
        DebtSeverity.LOW: 1,
        DebtSeverity.MEDIUM: 3,
        DebtSeverity.HIGH: 7,
        DebtSeverity.CRITICAL: 15,
    }
    
    total = sum(
        severity_weights.get(item.severity, 1)
        for item in debt_items
        if not item.resolved
    )
    
    return float(total)


def generate_debt_report(
    debt_items: list[TechnicalDebt],
    previous_report: DebtReport | None = None,
) -> DebtReport:
    """Generate a debt report from debt items."""
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    
    for item in debt_items:
        by_severity[item.severity.value] = by_severity.get(item.severity.value, 0) + 1
        by_category[item.category.value] = by_category.get(item.category.value, 0) + 1
    
    current_score = compute_debt_score(debt_items)
    
    # Determine trend
    trend = "stable"
    if previous_report:
        diff = current_score - previous_report.debt_score
        if diff > 2:
            trend = "degrading"
        elif diff < -2:
            trend = "improving"
    
    return DebtReport(
        total_items=len(debt_items),
        by_severity=by_severity,
        by_category=by_category,
        debt_score=current_score,
        items=debt_items,
        trend=trend,
    )


def save_review_result(result: ReviewGateResult, work_dir: Path) -> Path:
    """Save a review gate result to the compound directory."""
    compound_dir = work_dir / ".compound" / "reviews"
    compound_dir.mkdir(parents=True, exist_ok=True)
    
    result_path = compound_dir / f"review_iter_{result.iteration}.json"
    result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return result_path


def load_review_results(work_dir: Path) -> list[ReviewGateResult]:
    """Load all review results from the compound directory."""
    reviews_dir = work_dir / ".compound" / "reviews"
    if not reviews_dir.exists():
        return []
    
    results: list[ReviewGateResult] = []
    for path in sorted(reviews_dir.glob("review_iter_*.json")):
        results.append(
            ReviewGateResult.model_validate_json(path.read_text(encoding="utf-8"))
        )
    return results


def save_debt_report(report: DebtReport, work_dir: Path) -> Path:
    """Save the debt report to the compound directory."""
    compound_dir = work_dir / ".compound"
    compound_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = compound_dir / "debt_report.json"
    report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return report_path


def load_debt_report(work_dir: Path) -> DebtReport | None:
    """Load a previously saved debt report."""
    report_path = work_dir / ".compound" / "debt_report.json"
    if report_path.exists():
        return DebtReport.model_validate_json(report_path.read_text(encoding="utf-8"))
    return None


def should_block_commit(
    gate_result: ReviewGateResult,
    config: IgnitionConfig,
) -> tuple[bool, list[str]]:
    """Determine if the review gate should block the commit."""
    reasons: list[str] = []
    
    # Always block on critical issues
    if gate_result.blocking_issues:
        reasons.extend(gate_result.blocking_issues)
        return True, reasons
    
    # Block if below threshold
    if gate_result.overall_score < config.review_threshold:
        reasons.append(
            f"Review score {gate_result.overall_score:.1f} "
            f"below threshold {config.review_threshold}"
        )
        return True, reasons
    
    return False, reasons
