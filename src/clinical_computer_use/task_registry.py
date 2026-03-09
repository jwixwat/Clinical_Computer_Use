"""
Task registry for supervised agent tasks.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskDefinition:
    name: str
    description: str
    draft_only: bool = True


TASKS: dict[str, TaskDefinition] = {
    "wcb_form_draft": TaskDefinition(
        name="wcb_form_draft",
        description="Draft a WCB-style form from chart evidence without submission.",
    ),
    "insurance_form_draft": TaskDefinition(
        name="insurance_form_draft",
        description="Draft an insurance/disability form from chart evidence without submission.",
    ),
}


def get_task(name: str) -> TaskDefinition:
    try:
        return TASKS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown task: {name}") from exc
