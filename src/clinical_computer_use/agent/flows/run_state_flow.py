"""Run-state maintenance flows for correction and handoff loops."""

from __future__ import annotations

from dataclasses import dataclass

from clinical_computer_use.agent.contracts import apply_correction
from clinical_computer_use.runtime.artifacts import append_event, cleanup_tracked_artifacts, write_json_trace
from clinical_computer_use.runtime.checkpoint_policy import append_checkpoint_with_policy
from clinical_computer_use.runtime.checkpoints import make_checkpoint
from clinical_computer_use.runtime.clarification import make_correction_clarification_checkpoint
from clinical_computer_use.runtime.handoff import HandoffPacket, build_handoff_packet
from clinical_computer_use.runtime.ledgers import mark_artifact_rejected, note_broadening, next_step
from clinical_computer_use.runtime.understanding import build_operational_understanding_block
from clinical_computer_use.runtime.run_state import (
    RunState,
    apply_correction_to_state,
    load_run_state,
    save_run_state,
    session_from_run_state,
    summarize_run_state,
)
from clinical_computer_use.schemas.contract_types import RunLifecycleState


@dataclass
class ApplyCorrectionOutcome:
    state: RunState


@dataclass
class RunSummaryOutcome:
    state: RunState
    summary: dict[str, object]


@dataclass
class RunHandoffOutcome:
    state: RunState
    handoff: HandoffPacket


@dataclass
class CleanupArtifactsOutcome:
    summary: dict[str, object]


@dataclass
class RunLifecycleOutcome:
    state: RunState


def apply_run_correction(session_id: str, correction_text: str) -> ApplyCorrectionOutcome:
    state = load_run_state(session_id)
    if state.lifecycle_state in {RunLifecycleState.ARCHIVED, RunLifecycleState.PURGED}:
        raise RuntimeError(f"Cannot apply correction when run lifecycle_state is '{state.lifecycle_state.value}'.")
    correction = apply_correction(state.task_contract, correction_text)
    session = session_from_run_state(state)

    if "no_structured_delta_detected" in correction.delta.notes:
        checkpoint = make_correction_clarification_checkpoint(state, correction_text)
        append_checkpoint_with_policy(state.checkpoints, checkpoint)
        state.lifecycle_state = RunLifecycleState.PAUSED
        state.lifecycle_reason = "correction_clarification_required"
        save_run_state(session, state)
        write_json_trace(session, "checkpoint_correction_clarification_required.json", checkpoint.to_dict())
        handoff = build_handoff_packet(state)
        write_json_trace(session, "handoff_packet.json", handoff.to_dict())
        append_event(
            session,
            "correction_clarification_required",
            {
                "correction_text": correction_text,
                "notes": correction.delta.notes,
                "reason": "no_structured_delta_detected",
            },
        )
        return ApplyCorrectionOutcome(state=state)

    step = next_step(state.ledgers)

    for disposition in correction.delta.artifact_dispositions:
        if disposition.disposition.value == "reject_candidate":
            key = disposition.candidate_key or state.ledgers.last_candidate_key
            if key:
                mark_artifact_rejected(
                    state.ledgers,
                    key=key,
                    reason=disposition.reason or "rejected_by_user_correction",
                    step=step,
                )

    for change in correction.delta.contract_changes:
        if change.field.value in {
            "preferred_surfaces",
            "required_artifact_classes",
            "acceptable_artifact_classes",
            "disallowed_artifact_classes",
            "date_floor",
        }:
            note_broadening(state.ledgers, f"correction_change:{change.field.value}:{change.operation.value}")

    checkpoint = make_checkpoint(
        stage="progress",
        reason="correction_applied",
        task_understanding=f"Apply correction for task '{state.task_name}'",
        operational_understanding=build_operational_understanding_block(
            state, next_safest_actions=["continue_with_updated_contract"]
        ),
        where_looked=[episode.surface.value for episode in state.ledgers.search_episodes],
        why_done_or_not="User correction compiled into structured state deltas and applied.",
        next_actions=["continue_with_updated_contract"],
    )

    apply_correction_to_state(
        state=state,
        delta=correction.delta,
        updated_contract=correction.contract,
        checkpoint=checkpoint,
    )
    state.lifecycle_state = RunLifecycleState.ACTIVE
    state.lifecycle_reason = "correction_applied"

    save_run_state(session, state)
    append_event(
        session,
        "correction_applied",
        {
            "correction_text": correction_text,
            "contract_changes": [change.model_dump() for change in correction.delta.contract_changes],
            "artifact_dispositions": [item.model_dump() for item in correction.delta.artifact_dispositions],
            "runtime_directives": [item.model_dump() for item in correction.delta.runtime_directives],
            "notes": correction.delta.notes,
            "rejected_candidates": list(state.ledgers.rejected_candidates),
        },
    )
    return ApplyCorrectionOutcome(state=state)


def summarize_run(session_id: str) -> RunSummaryOutcome:
    state = load_run_state(session_id)
    return RunSummaryOutcome(state=state, summary=summarize_run_state(state))


def build_run_handoff(session_id: str) -> RunHandoffOutcome:
    state = load_run_state(session_id)
    handoff = build_handoff_packet(state)
    session = session_from_run_state(state)
    append_event(session, "handoff_packet_generated", handoff.to_dict())
    return RunHandoffOutcome(state=state, handoff=handoff)


def cleanup_artifacts(*, older_than_days: int, dry_run: bool = True) -> CleanupArtifactsOutcome:
    result = cleanup_tracked_artifacts(older_than_days=older_than_days, dry_run=dry_run)
    return CleanupArtifactsOutcome(summary=result.to_dict())


def stop_run(session_id: str, *, reason: str = "manual_stop") -> RunLifecycleOutcome:
    state = load_run_state(session_id)
    if state.lifecycle_state in {RunLifecycleState.ARCHIVED, RunLifecycleState.PURGED}:
        raise RuntimeError(f"Cannot stop run from lifecycle_state '{state.lifecycle_state.value}'.")
    state.lifecycle_state = RunLifecycleState.STOPPED
    state.lifecycle_reason = reason
    session = session_from_run_state(state)
    save_run_state(session, state)
    append_event(
        session,
        "run_stopped",
        {
            "reason": reason,
            "lifecycle_state": state.lifecycle_state.value,
        },
    )
    return RunLifecycleOutcome(state=state)


def archive_run(session_id: str, *, reason: str = "manual_archive") -> RunLifecycleOutcome:
    state = load_run_state(session_id)
    if state.lifecycle_state == RunLifecycleState.PURGED:
        raise RuntimeError("Cannot archive a purged run.")
    state.lifecycle_state = RunLifecycleState.ARCHIVED
    state.lifecycle_reason = reason
    session = session_from_run_state(state)
    save_run_state(session, state)
    append_event(
        session,
        "run_archived",
        {
            "reason": reason,
            "lifecycle_state": state.lifecycle_state.value,
        },
    )
    return RunLifecycleOutcome(state=state)
