"""Checkpoint models and helpers for supervised run checkpoints."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


CheckpointStage = Literal["start", "progress", "risk_boundary", "completion", "handoff"]
CheckpointReason = Literal[
    "start",
    "candidate_found",
    "surface_exhausted",
    "risk_boundary",
    "completion_claim",
    "correction_applied",
    "handoff",
]


@dataclass
class Checkpoint:
    task_understanding: str = ""
    operational_understanding: dict[str, object] = field(default_factory=dict)
    step_index: int | None = None
    where_looked: list[str] = field(default_factory=list)
    found: list[str] = field(default_factory=list)
    why_done_or_not: str = ""
    next_actions: list[str] = field(default_factory=list)
    stage: CheckpointStage = "progress"
    reason: CheckpointReason = "start"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Checkpoint":
        where_looked_raw = payload.get("where_looked", [])
        found_raw = payload.get("found", [])
        next_actions_raw = payload.get("next_actions", [])
        return cls(
            task_understanding=str(payload.get("task_understanding", "")),
            operational_understanding=payload.get("operational_understanding", {})
            if isinstance(payload.get("operational_understanding", {}), dict)
            else {},
            step_index=int(payload.get("step_index")) if payload.get("step_index") is not None else None,
            where_looked=[str(x) for x in where_looked_raw] if isinstance(where_looked_raw, list) else [],
            found=[str(x) for x in found_raw] if isinstance(found_raw, list) else [],
            why_done_or_not=str(payload.get("why_done_or_not", "")),
            next_actions=[str(x) for x in next_actions_raw] if isinstance(next_actions_raw, list) else [],
            stage=str(payload.get("stage", "progress")),
            reason=str(payload.get("reason", "start")),
        )


def make_start_checkpoint(
    task_understanding: str,
    next_actions: list[str] | None = None,
    operational_understanding: dict[str, object] | None = None,
    step_index: int | None = None,
) -> Checkpoint:
    return Checkpoint(
        task_understanding=task_understanding,
        operational_understanding=operational_understanding or {},
        step_index=step_index,
        stage="start",
        reason="start",
        next_actions=next_actions or [],
    )


def make_checkpoint(
    *,
    stage: CheckpointStage,
    reason: CheckpointReason,
    task_understanding: str,
    operational_understanding: dict[str, object] | None = None,
    step_index: int | None = None,
    where_looked: list[str] | None = None,
    found: list[str] | None = None,
    why_done_or_not: str = "",
    next_actions: list[str] | None = None,
) -> Checkpoint:
    return Checkpoint(
        stage=stage,
        reason=reason,
        task_understanding=task_understanding,
        operational_understanding=operational_understanding or {},
        step_index=step_index,
        where_looked=where_looked or [],
        found=found or [],
        why_done_or_not=why_done_or_not,
        next_actions=next_actions or [],
    )


def make_candidate_found_checkpoint(
    *,
    task_understanding: str,
    where_looked: list[str],
    found: list[str],
    next_actions: list[str],
    operational_understanding: dict[str, object] | None = None,
    step_index: int | None = None,
) -> Checkpoint:
    return make_checkpoint(
        stage="progress",
        reason="candidate_found",
        task_understanding=task_understanding,
        operational_understanding=operational_understanding or {},
        step_index=step_index,
        where_looked=where_looked,
        found=found,
        why_done_or_not="A likely candidate was opened and needs verification.",
        next_actions=next_actions,
    )


def make_surface_exhausted_checkpoint(
    *,
    task_understanding: str,
    where_looked: list[str],
    next_actions: list[str],
    why_done_or_not: str,
    operational_understanding: dict[str, object] | None = None,
    step_index: int | None = None,
) -> Checkpoint:
    return make_checkpoint(
        stage="progress",
        reason="surface_exhausted",
        task_understanding=task_understanding,
        operational_understanding=operational_understanding or {},
        step_index=step_index,
        where_looked=where_looked,
        why_done_or_not=why_done_or_not,
        next_actions=next_actions,
    )


def make_risk_boundary_checkpoint(
    *,
    task_understanding: str,
    where_looked: list[str],
    next_actions: list[str],
    why_done_or_not: str,
    operational_understanding: dict[str, object] | None = None,
    step_index: int | None = None,
) -> Checkpoint:
    return make_checkpoint(
        stage="risk_boundary",
        reason="risk_boundary",
        task_understanding=task_understanding,
        operational_understanding=operational_understanding or {},
        step_index=step_index,
        where_looked=where_looked,
        why_done_or_not=why_done_or_not,
        next_actions=next_actions,
    )


def make_completion_checkpoint(
    *,
    task_understanding: str,
    where_looked: list[str],
    found: list[str],
    why_done_or_not: str,
    next_actions: list[str],
    operational_understanding: dict[str, object] | None = None,
    step_index: int | None = None,
) -> Checkpoint:
    return make_checkpoint(
        stage="completion",
        reason="completion_claim",
        task_understanding=task_understanding,
        operational_understanding=operational_understanding or {},
        step_index=step_index,
        where_looked=where_looked,
        found=found,
        why_done_or_not=why_done_or_not,
        next_actions=next_actions,
    )
