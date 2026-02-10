"""Scaffold: Ralph loop scripts (bash + PowerShell)."""

from __future__ import annotations

from ignition.config import IgnitionConfig
from ignition.models import PRD


def scaffold_ralph(prd: PRD, config: IgnitionConfig) -> list[str]:
    """Generate ralph.sh and ralph.ps1."""
    work = config.ensure_work_dir()
    files: list[str] = []

    # ralph.sh
    sh = work / "ralph.sh"
    sh.write_text(_ralph_bash(prd, config), encoding="utf-8")
    files.append("ralph.sh")

    # ralph.ps1
    ps = work / "ralph.ps1"
    ps.write_text(_ralph_powershell(prd, config), encoding="utf-8")
    files.append("ralph.ps1")

    return files


def _ralph_bash(prd: PRD, config: IgnitionConfig) -> str:
    compound_section = ""
    if config.compound_mode:
        compound_section = """
    # ── Compound Engineering: Pre-iteration Planning ──
    echo "  📋 Planning: validating task quality..."
    FEED_FORWARD=""
    if [ -f ".ignition/feed-forward.md" ]; then
        FEED_FORWARD=$(cat .ignition/feed-forward.md)
    fi

    PLAN_PROMPT="Review the task plan before implementing. Check for:
    - Clear acceptance criteria
    - Testable outcomes
    - Bounded scope (< 30 min)
    - No hidden dependencies
    If the plan is weak, enrich it before coding.
    Feed-forward context from previous sprints:
    ${FEED_FORWARD:0:2000}"

    gh copilot suggest "$PLAN_PROMPT" 2>/dev/null || true
"""

    compound_review = ""
    if config.compound_mode:
        compound_review = """
    # ── Compound Engineering: Post-iteration Review ──
    echo "  🔍 Review: checking for technical debt..."
    REVIEW_PROMPT="Review the changes just made. Look for:
    - Hardcoded values or TODOs
    - Missing error handling or tests
    - Tight coupling between components
    - Alignment with the original task plan
    Record any findings in .ignition/reviews/review-iter-${i}.md"

    gh copilot suggest "$REVIEW_PROMPT" 2>/dev/null || true
"""

    compound_reflection = ""
    if config.compound_mode:
        compound_reflection = f"""
# ── Compound Engineering: Sprint Reflection ──
echo ""
echo "📊 Compound Engineering — Sprint Reflection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

REFLECT_PROMPT="Analyze the sprint that just completed:
1. What patterns led to success?
2. What caused failures or slowdowns?
3. What knowledge should be codified for next sprint?
4. How should planning improve?

Read .ignition/compound-state.json for historical context.
Write findings to .ignition/retrospectives/sprint-reflection.md
Update .ignition/feed-forward.md with context for next sprint."

gh copilot suggest "$REFLECT_PROMPT" 2>/dev/null || true

echo "  ✅ Reflection complete — learnings saved for next sprint"
echo "  📈 Run 'cat compound-metrics.md' to see trends"
"""

    return f"""\
#!/usr/bin/env bash
# ralph.sh — The IgnitionStack Ralph Loop
# Project: {prd.project_name}
# Iterations: {config.iterations}
# Compound Engineering: {'ENABLED' if config.compound_mode else 'DISABLED'}
#
# Each iteration: {'plan → implement → review → learn' if config.compound_mode else 'read PRD → pick next task → implement → test → commit'}
# Context window stays clean — no accumulated confusion.

set -euo pipefail

PRD_FILE="PRD.json"
PROGRESS_FILE="progress.txt"
ITERATIONS={config.iterations}
MODEL="${{IGNITION_MODEL:-{config.model}}}"

echo "🔄 Ralph Loop — {prd.project_name}"
echo "   Model: $MODEL"
echo "   Iterations: $ITERATIONS"
echo "   Compound Engineering: {'ENABLED' if config.compound_mode else 'DISABLED'}"
echo ""

for i in $(seq 1 $ITERATIONS); do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Iteration $i / $ITERATIONS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
{compound_section}
    # 1. Read PRD + progress
    CONTEXT=$(cat "$PRD_FILE" "$PROGRESS_FILE" 2>/dev/null || echo "{{}}")

    # 2. Ask the model to pick the next task and implement it
    gh copilot suggest \\
        "Read the PRD and progress file. Pick the next pending task whose dependencies are done. \\
         Implement it completely: write code, add tests, handle errors. \\
         Then mark it done in PRD.json and append a log entry to progress.txt. \\
         Context: ${{CONTEXT:0:4000}}" \\
        2>/dev/null || echo "  ⚠️  gh copilot not available — using fallback"
{compound_review}
    # 3. Stage and commit
    if git diff --quiet && git diff --cached --quiet; then
        echo "  ℹ️  No changes in iteration $i — skipping commit"
    else
        git add -A
        git commit -m "ralph: iteration $i — $(date +%H:%M:%S)" || true
    fi

    echo "  ✅ Iteration $i complete"
    echo ""
done

echo "🏁 Ralph Loop complete — $ITERATIONS iterations"
{compound_reflection}
echo "   Run 'ignition verify .' to check the output."
"""


def _ralph_powershell(prd: PRD, config: IgnitionConfig) -> str:
    compound_plan = ""
    if config.compound_mode:
        compound_plan = """
    # -- Compound Engineering: Pre-iteration Planning --
    Write-Host "  Planning: validating task quality..." -ForegroundColor Magenta
    $FeedForward = ""
    if (Test-Path ".ignition/feed-forward.md") {{
        $FeedForward = Get-Content ".ignition/feed-forward.md" -Raw
    }}
    try {{
        gh copilot suggest `
            "Review the task plan before implementing. Check for clear acceptance criteria, `
             testable outcomes, bounded scope, and no hidden dependencies. `
             Feed-forward: $($FeedForward.Substring(0, [Math]::Min(2000, $FeedForward.Length)))"
    }} catch {{ }}
"""

    compound_review = ""
    if config.compound_mode:
        compound_review = """
    # -- Compound Engineering: Post-iteration Review --
    Write-Host "  Review: checking for technical debt..." -ForegroundColor Magenta
    try {{
        gh copilot suggest `
            "Review changes just made. Check for hardcoded values, missing tests, `
             tight coupling, and alignment with the plan. `
             Record findings in .ignition/reviews/review-iter-$i.md"
    }} catch {{ }}
"""

    compound_reflection = ""
    if config.compound_mode:
        compound_reflection = f"""
# -- Compound Engineering: Sprint Reflection --
Write-Host ""
Write-Host "Compound Engineering - Sprint Reflection" -ForegroundColor Magenta
Write-Host ("=" * 40) -ForegroundColor DarkGray
try {{
    gh copilot suggest `
        "Analyze the sprint. What patterns led to success? What caused failures? `
         What knowledge should be codified? How should planning improve? `
         Read .ignition/compound-state.json for context. `
         Write to .ignition/retrospectives/ and update .ignition/feed-forward.md"
}} catch {{ }}
Write-Host "  Reflection complete - learnings saved for next sprint" -ForegroundColor Green
Write-Host "  Run 'Get-Content compound-metrics.md' to see trends" -ForegroundColor Cyan
"""

    return f"""\
# ralph.ps1 — The IgnitionStack Ralph Loop (PowerShell)
# Project: {prd.project_name}
# Iterations: {config.iterations}
# Compound Engineering: {'ENABLED' if config.compound_mode else 'DISABLED'}

$ErrorActionPreference = "Stop"

$PrdFile = "PRD.json"
$ProgressFile = "progress.txt"
$Iterations = {config.iterations}
$Model = if ($env:IGNITION_MODEL) {{ $env:IGNITION_MODEL }} else {{ "{config.model}" }}

Write-Host "Ralph Loop — {prd.project_name}" -ForegroundColor Cyan
Write-Host "   Model: $Model"
Write-Host "   Iterations: $Iterations"
Write-Host "   Compound Engineering: {'ENABLED' if config.compound_mode else 'DISABLED'}"
Write-Host ""

for ($i = 1; $i -le $Iterations; $i++) {{
    Write-Host ("=" * 40) -ForegroundColor DarkGray
    Write-Host "  Iteration $i / $Iterations" -ForegroundColor Yellow
    Write-Host ("=" * 40) -ForegroundColor DarkGray
{compound_plan}
    # 1. Read PRD + progress
    $Context = ""
    if (Test-Path $PrdFile) {{ $Context += Get-Content $PrdFile -Raw }}
    if (Test-Path $ProgressFile) {{ $Context += Get-Content $ProgressFile -Raw }}

    # 2. Ask the model
    try {{
        gh copilot suggest `
            "Read PRD and progress. Pick next pending task. `
             Implement fully. Mark done in PRD.json. `
             Append to progress.txt. `
             Context: $($Context.Substring(0, `
             [Math]::Min(4000, $Context.Length)))"
    }} catch {{
        Write-Host "  gh copilot not available — using fallback" -ForegroundColor DarkYellow
    }}
{compound_review}
    # 3. Stage and commit
    $diff = git diff --stat 2>$null
    if ($diff) {{
        git add -A
        git commit -m "ralph: iteration $i — $(Get-Date -Format 'HH:mm:ss')" 2>$null
    }} else {{
        Write-Host "  No changes in iteration $i" -ForegroundColor DarkGray
    }}

    Write-Host "  Iteration $i complete" -ForegroundColor Green
    Write-Host ""
}}

Write-Host "Ralph Loop complete — $Iterations iterations" -ForegroundColor Cyan
{compound_reflection}
Write-Host "   Run 'ignition verify .' to check the output."
"""
