"""Autonomy budget and progress-tracking helpers."""

from __future__ import annotations

from dataclasses import dataclass

from clinical_computer_use.config import (
    AUTONOMY_MAX_CONSECUTIVE_T0,
    AUTONOMY_MAX_CONSECUTIVE_T1,
    AUTONOMY_MAX_SAME_SURFACE_NO_PROGRESS,
)
from clinical_computer_use.schemas.contract_types import RiskTier


@dataclass
class AutonomyState:
    consecutive_t0: int = 0
    consecutive_t1: int = 0
    same_surface_no_progress: int = 0
    last_surface: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "consecutive_t0": self.consecutive_t0,
            "consecutive_t1": self.consecutive_t1,
            "same_surface_no_progress": self.same_surface_no_progress,
            "last_surface": self.last_surface,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "AutonomyState":
        return cls(
            consecutive_t0=int(payload.get("consecutive_t0", 0) or 0),
            consecutive_t1=int(payload.get("consecutive_t1", 0) or 0),
            same_surface_no_progress=int(payload.get("same_surface_no_progress", 0) or 0),
            last_surface=str(payload.get("last_surface", "")),
        )


def reset_autonomy_leg(state: AutonomyState) -> None:
    state.consecutive_t0 = 0
    state.consecutive_t1 = 0
    state.same_surface_no_progress = 0
    state.last_surface = ""


def record_action(
    state: AutonomyState,
    *,
    tier: RiskTier,
    surface: str,
    progress_made: bool,
) -> None:
    if surface != state.last_surface:
        state.same_surface_no_progress = 0
        state.last_surface = surface

    if tier == RiskTier.TIER0:
        state.consecutive_t0 += 1
        state.consecutive_t1 = 0
    elif tier == RiskTier.TIER1:
        state.consecutive_t1 += 1
        state.consecutive_t0 = 0
    else:
        state.consecutive_t0 = 0
        state.consecutive_t1 = 0

    if progress_made:
        state.same_surface_no_progress = 0
    else:
        state.same_surface_no_progress += 1


def budget_exceeded_reason(state: AutonomyState) -> str | None:
    if state.consecutive_t0 >= AUTONOMY_MAX_CONSECUTIVE_T0:
        return f"autonomy_budget_t0_limit_reached:{AUTONOMY_MAX_CONSECUTIVE_T0}"
    if state.consecutive_t1 >= AUTONOMY_MAX_CONSECUTIVE_T1:
        return f"autonomy_budget_t1_limit_reached:{AUTONOMY_MAX_CONSECUTIVE_T1}"
    if state.same_surface_no_progress >= AUTONOMY_MAX_SAME_SURFACE_NO_PROGRESS:
        return f"autonomy_budget_same_surface_no_progress_limit:{AUTONOMY_MAX_SAME_SURFACE_NO_PROGRESS}"
    return None

