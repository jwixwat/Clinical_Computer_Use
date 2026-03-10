"""Deterministic checkpoint emission policy for sparse supervisory boundaries."""

from __future__ import annotations

from clinical_computer_use.config import CHECKPOINT_MAX_ROLLING_PER_6_STEPS
from clinical_computer_use.runtime.checkpoints import Checkpoint


def append_checkpoint_with_policy(
    checkpoints: list[Checkpoint],
    checkpoint: Checkpoint,
    *,
    throttle_by_reason: int = 1,
) -> bool:
    if not checkpoints:
        checkpoints.append(checkpoint)
        return True

    last = checkpoints[-1]
    if (
        last.reason == checkpoint.reason
        and last.stage == checkpoint.stage
        and last.task_understanding == checkpoint.task_understanding
        and last.operational_understanding == checkpoint.operational_understanding
        and last.why_done_or_not == checkpoint.why_done_or_not
    ):
        return False

    if throttle_by_reason > 0:
        recent = checkpoints[-(throttle_by_reason + 1) :]
        if any(item.reason == checkpoint.reason and item.stage == checkpoint.stage for item in recent):
            return False

    # Guardrail: avoid dense non-risk checkpoint clusters in small step windows.
    if checkpoint.step_index is not None:
        rolling = [
            item
            for item in checkpoints
            if item.step_index is not None
            and checkpoint.step_index - item.step_index <= 6
            and item.stage not in {"risk_boundary", "completion", "start"}
        ]
        if checkpoint.stage not in {"risk_boundary", "completion", "start"} and len(rolling) >= CHECKPOINT_MAX_ROLLING_PER_6_STEPS:
            return False

    checkpoints.append(checkpoint)
    return True
