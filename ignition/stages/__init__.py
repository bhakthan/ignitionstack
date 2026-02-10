"""Pipeline stages for the IgnitionStack agent."""

from ignition.stages.decomposer import decompose
from ignition.stages.discovery import discover, save_discovery
from ignition.stages.input import validate_input
from ignition.stages.parser import parse
from ignition.stages.planning import assess_planning_quality, save_planning_report
from ignition.stages.prd import generate_prd, init_progress, save_prd, load_prd
from ignition.stages.reflection import (
    reflect_on_iteration,
    generate_final_reflection,
    load_session,
    save_session,
)
from ignition.stages.review import (
    run_review_gate,
    generate_debt_report,
    save_review_result,
    save_debt_report,
)

__all__ = [
    "decompose",
    "discover",
    "save_discovery",
    "validate_input",
    "parse",
    "assess_planning_quality",
    "save_planning_report",
    "generate_prd",
    "init_progress",
    "save_prd",
    "load_prd",
    "reflect_on_iteration",
    "generate_final_reflection",
    "load_session",
    "save_session",
    "run_review_gate",
    "generate_debt_report",
    "save_review_result",
    "save_debt_report",
]
