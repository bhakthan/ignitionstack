"""Compound Engineering primitives for IgnitionStack.

Implements the four-step compound engineering loop:
  1. Plan   — validate quality before execution
  2. Work   — execute (existing Ralph loop)
  3. Review — catch issues and technical debt
  4. Compound — reflect, codify learnings, feed forward

Reference: https://every.to/chain-of-thought/compound-engineering-how-every-codes-with-agents
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Planning Quality
# ---------------------------------------------------------------------------


class PlanningDimension(StrEnum):
    """Dimensions of planning quality."""

    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    TESTABILITY = "testability"
    SCOPE = "scope"
    DEPENDENCIES = "dependencies"


class PlanningScore(BaseModel):
    """Score for a single planning dimension."""

    dimension: PlanningDimension
    score: float = Field(ge=0.0, le=1.0, description="0.0–1.0 score")
    reasoning: str = Field(default="", description="Why this score was given")


class TaskPlanQuality(BaseModel):
    """Planning quality assessment for a single task."""

    task_id: int
    task_title: str
    scores: list[PlanningScore] = Field(default_factory=list)
    gaps: list[str] = Field(
        default_factory=list,
        description="Identified gaps or ambiguities in the plan",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Improvements to raise quality",
    )
    definition_of_done: list[str] = Field(
        default_factory=list,
        description="Concrete acceptance criteria",
    )

    @property
    def aggregate_score(self) -> float:
        """Weighted average across all dimensions (0–100)."""
        if not self.scores:
            return 0.0
        return round(sum(s.score for s in self.scores) / len(self.scores) * 100, 1)

    @property
    def passes(self) -> bool:
        """True if aggregate score meets the minimum threshold (70)."""
        return self.aggregate_score >= 70.0


class PlanningReport(BaseModel):
    """Full planning quality report for a PRD."""

    project_name: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    task_assessments: list[TaskPlanQuality] = Field(default_factory=list)
    overall_score: float = 0.0
    blocking_gaps: list[str] = Field(
        default_factory=list,
        description="Gaps that must be resolved before execution",
    )

    def compute_overall(self) -> None:
        """Recompute overall score from task assessments."""
        if self.task_assessments:
            self.overall_score = round(
                sum(a.aggregate_score for a in self.task_assessments)
                / len(self.task_assessments),
                1,
            )


# ---------------------------------------------------------------------------
# Review Gates
# ---------------------------------------------------------------------------


class ReviewSeverity(StrEnum):
    """Severity of a review finding."""

    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class ReviewFinding(BaseModel):
    """A single finding from the review gate."""

    category: str = Field(description="e.g. technical-debt, coupling, test-coverage")
    severity: ReviewSeverity
    description: str
    location: str = Field(default="", description="File or task reference")
    suggestion: str = Field(default="", description="How to fix it")


class ReviewReport(BaseModel):
    """Output of a review gate evaluation."""

    iteration: int
    task_id: int
    task_title: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    findings: list[ReviewFinding] = Field(default_factory=list)
    passed: bool = False
    technical_debt_score: float = Field(
        default=0.0,
        ge=0.0,
        description="0 = no debt, higher = more debt",
    )

    @property
    def blockers(self) -> list[ReviewFinding]:
        return [f for f in self.findings if f.severity == ReviewSeverity.BLOCKER]

    @property
    def warnings(self) -> list[ReviewFinding]:
        return [f for f in self.findings if f.severity == ReviewSeverity.WARNING]

    def evaluate(self, max_debt: float = 50.0) -> None:
        """Set passed based on blockers and debt threshold."""
        self.passed = len(self.blockers) == 0 and self.technical_debt_score <= max_debt


# ---------------------------------------------------------------------------
# Technical Debt Tracking
# ---------------------------------------------------------------------------


class DebtItem(BaseModel):
    """A tracked technical debt item."""

    id: str = Field(description="Unique debt identifier")
    category: str = Field(description="e.g. hardcoded-value, missing-test, tight-coupling")
    description: str
    severity: ReviewSeverity = ReviewSeverity.WARNING
    introduced_iteration: int = 0
    resolved_iteration: int | None = None
    task_id: int | None = None

    @property
    def is_resolved(self) -> bool:
        return self.resolved_iteration is not None


class TechnicalDebtLedger(BaseModel):
    """Running ledger of technical debt across iterations."""

    items: list[DebtItem] = Field(default_factory=list)

    @property
    def open_items(self) -> list[DebtItem]:
        return [i for i in self.items if not i.is_resolved]

    @property
    def resolved_items(self) -> list[DebtItem]:
        return [i for i in self.items if i.is_resolved]

    @property
    def debt_score(self) -> float:
        """Weighted score: blockers=10, warnings=3, info=1."""
        weights = {
            ReviewSeverity.BLOCKER: 10.0,
            ReviewSeverity.WARNING: 3.0,
            ReviewSeverity.INFO: 1.0,
        }
        return sum(weights.get(i.severity, 1.0) for i in self.open_items)

    def add(self, item: DebtItem) -> None:
        self.items.append(item)

    def resolve(self, debt_id: str, iteration: int) -> None:
        for item in self.items:
            if item.id == debt_id and not item.is_resolved:
                item.resolved_iteration = iteration
                break


# ---------------------------------------------------------------------------
# Reflection / Compound — the learning loop
# ---------------------------------------------------------------------------


class PatternType(StrEnum):
    """Whether a recorded pattern is positive or negative."""

    SUCCESS = "success"
    ANTI_PATTERN = "anti_pattern"


class EngineeringPattern(BaseModel):
    """A recorded engineering pattern (success or anti-pattern)."""

    id: str
    pattern_type: PatternType
    title: str
    description: str
    context: str = Field(default="", description="When this pattern applies")
    evidence: list[str] = Field(
        default_factory=list,
        description="Iterations/tasks where this was observed",
    )
    times_observed: int = 1
    first_seen_iteration: int = 0
    last_seen_iteration: int = 0


class SprintRetrospective(BaseModel):
    """Post-sprint reflection — captures learnings for the next sprint."""

    sprint_number: int
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    iterations_completed: int = 0
    tasks_completed: int = 0
    tasks_total: int = 0

    # What happened
    successes: list[str] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
    surprises: list[str] = Field(default_factory=list)

    # Patterns discovered
    new_patterns: list[EngineeringPattern] = Field(default_factory=list)
    reinforced_patterns: list[str] = Field(
        default_factory=list,
        description="IDs of existing patterns that were reinforced",
    )

    # Feed-forward for next sprint
    planning_improvements: list[str] = Field(
        default_factory=list,
        description="How to improve planning in the next sprint",
    )
    process_improvements: list[str] = Field(
        default_factory=list,
        description="How to improve the process in the next sprint",
    )
    knowledge_gaps: list[str] = Field(
        default_factory=list,
        description="What we still don't know and need to research",
    )

    @property
    def completion_rate(self) -> float:
        if self.tasks_total == 0:
            return 0.0
        return round(self.tasks_completed / self.tasks_total * 100, 1)


class PatternLibrary(BaseModel):
    """Persistent library of engineering patterns across sprints."""

    patterns: list[EngineeringPattern] = Field(default_factory=list)

    def add_or_reinforce(self, pattern: EngineeringPattern) -> None:
        """Add a new pattern or reinforce an existing one."""
        for existing in self.patterns:
            if existing.id == pattern.id:
                existing.times_observed += 1
                existing.last_seen_iteration = pattern.last_seen_iteration
                existing.evidence.extend(pattern.evidence)
                return
        self.patterns.append(pattern)

    @property
    def success_patterns(self) -> list[EngineeringPattern]:
        return [p for p in self.patterns if p.pattern_type == PatternType.SUCCESS]

    @property
    def anti_patterns(self) -> list[EngineeringPattern]:
        return [p for p in self.patterns if p.pattern_type == PatternType.ANTI_PATTERN]

    @property
    def top_patterns(self) -> list[EngineeringPattern]:
        """Most reinforced success patterns — the strongest learnings."""
        return sorted(
            self.success_patterns,
            key=lambda p: p.times_observed,
            reverse=True,
        )[:10]


# ---------------------------------------------------------------------------
# Compound Engineering State — persists across sprints
# ---------------------------------------------------------------------------


class CompoundState(BaseModel):
    """
    Persistent compound engineering state.

    Stored in .ignition/compound-state.json and loaded at the start
    of each sprint, enabling recursive self-improvement.
    """

    project_name: str
    current_sprint: int = 1
    total_iterations: int = 0

    # Planning
    planning_reports: list[PlanningReport] = Field(default_factory=list)
    planning_score_trend: list[float] = Field(
        default_factory=list,
        description="Overall planning score per sprint",
    )

    # Reviews
    review_reports: list[ReviewReport] = Field(default_factory=list)

    # Technical Debt
    debt_ledger: TechnicalDebtLedger = Field(
        default_factory=TechnicalDebtLedger,
    )
    debt_score_trend: list[float] = Field(
        default_factory=list,
        description="Debt score at the end of each sprint",
    )

    # Patterns
    pattern_library: PatternLibrary = Field(
        default_factory=PatternLibrary,
    )

    # Retrospectives
    retrospectives: list[SprintRetrospective] = Field(default_factory=list)

    # Feed-forward context for next sprint
    feed_forward: dict[str, Any] = Field(
        default_factory=dict,
        description="Context injected into the next sprint's planning",
    )

    def save(self, work_dir: Path) -> Path:
        """Persist state to .ignition/compound-state.json."""
        state_dir = work_dir / ".ignition"
        state_dir.mkdir(parents=True, exist_ok=True)
        path = state_dir / "compound-state.json"
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, work_dir: Path) -> CompoundState:
        """Load state from .ignition/compound-state.json, or create new."""
        path = work_dir / ".ignition" / "compound-state.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**data)
        return cls(project_name="unknown")

    def begin_sprint(self) -> None:
        """Prepare for a new sprint iteration."""
        self.current_sprint += 1
        # Build feed-forward context from last retrospective
        if self.retrospectives:
            last = self.retrospectives[-1]
            self.feed_forward = {
                "last_sprint": last.sprint_number,
                "completion_rate": last.completion_rate,
                "planning_improvements": last.planning_improvements,
                "process_improvements": last.process_improvements,
                "knowledge_gaps": last.knowledge_gaps,
                "top_patterns": [
                    {"title": p.title, "description": p.description}
                    for p in self.pattern_library.top_patterns[:5]
                ],
                "anti_patterns": [
                    {"title": p.title, "description": p.description}
                    for p in self.pattern_library.anti_patterns[:5]
                ],
                "open_debt_count": len(self.debt_ledger.open_items),
                "debt_score": self.debt_ledger.debt_score,
            }

    def end_sprint(self, retro: SprintRetrospective) -> None:
        """Close the sprint — record retrospective and update trends."""
        self.retrospectives.append(retro)

        # Update pattern library with new patterns
        for pattern in retro.new_patterns:
            self.pattern_library.add_or_reinforce(pattern)

        # Record trends
        if self.planning_reports:
            self.planning_score_trend.append(
                self.planning_reports[-1].overall_score,
            )
        self.debt_score_trend.append(self.debt_ledger.debt_score)

    @property
    def is_improving(self) -> bool:
        """True if planning scores trend up and debt scores trend down."""
        if len(self.planning_score_trend) < 2:
            return True  # not enough data
        plan_improving = (
            self.planning_score_trend[-1] >= self.planning_score_trend[-2]
        )
        if len(self.debt_score_trend) < 2:
            return plan_improving
        debt_improving = (
            self.debt_score_trend[-1] <= self.debt_score_trend[-2]
        )
        return plan_improving and debt_improving
