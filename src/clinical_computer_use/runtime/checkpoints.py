"""Checkpoint scaffold models and helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


CheckpointStage = Literal["start", "progress", "risk_boundary", "completion", "handoff"]


@dataclass
class Checkpoint:
    task_understanding: str = ""
    where_looked: list[str] = field(default_factory=list)
    found: list[str] = field(default_factory=list)
    why_done_or_not: str = ""
    next_actions: list[str] = field(default_factory=list)
    stage: CheckpointStage = "progress"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def make_start_checkpoint(task_understanding: str, next_actions: list[str] | None = None) -> Checkpoint:
    return Checkpoint(
        task_understanding=task_understanding,
        stage="start",
        next_actions=next_actions or [],
    )
