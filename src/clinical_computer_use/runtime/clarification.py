"""N1 clarification gate helpers."""

from __future__ import annotations

from clinical_computer_use.runtime.checkpoints import Checkpoint, make_checkpoint
from clinical_computer_use.runtime.run_state import RunState
from clinical_computer_use.runtime.understanding import build_operational_understanding_block


def needs_contract_clarification(state: RunState) -> bool:
    return bool(state.task_contract.diagnostics.needs_clarification)


def make_clarification_checkpoint(state: RunState, *, stage: str = "progress", reason: str = "handoff") -> Checkpoint:
    diagnostic = state.task_contract.diagnostics
    details = diagnostic.contradictions + diagnostic.unsupported_constraints
    if not details:
        details = ["contract_diagnostics_flagged_for_clarification"]

    return make_checkpoint(
        stage=stage,
        reason=reason,
        task_understanding=f"Clarification required before continuing '{state.task_name}'",
        operational_understanding=build_operational_understanding_block(
            state,
            next_safest_actions=["request_user_clarification", "apply-correction", "resume_after_clarification"],
        ),
        where_looked=[episode.surface.value for episode in state.ledgers.search_episodes],
        why_done_or_not=(
            "Task contract diagnostics require clarification before active pursuit. "
            f"Details: {', '.join(details)}"
        ),
        next_actions=["request_user_clarification", "apply-correction", "resume_after_clarification"],
    )


def make_correction_clarification_checkpoint(state: RunState, correction_text: str) -> Checkpoint:
    return make_checkpoint(
        stage="progress",
        reason="correction_needs_clarification",
        task_understanding=f"Correction for '{state.task_name}' could not be compiled safely",
        operational_understanding=build_operational_understanding_block(
            state,
            next_safest_actions=["rephrase_correction_with_explicit_constraint", "apply-correction", "continue_after_correction"],
        ),
        where_looked=[episode.surface.value for episode in state.ledgers.search_episodes],
        why_done_or_not=(
            "Correction text did not map to structured deltas. "
            f"Correction: '{correction_text}'"
        ),
        next_actions=["rephrase_correction_with_explicit_constraint", "apply-correction", "continue_after_correction"],
    )
