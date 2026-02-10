"""Pipeline stages for the IgnitionStack agent."""

from ignition.stages.decomposer import decompose
from ignition.stages.discovery import discover, save_discovery
from ignition.stages.input import validate_input
from ignition.stages.parser import parse
from ignition.stages.planning import (
    enrich_tasks_from_planning,
    save_planning_report,
    validate_planning,
)
from ignition.stages.prd import generate_prd, init_progress, save_prd
from ignition.stages.reflection import (
    generate_feed_forward_prompt,
    reflect_on_sprint,
    save_retrospective,
)
from ignition.stages.review import (
    apply_review_to_state,
    review_iteration,
    save_review_report,
)

__all__ = [
    "decompose",
    "discover",
    "save_discovery",
    "validate_input",
    "parse",
    "validate_planning",
    "enrich_tasks_from_planning",
    "save_planning_report",
    "generate_prd",
    "init_progress",
    "save_prd",
    "reflect_on_sprint",
    "generate_feed_forward_prompt",
    "save_retrospective",
    "review_iteration",
    "apply_review_to_state",
    "save_review_report",
]
