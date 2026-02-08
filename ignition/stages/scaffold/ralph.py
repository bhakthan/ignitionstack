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
    return f"""\
#!/usr/bin/env bash
# ralph.sh — The IgnitionStack Ralph Loop
# Project: {prd.project_name}
# Iterations: {config.iterations}
#
# Each iteration: read PRD → pick next task → implement → test → commit
# Context window stays clean — no accumulated confusion.

set -euo pipefail

PRD_FILE="PRD.json"
PROGRESS_FILE="progress.txt"
ITERATIONS={config.iterations}
MODEL="${{IGNITION_MODEL:-{config.model}}}"

echo "🔄 Ralph Loop — {prd.project_name}"
echo "   Model: $MODEL"
echo "   Iterations: $ITERATIONS"
echo ""

for i in $(seq 1 $ITERATIONS); do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Iteration $i / $ITERATIONS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # 1. Read PRD + progress
    CONTEXT=$(cat "$PRD_FILE" "$PROGRESS_FILE" 2>/dev/null || echo "{{}}")

    # 2. Ask the model to pick the next task and implement it
    gh copilot suggest \\
        "Read the PRD and progress file. Pick the next pending task whose dependencies are done. \\
         Implement it completely: write code, add tests, handle errors. \\
         Then mark it done in PRD.json and append a log entry to progress.txt. \\
         Context: ${{CONTEXT:0:4000}}" \\
        2>/dev/null || echo "  ⚠️  gh copilot not available — using fallback"

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
echo "   Run 'ignition verify .' to check the output."
"""


def _ralph_powershell(prd: PRD, config: IgnitionConfig) -> str:
    return f"""\
# ralph.ps1 — The IgnitionStack Ralph Loop (PowerShell)
# Project: {prd.project_name}
# Iterations: {config.iterations}

$ErrorActionPreference = "Stop"

$PrdFile = "PRD.json"
$ProgressFile = "progress.txt"
$Iterations = {config.iterations}
$Model = if ($env:IGNITION_MODEL) {{ $env:IGNITION_MODEL }} else {{ "{config.model}" }}

Write-Host "🔄 Ralph Loop — {prd.project_name}" -ForegroundColor Cyan
Write-Host "   Model: $Model"
Write-Host "   Iterations: $Iterations"
Write-Host ""

for ($i = 1; $i -le $Iterations; $i++) {{
    Write-Host ("━" * 40) -ForegroundColor DarkGray
    Write-Host "  Iteration $i / $Iterations" -ForegroundColor Yellow
    Write-Host ("━" * 40) -ForegroundColor DarkGray

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
        Write-Host "  ⚠️  gh copilot not available — using fallback" -ForegroundColor DarkYellow
    }}

    # 3. Stage and commit
    $diff = git diff --stat 2>$null
    if ($diff) {{
        git add -A
        git commit -m "ralph: iteration $i — $(Get-Date -Format 'HH:mm:ss')" 2>$null
    }} else {{
        Write-Host "  ℹ️  No changes in iteration $i" -ForegroundColor DarkGray
    }}

    Write-Host "  ✅ Iteration $i complete" -ForegroundColor Green
    Write-Host ""
}}

Write-Host "🏁 Ralph Loop complete — $Iterations iterations" -ForegroundColor Cyan
Write-Host "   Run 'ignition verify .' to check the output."
"""
