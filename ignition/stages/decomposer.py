"""Stage 3 — Decompose: break requirements into atomic T/B/I/C tasks."""

from __future__ import annotations

import json

from openai import OpenAI

from ignition.config import IgnitionConfig
from ignition.llm import chat_json, get_client
from ignition.models import ParsedRequirements, Task, TaskCategory

DECOMPOSE_SYSTEM = """\
You are a senior staff engineer and project decomposition expert.

Given a set of software requirements, break them down into 30–50 ATOMIC tasks.
Each task MUST pass the Decomposition Test (T/B/I/C):

  T — Testable: a type checker or automated test can verify it
  B — Bounded: completable in ONE iteration (<30 min of focused coding)
  I — Independent: does not require incomplete tasks to be finished first
  C — Committable: produces a meaningful, self-contained git commit

Rules:
- Number tasks sequentially starting from 1
- Group by category: infra, backend, frontend, database, agent, cicd, docs, test
- Order by dependency — infra first, then DB, then backend, frontend, agent, cicd, docs, tests
- Include "dependencies" as list of task IDs (empty = fully independent)
- Each task.description must be specific enough for an LLM to implement from
- If a feature would take >30 min, SPLIT it into sub-tasks

Respond with JSON:
{
  "tasks": [
    {
      "id": 1,
      "title": "...",
      "category": "infra|backend|frontend|database|agent|cicd|docs|test",
      "description": "Detailed specification...",
      "dependencies": [],
      "testable": true,
      "bounded": true,
      "independent": true,
      "committable": true
    },
    ...
  ]
}
"""


def decompose(
    requirements: ParsedRequirements,
    config: IgnitionConfig,
    client: OpenAI | None = None,
) -> list[Task]:
    """Decompose parsed requirements into atomic tasks."""
    if client is None:
        client = get_client(config)

    user_msg = f"""Project Summary: {requirements.summary}

Domain: {requirements.domain_hint}

Features:
{chr(10).join(f"- {f}" for f in requirements.features)}

Constraints:
{chr(10).join(f"- {c}" for c in requirements.constraints)}

Actors/Personas:
{chr(10).join(f"- {a}" for a in requirements.actors)}

Generate 30-50 atomic tasks following the T/B/I/C decomposition test."""

    result = chat_json(
        client,
        model=config.model,
        system=DECOMPOSE_SYSTEM,
        user=user_msg,
        max_tokens=8192,
    )
    data = json.loads(result)
    tasks: list[Task] = []
    for t in data.get("tasks", []):
        tasks.append(
            Task(
                id=t["id"],
                title=t["title"],
                category=TaskCategory(t.get("category", "backend")),
                description=t["description"],
                dependencies=t.get("dependencies", []),
                testable=t.get("testable", True),
                bounded=t.get("bounded", True),
                independent=t.get("independent", True),
                committable=t.get("committable", True),
            )
        )
    return tasks
