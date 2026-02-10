"""Stage 8.5 — Reflection: post-iteration learning and pattern extraction."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from openai import OpenAI

from ignition.compound import (
    CompoundSession,
    IterationReflection,
    LearnedPattern,
    PatternType,
    ReflectionReport,
)
from ignition.config import IgnitionConfig
from ignition.llm import chat_json, get_client
from ignition.models import IterationResult, PRD, Task

REFLECTION_SYSTEM = """\
You are an engineering retrospective analyst. Your job is to analyze iteration outcomes
and extract patterns that can improve future iterations.

For each iteration, analyze:

1. SUCCESS FACTORS: What contributed to success?
   - Good task definition
   - Appropriate scope
   - Clear dependencies
   - Effective testing approach

2. FAILURE CAUSES: What caused failures? (root cause analysis)
   - Unclear requirements
   - Missing dependencies
   - Scope creep
   - Technical blockers
   - Integration issues

3. PATTERNS: What patterns emerge?
   - Success patterns: approaches that worked well
   - Anti-patterns: approaches that caused problems
   - Consider: task category, complexity, dependencies

4. IMPROVEMENT SUGGESTIONS:
   - How to prevent similar failures
   - How to replicate successes
   - Changes to planning, process, or tooling

Respond with JSON:
{
  "iteration_analysis": {
    "what_worked": ["Good modular design", "Comprehensive tests"],
    "what_failed": ["Missing edge case handling"],
    "root_causes": ["Task description didn't specify edge cases"],
    "patterns_identified": ["pattern-id-1", "pattern-id-2"]
  },
  "new_patterns": [
    {
      "pattern_type": "success|anti",
      "category": "backend|frontend|...",
      "description": "Breaking UI tasks into component + logic + test",
      "context": "When building new UI components",
      "confidence": 0.8
    }
  ],
  "improvement_suggestions": [
    "Add edge case section to task template",
    "Run static analysis before commit"
  ]
}
"""

FINAL_REFLECTION_SYSTEM = """\
You are an engineering retrospective analyst. Analyze the complete run of iterations
and provide a comprehensive reflection report.

Analyze:
1. Overall success rate and trends
2. Common success factors across iterations
3. Common failure causes
4. Patterns that emerged (both successful and problematic)
5. Recommendations for the next run

Focus on actionable insights that will improve future runs.

Respond with JSON:
{
  "top_success_factors": ["Clear task definitions", "Good test coverage"],
  "top_failure_causes": ["Scope creep in frontend tasks", "Missing integration tests"],
  "pattern_summary": {
    "success_patterns": ["Modular design", "Test-first approach"],
    "anti_patterns": ["Skipping code review", "Large commits"]
  },
  "recommendations_for_next_run": [
    "Break frontend tasks into smaller units",
    "Add integration test task after each feature",
    "Review task scope before starting"
  ]
}
"""


def reflect_on_iteration(
    iteration: int,
    task: Task,
    result: IterationResult,
    context: dict,
    config: IgnitionConfig,
    client: OpenAI | None = None,
) -> IterationReflection:
    """Reflect on a single iteration's outcome."""
    if client is None:
        client = get_client(config)
    
    user_msg = f"""Analyze this iteration:

Iteration: {iteration}
Task ID: {task.id}
Task Title: {task.title}
Task Category: {task.category.value}
Task Description: {task.description}
Dependencies: {task.dependencies}

Outcome: {"SUCCESS" if result.success else "FAILURE"}
Duration: {result.duration_seconds:.1f} seconds
{f"Error: {result.error}" if result.error else ""}

Additional context:
- Files changed: {context.get("files_changed", [])}
- Tests run: {context.get("tests_run", 0)}
- Tests passed: {context.get("tests_passed", 0)}
- Review score: {context.get("review_score", "N/A")}

What worked, what failed, and what patterns do you observe?"""

    response = chat_json(
        client,
        model=config.model,
        system=REFLECTION_SYSTEM,
        user=user_msg,
        max_tokens=2048,
    )
    data = json.loads(response)
    
    analysis = data.get("iteration_analysis", {})
    
    return IterationReflection(
        iteration=iteration,
        task_id=task.id,
        task_title=task.title,
        success=result.success,
        duration_seconds=result.duration_seconds,
        what_worked=analysis.get("what_worked", []),
        what_failed=analysis.get("what_failed", []),
        root_causes=analysis.get("root_causes", []),
        patterns_identified=analysis.get("patterns_identified", []),
        improvement_suggestions=data.get("improvement_suggestions", []),
    )


def extract_patterns_from_reflection(
    reflection: IterationReflection,
    raw_data: dict,
    task: Task,
) -> list[LearnedPattern]:
    """Extract learned patterns from reflection data."""
    patterns: list[LearnedPattern] = []
    
    for p in raw_data.get("new_patterns", []):
        pattern_type_str = p.get("pattern_type", "neutral")
        try:
            pattern_type = PatternType(pattern_type_str)
        except ValueError:
            pattern_type = PatternType.NEUTRAL
        
        patterns.append(
            LearnedPattern(
                id=f"pattern-{uuid4().hex[:8]}",
                pattern_type=pattern_type,
                category=p.get("category", task.category.value),
                description=p.get("description", ""),
                context=p.get("context", ""),
                confidence=p.get("confidence", 0.5),
                evidence=[f"iteration-{reflection.iteration}"],
                times_observed=1,
                times_successful=1 if reflection.success else 0,
            )
        )
    
    return patterns


def generate_final_reflection(
    prd: PRD,
    iteration_results: list[IterationResult],
    reflections: list[IterationReflection],
    session: CompoundSession,
    config: IgnitionConfig,
    client: OpenAI | None = None,
) -> ReflectionReport:
    """Generate a comprehensive reflection report after all iterations."""
    if client is None:
        client = get_client(config)
    
    # Build summary for LLM
    iterations_summary = []
    for result in iteration_results:
        iterations_summary.append({
            "iteration": result.iteration,
            "task_id": result.task_id,
            "task_title": result.task_title,
            "success": result.success,
            "duration": result.duration_seconds,
            "error": result.error if result.error else None,
        })
    
    reflections_summary = []
    for r in reflections:
        reflections_summary.append({
            "iteration": r.iteration,
            "success": r.success,
            "what_worked": r.what_worked,
            "what_failed": r.what_failed,
            "root_causes": r.root_causes,
        })
    
    patterns_summary = [
        {
            "type": p.pattern_type.value,
            "category": p.category,
            "description": p.description,
            "confidence": p.confidence,
            "times_observed": p.times_observed,
        }
        for p in session.pattern_library
    ]
    
    user_msg = f"""Analyze the complete run for project: {prd.project_name}

Total iterations: {len(iteration_results)}
Successful: {sum(1 for r in iteration_results if r.success)}
Failed: {sum(1 for r in iteration_results if not r.success)}

Iteration results:
{json.dumps(iterations_summary, indent=2)}

Individual reflections:
{json.dumps(reflections_summary, indent=2)}

Patterns observed:
{json.dumps(patterns_summary, indent=2)}

Provide a comprehensive analysis and recommendations for future runs."""

    response = chat_json(
        client,
        model=config.model,
        system=FINAL_REFLECTION_SYSTEM,
        user=user_msg,
        max_tokens=4096,
    )
    data = json.loads(response)
    
    success_count = sum(1 for r in iteration_results if r.success)
    total_duration = sum(r.duration_seconds for r in iteration_results)
    
    return ReflectionReport(
        project_name=prd.project_name,
        total_iterations=len(iteration_results),
        successful_iterations=success_count,
        failed_iterations=len(iteration_results) - success_count,
        success_rate=(success_count / len(iteration_results) * 100) if iteration_results else 0.0,
        total_duration_seconds=total_duration,
        iteration_reflections=reflections,
        learned_patterns=session.pattern_library,
        top_success_factors=data.get("top_success_factors", []),
        top_failure_causes=data.get("top_failure_causes", []),
        recommendations_for_next_run=data.get("recommendations_for_next_run", []),
    )


def update_pattern_library(
    session: CompoundSession,
    new_patterns: list[LearnedPattern],
) -> None:
    """Update the session's pattern library with new patterns."""
    for pattern in new_patterns:
        # Check for similar existing patterns
        existing = find_similar_pattern(session.pattern_library, pattern)
        if existing:
            # Merge evidence
            existing.times_observed += 1
            existing.evidence.extend(pattern.evidence)
            existing.last_seen = datetime.now()
            if pattern.pattern_type == PatternType.SUCCESS:
                existing.times_successful += 1
            # Update confidence
            existing.confidence = existing.times_successful / existing.times_observed
        else:
            session.add_pattern(pattern)


def find_similar_pattern(
    patterns: list[LearnedPattern],
    new_pattern: LearnedPattern,
    similarity_threshold: float = 0.7,
) -> LearnedPattern | None:
    """Find a similar pattern in the library (simple string matching for now)."""
    for existing in patterns:
        if existing.category != new_pattern.category:
            continue
        if existing.pattern_type != new_pattern.pattern_type:
            continue
        # Simple similarity: check if descriptions share significant words
        existing_words = set(existing.description.lower().split())
        new_words = set(new_pattern.description.lower().split())
        if len(existing_words) == 0 or len(new_words) == 0:
            continue
        overlap = len(existing_words & new_words)
        similarity = overlap / max(len(existing_words), len(new_words))
        if similarity >= similarity_threshold:
            return existing
    return None


def get_relevant_patterns(
    session: CompoundSession,
    task: Task,
    min_confidence: float = 0.5,
) -> tuple[list[LearnedPattern], list[LearnedPattern]]:
    """Get success patterns and anti-patterns relevant to a task."""
    success_patterns = session.get_patterns_for_category(
        task.category.value, PatternType.SUCCESS
    )
    anti_patterns = session.get_patterns_for_category(
        task.category.value, PatternType.ANTI
    )
    
    # Filter by confidence
    success_patterns = [p for p in success_patterns if p.confidence >= min_confidence]
    anti_patterns = [p for p in anti_patterns if p.confidence >= min_confidence]
    
    return success_patterns, anti_patterns


def generate_task_guidance(
    task: Task,
    success_patterns: list[LearnedPattern],
    anti_patterns: list[LearnedPattern],
) -> str:
    """Generate guidance for a task based on learned patterns."""
    guidance_parts = [
        f"## Guidance for Task: {task.title}",
        f"Category: {task.category.value}",
        "",
    ]
    
    if success_patterns:
        guidance_parts.append("### Recommended Approaches (Success Patterns)")
        for p in success_patterns[:3]:  # Top 3
            guidance_parts.append(
                f"- {p.description} (confidence: {p.confidence:.0%})"
            )
        guidance_parts.append("")
    
    if anti_patterns:
        guidance_parts.append("### Avoid These Approaches (Anti-Patterns)")
        for p in anti_patterns[:3]:  # Top 3
            guidance_parts.append(
                f"- ⚠️ {p.description} (observed: {p.times_observed}x)"
            )
        guidance_parts.append("")
    
    if not success_patterns and not anti_patterns:
        guidance_parts.append("No specific patterns learned yet for this task category.")
    
    return "\n".join(guidance_parts)


def save_reflection(reflection: IterationReflection, work_dir: Path) -> Path:
    """Save an iteration reflection to the compound directory."""
    compound_dir = work_dir / ".compound" / "reflections"
    compound_dir.mkdir(parents=True, exist_ok=True)
    
    path = compound_dir / f"reflection_iter_{reflection.iteration}.json"
    path.write_text(reflection.model_dump_json(indent=2), encoding="utf-8")
    return path


def save_final_report(report: ReflectionReport, work_dir: Path) -> Path:
    """Save the final reflection report."""
    compound_dir = work_dir / ".compound"
    compound_dir.mkdir(parents=True, exist_ok=True)
    
    path = compound_dir / "reflection_report.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_reflections(work_dir: Path) -> list[IterationReflection]:
    """Load all iteration reflections from the compound directory."""
    reflections_dir = work_dir / ".compound" / "reflections"
    if not reflections_dir.exists():
        return []
    
    reflections: list[IterationReflection] = []
    for path in sorted(reflections_dir.glob("reflection_iter_*.json")):
        reflections.append(
            IterationReflection.model_validate_json(path.read_text(encoding="utf-8"))
        )
    return reflections


def load_session(work_dir: Path, project_name: str) -> CompoundSession:
    """Load or create a compound engineering session."""
    session_path = work_dir / ".compound" / "session.json"
    
    if session_path.exists():
        return CompoundSession.model_validate_json(
            session_path.read_text(encoding="utf-8")
        )
    
    return CompoundSession(project_name=project_name)


def save_session(session: CompoundSession, work_dir: Path) -> Path:
    """Save the compound engineering session."""
    compound_dir = work_dir / ".compound"
    compound_dir.mkdir(parents=True, exist_ok=True)
    
    session.last_updated = datetime.now()
    path = compound_dir / "session.json"
    path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
    return path
