"""Deterministic context compaction for long-running N1 sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clinical_computer_use.runtime.run_state import RunState


def compact_run_context(
    state: "RunState",
    *,
    max_search_episodes: int = 8,
    max_artifacts: int = 10,
    max_evidence: int = 8,
    max_uncertainties: int = 8,
) -> dict[str, object]:
    recent_episodes = state.ledgers.search_episodes[-max_search_episodes:]
    artifact_items = list(state.ledgers.artifact_registry.items())
    recent_artifacts = artifact_items[-max_artifacts:]
    recent_evidence = state.ledgers.evidence_records[-max_evidence:]

    return {
        "session_id": state.session_id,
        "task_name": state.task_name,
        "objective_type": state.task_contract.objective_type.value,
        "preferred_surfaces": [surface.value for surface in state.task_contract.preferred_surfaces],
        "required_artifact_classes": [item.value for item in state.task_contract.required_artifact_classes],
        "acceptable_artifact_classes": [item.value for item in state.task_contract.acceptable_artifact_classes],
        "disallowed_artifact_classes": [item.value for item in state.task_contract.disallowed_artifact_classes],
        "date_floor": state.task_contract.date_floor,
        "artifact_match_mode": state.task_contract.artifact_match_mode.value,
        "diagnostics": state.task_contract.diagnostics.model_dump(),
        "bound_patient_context": state.bound_patient_context.to_dict(),
        "recent_search_episodes": [
            {
                "step": episode.step,
                "surface": episode.surface.value,
                "query": episode.query,
                "result_count": episode.result_count,
                "exhausted": episode.exhausted,
                "broadened": episode.broadened,
                "broadening_reason": episode.broadening_reason,
            }
            for episode in recent_episodes
        ],
        "recent_artifacts": [
            {
                "key": key,
                "surface": record.source_surface.value,
                "class": record.provisional_class.value,
                "opened_count": record.opened_count,
                "verified": record.verified,
                "rejected_reason": record.rejected_reason,
            }
            for key, record in recent_artifacts
        ],
        "recent_evidence": [
            {
                "id": evidence.evidence_id,
                "step": evidence.step,
                "surface": evidence.source_surface.value,
                "kind": evidence.kind,
                "artifact_key": evidence.artifact_key,
            }
            for evidence in recent_evidence
        ],
        "uncertainties": list(state.task_contract.uncertainties[-max_uncertainties:])
        + list(state.ledgers.uncertainties[-max_uncertainties:]),
    }
