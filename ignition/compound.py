"""Compound Engineering — models and primitives for reducing technical debt."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Technical Debt Tracking
# ---------------------------------------------------------------------------

class DebtSeverity(StrEnum):
    """Severity level of technical debt item."""
    
    LOW = "low"          # Minor code smell, can be deferred
    MEDIUM = "medium"    # Should be addressed within a few iterations
    HIGH = "high"        # Blocking quality, address ASAP
    CRITICAL = "critical"  # Must be fixed before next commit


class DebtCategory(StrEnum):
    """Category of technical debt."""
    
    CODE_SMELL = "code_smell"        # Poor naming, long functions, etc.
    HARDCODED = "hardcoded"          # Magic numbers, hardcoded strings
    MISSING_TEST = "missing_test"    # Untested code paths
    TODO_FIXME = "todo_fixme"        # TODO/FIXME comments left in code
    DUPLICATION = "duplication"      # Copy-paste code
    COUPLING = "coupling"            # Tight coupling between modules
    DOCUMENTATION = "documentation"  # Missing or outdated docs
    DEPENDENCY = "dependency"        # Outdated or problematic deps


class TechnicalDebt(BaseModel):
    """A single technical debt item identified during review."""
    
    id: str = Field(description="Unique identifier for tracking")
    category: DebtCategory
    severity: DebtSeverity
    file_path: str = Field(description="File where debt was found")
    line_number: int | None = Field(default=None, description="Line number if applicable")
    description: str = Field(description="What the debt is")
    suggested_fix: str = Field(default="", description="How to address it")
    iteration_found: int = Field(default=0, description="Which iteration found this")
    resolved: bool = False
    resolution_iteration: int | None = None


class DebtReport(BaseModel):
    """Aggregate report of technical debt across the project."""
    
    total_items: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    debt_score: float = Field(
        default=0.0,
        description="Weighted score (higher = more debt). Target: < 10",
    )
    items: list[TechnicalDebt] = Field(default_factory=list)
    trend: str = Field(
        default="stable",
        description="improving | stable | degrading",
    )


# ---------------------------------------------------------------------------
# Planning Quality
# ---------------------------------------------------------------------------

class PlanningDimension(StrEnum):
    """Dimensions of planning quality assessment."""
    
    COMPLETENESS = "completeness"    # All aspects defined?
    CLARITY = "clarity"              # Unambiguous description?
    TESTABILITY = "testability"      # Can success be verified?
    SCOPE = "scope"                  # Appropriately bounded?
    DEPENDENCIES = "dependencies"    # All deps identified?
    ACCEPTANCE = "acceptance"        # Clear acceptance criteria?


class TaskPlanQuality(BaseModel):
    """Planning quality assessment for a single task."""
    
    task_id: int
    task_title: str
    scores: dict[str, float] = Field(
        default_factory=dict,
        description="Score per dimension (0-100)",
    )
    overall_score: float = Field(
        default=0.0,
        description="Weighted average (0-100)",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Identified planning gaps",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="How to improve the task definition",
    )
    passes_threshold: bool = Field(
        default=False,
        description="True if overall_score >= threshold (default 70)",
    )


class PlanningQualityReport(BaseModel):
    """Aggregate planning quality report for the PRD."""
    
    prd_name: str
    total_tasks: int = 0
    average_score: float = 0.0
    passing_tasks: int = 0
    failing_tasks: int = 0
    threshold: float = 70.0
    task_assessments: list[TaskPlanQuality] = Field(default_factory=list)
    common_gaps: list[str] = Field(
        default_factory=list,
        description="Most frequent planning gaps across tasks",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="High-level recommendations for PRD improvement",
    )


# ---------------------------------------------------------------------------
# Review Gates
# ---------------------------------------------------------------------------

class ReviewCheckType(StrEnum):
    """Types of checks in a review gate."""
    
    CODE_QUALITY = "code_quality"      # Lint, format, complexity
    TEST_COVERAGE = "test_coverage"    # Test presence and coverage
    DEBT_SCAN = "debt_scan"            # Technical debt detection
    DEPENDENCY = "dependency"          # Dependency analysis
    SECURITY = "security"              # Basic security checks
    DOCUMENTATION = "documentation"    # Doc completeness


class ReviewCheckResult(BaseModel):
    """Result of a single review check."""
    
    check_type: ReviewCheckType
    passed: bool
    score: float = Field(default=0.0, description="0-100 score")
    findings: list[str] = Field(default_factory=list)
    blocking: bool = Field(
        default=False,
        description="If True, fails the gate even if other checks pass",
    )


class ReviewGateResult(BaseModel):
    """Result of running a review gate before commit."""
    
    iteration: int
    task_id: int
    task_title: str
    timestamp: datetime = Field(default_factory=datetime.now)
    checks: list[ReviewCheckResult] = Field(default_factory=list)
    overall_passed: bool = False
    overall_score: float = 0.0
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    
    def compute_result(self) -> None:
        """Compute overall pass/fail from individual checks."""
        if not self.checks:
            self.overall_passed = False
            return
        
        # Any blocking failure fails the gate
        blocking_failures = [c for c in self.checks if c.blocking and not c.passed]
        if blocking_failures:
            self.overall_passed = False
            self.blocking_issues = [
                f for c in blocking_failures for f in c.findings
            ]
            return
        
        # Otherwise, use score threshold
        self.overall_score = sum(c.score for c in self.checks) / len(self.checks)
        self.overall_passed = self.overall_score >= 70.0
        self.warnings = [
            f for c in self.checks if not c.passed for f in c.findings
        ]


# ---------------------------------------------------------------------------
# Self-Improvement / Reflection
# ---------------------------------------------------------------------------

class PatternType(StrEnum):
    """Type of pattern learned from iterations."""
    
    SUCCESS = "success"      # Pattern that led to success
    ANTI = "anti"            # Anti-pattern that caused problems
    NEUTRAL = "neutral"      # Observed pattern, not yet classified


class LearnedPattern(BaseModel):
    """A pattern learned from iteration analysis."""
    
    id: str
    pattern_type: PatternType
    category: str = Field(description="Task category this applies to")
    description: str = Field(description="What the pattern is")
    context: str = Field(default="", description="When this pattern applies")
    evidence: list[str] = Field(
        default_factory=list,
        description="Iterations/tasks that demonstrate this pattern",
    )
    confidence: float = Field(
        default=0.5,
        description="0-1 confidence score based on evidence",
    )
    times_observed: int = 1
    times_successful: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)


class IterationReflection(BaseModel):
    """Reflection on a single iteration's outcome."""
    
    iteration: int
    task_id: int
    task_title: str
    success: bool
    duration_seconds: float = 0.0
    what_worked: list[str] = Field(default_factory=list)
    what_failed: list[str] = Field(default_factory=list)
    root_causes: list[str] = Field(
        default_factory=list,
        description="Root cause analysis for failures",
    )
    patterns_identified: list[str] = Field(
        default_factory=list,
        description="Pattern IDs observed in this iteration",
    )
    improvement_suggestions: list[str] = Field(default_factory=list)


class ReflectionReport(BaseModel):
    """Aggregate reflection after all iterations."""
    
    project_name: str
    total_iterations: int = 0
    successful_iterations: int = 0
    failed_iterations: int = 0
    success_rate: float = 0.0
    total_duration_seconds: float = 0.0
    iteration_reflections: list[IterationReflection] = Field(default_factory=list)
    learned_patterns: list[LearnedPattern] = Field(default_factory=list)
    top_success_factors: list[str] = Field(default_factory=list)
    top_failure_causes: list[str] = Field(default_factory=list)
    recommendations_for_next_run: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Compound Engineering Metrics
# ---------------------------------------------------------------------------

class CompoundMetrics(BaseModel):
    """Metrics for tracking compound engineering effectiveness."""
    
    project_name: str
    timestamp: datetime = Field(default_factory=datetime.now)
    iteration: int = 0
    
    # Planning metrics
    planning_quality_score: float = 0.0
    tasks_passing_planning_threshold: int = 0
    
    # Review metrics
    review_gate_pass_rate: float = 0.0
    average_review_score: float = 0.0
    
    # Debt metrics
    technical_debt_score: float = 0.0
    debt_items_total: int = 0
    debt_items_resolved: int = 0
    debt_trend: str = "stable"
    
    # Self-improvement metrics
    patterns_learned: int = 0
    success_patterns: int = 0
    anti_patterns: int = 0
    
    # Overall compound score (weighted aggregate)
    compound_score: float = Field(
        default=0.0,
        description="0-100 overall compound engineering health",
    )
    
    def compute_compound_score(self) -> float:
        """Compute weighted compound engineering score."""
        weights = {
            "planning": 0.25,
            "review": 0.25,
            "debt": 0.25,
            "learning": 0.25,
        }
        
        # Normalize debt score (lower is better, invert it)
        debt_normalized = max(0, 100 - self.technical_debt_score * 10)
        
        # Learning score based on pattern ratio
        if self.patterns_learned > 0:
            learning_score = (self.success_patterns / self.patterns_learned) * 100
        else:
            learning_score = 50.0  # Neutral if no patterns yet
        
        self.compound_score = (
            weights["planning"] * self.planning_quality_score +
            weights["review"] * self.average_review_score +
            weights["debt"] * debt_normalized +
            weights["learning"] * learning_score
        )
        return self.compound_score


class MetricsHistory(BaseModel):
    """Historical metrics for trend analysis."""
    
    project_name: str
    snapshots: list[CompoundMetrics] = Field(default_factory=list)
    
    @property
    def latest(self) -> CompoundMetrics | None:
        return self.snapshots[-1] if self.snapshots else None
    
    def trend(self, metric: str, window: int = 5) -> str:
        """Analyze trend for a specific metric over recent snapshots."""
        if len(self.snapshots) < 2:
            return "insufficient_data"
        
        recent = self.snapshots[-window:]
        values = [getattr(s, metric, 0) for s in recent]
        
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear trend
        avg_first_half = sum(values[:len(values)//2]) / (len(values)//2)
        avg_second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff = avg_second_half - avg_first_half
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "degrading"
        return "stable"


# ---------------------------------------------------------------------------
# Compound Engineering Session State
# ---------------------------------------------------------------------------

class CompoundSession(BaseModel):
    """Persistent state for compound engineering across runs."""
    
    project_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Historical data
    metrics_history: MetricsHistory = Field(default_factory=lambda: MetricsHistory(project_name=""))
    pattern_library: list[LearnedPattern] = Field(default_factory=list)
    debt_backlog: list[TechnicalDebt] = Field(default_factory=list)
    
    # Current run state
    current_iteration: int = 0
    planning_report: PlanningQualityReport | None = None
    review_results: list[ReviewGateResult] = Field(default_factory=list)
    reflections: list[IterationReflection] = Field(default_factory=list)
    
    def add_pattern(self, pattern: LearnedPattern) -> None:
        """Add or update a pattern in the library."""
        existing = next(
            (p for p in self.pattern_library if p.id == pattern.id),
            None,
        )
        if existing:
            existing.times_observed += 1
            existing.last_seen = datetime.now()
            if pattern.pattern_type == PatternType.SUCCESS:
                existing.times_successful += 1
            # Update confidence based on success rate
            existing.confidence = existing.times_successful / existing.times_observed
        else:
            self.pattern_library.append(pattern)
        self.last_updated = datetime.now()
    
    def get_patterns_for_category(
        self, category: str, pattern_type: PatternType | None = None
    ) -> list[LearnedPattern]:
        """Get relevant patterns for a task category."""
        patterns = [p for p in self.pattern_library if p.category == category]
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        return sorted(patterns, key=lambda p: p.confidence, reverse=True)
    
    def model_post_init(self, __context: Any) -> None:
        """Initialize metrics history with project name."""
        if not self.metrics_history.project_name:
            self.metrics_history.project_name = self.project_name
