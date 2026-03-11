"""Run-state models and persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path

from clinical_computer_use.config import TRACE_DIR
from clinical_computer_use.runtime.checkpoint_policy import append_checkpoint_with_policy
from clinical_computer_use.runtime.checkpoints import Checkpoint
from clinical_computer_use.runtime.context_compaction import compact_run_context
from clinical_computer_use.runtime.surfaces import ChartSurfaceState
from clinical_computer_use.runtime.autonomy import AutonomyState
from clinical_computer_use.runtime.ledgers import RunLedgers
from clinical_computer_use.runtime.versioning import RunVersionBundle, build_run_version_bundle
from clinical_computer_use.schemas.contract_types import RunLifecycleState
from clinical_computer_use.schemas.correction_delta import CorrectionDelta, RuntimeDirectiveDelta
from clinical_computer_use.schemas.task_contract import TaskContract
from clinical_computer_use.session import SessionContext


@dataclass
class BoundPatientContext:
    intended_patient_target: str | None = None
    bound_patient_label: str | None = None
    bound_patient_identifier: str | None = None
    last_verified_at: str | None = None
    verification_source: str | None = None
    verification_confidence: float | None = None
    context_valid: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "intended_patient_target": self.intended_patient_target,
            "bound_patient_label": self.bound_patient_label,
            "bound_patient_identifier": self.bound_patient_identifier,
            "last_verified_at": self.last_verified_at,
            "verification_source": self.verification_source,
            "verification_confidence": self.verification_confidence,
            "context_valid": self.context_valid,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "BoundPatientContext":
        return cls(
            intended_patient_target=str(payload.get("intended_patient_target"))
            if payload.get("intended_patient_target") is not None
            else None,
            bound_patient_label=str(payload.get("bound_patient_label")) if payload.get("bound_patient_label") is not None else None,
            bound_patient_identifier=str(payload.get("bound_patient_identifier"))
            if payload.get("bound_patient_identifier") is not None
            else None,
            last_verified_at=str(payload.get("last_verified_at")) if payload.get("last_verified_at") is not None else None,
            verification_source=str(payload.get("verification_source")) if payload.get("verification_source") is not None else None,
            verification_confidence=float(payload.get("verification_confidence"))
            if payload.get("verification_confidence") is not None
            else None,
            context_valid=bool(payload.get("context_valid", False)),
        )


@dataclass
class RunState:
    session_id: str
    task_name: str
    user_prompt: str
    draft_only: bool
    created_at: str
    task_contract: TaskContract
    bound_patient_context: BoundPatientContext = field(default_factory=BoundPatientContext)
    contract_history: list[CorrectionDelta] = field(default_factory=list)
    runtime_directives: list[RuntimeDirectiveDelta] = field(default_factory=list)
    ledgers: RunLedgers = field(default_factory=RunLedgers)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    autonomy_state: AutonomyState = field(default_factory=AutonomyState)
    lifecycle_state: RunLifecycleState = RunLifecycleState.ACTIVE
    lifecycle_reason: str = ""
    version_bundle: RunVersionBundle = field(default_factory=RunVersionBundle)
    run_version: str = "n1.v2"
    latest_surface_state: ChartSurfaceState | None = None
    last_updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z"))

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "task_name": self.task_name,
            "user_prompt": self.user_prompt,
            "draft_only": self.draft_only,
            "created_at": self.created_at,
            "task_contract": self.task_contract.model_dump(),
            "bound_patient_context": self.bound_patient_context.to_dict(),
            "contract_history": [delta.model_dump() for delta in self.contract_history],
            "runtime_directives": [directive.model_dump() for directive in self.runtime_directives],
            "ledgers": self.ledgers.to_dict(),
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "autonomy_state": self.autonomy_state.to_dict(),
            "lifecycle_state": self.lifecycle_state.value,
            "lifecycle_reason": self.lifecycle_reason,
            "version_bundle": self.version_bundle.to_dict(),
            "run_version": self.run_version,
            "latest_surface_state": self.latest_surface_state.to_dict() if self.latest_surface_state is not None else None,
            "last_updated_at": self.last_updated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RunState":
        raw_history = payload.get("contract_history", [])
        history: list[CorrectionDelta] = []
        if isinstance(raw_history, list):
            for item in raw_history:
                if isinstance(item, dict):
                    history.append(CorrectionDelta.model_validate(item))

        raw_runtime = payload.get("runtime_directives", [])
        runtime_directives: list[RuntimeDirectiveDelta] = []
        if isinstance(raw_runtime, list):
            for item in raw_runtime:
                if isinstance(item, dict):
                    runtime_directives.append(RuntimeDirectiveDelta.model_validate(item))

        raw_checkpoints = payload.get("checkpoints", [])
        checkpoints: list[Checkpoint] = []
        if isinstance(raw_checkpoints, list):
            for item in raw_checkpoints:
                if isinstance(item, dict):
                    checkpoints.append(Checkpoint.from_dict(item))

        ledgers_payload = payload.get("ledgers", {})
        contract_payload = payload.get("task_contract", {})
        patient_payload = payload.get("bound_patient_context", {})
        version_bundle_payload = payload.get("version_bundle", {})
        autonomy_payload = payload.get("autonomy_state", {})
        latest_surface_payload = payload.get("latest_surface_state", {})
        try:
            lifecycle_state = RunLifecycleState(str(payload.get("lifecycle_state", RunLifecycleState.ACTIVE.value)))
        except ValueError:
            lifecycle_state = RunLifecycleState.ACTIVE

        return cls(
            session_id=str(payload.get("session_id", "")),
            task_name=str(payload.get("task_name", "")),
            user_prompt=str(payload.get("user_prompt", "")),
            draft_only=bool(payload.get("draft_only", True)),
            created_at=str(payload.get("created_at", "")),
            task_contract=TaskContract.model_validate(contract_payload if isinstance(contract_payload, dict) else {}),
            bound_patient_context=BoundPatientContext.from_dict(patient_payload if isinstance(patient_payload, dict) else {}),
            contract_history=history,
            runtime_directives=runtime_directives,
            ledgers=RunLedgers.from_dict(ledgers_payload if isinstance(ledgers_payload, dict) else {}),
            checkpoints=checkpoints,
            autonomy_state=AutonomyState.from_dict(autonomy_payload if isinstance(autonomy_payload, dict) else {}),
            lifecycle_state=lifecycle_state,
            lifecycle_reason=str(payload.get("lifecycle_reason", "")),
            version_bundle=RunVersionBundle.from_dict(
                version_bundle_payload if isinstance(version_bundle_payload, dict) else {}
            ),
            run_version=str(payload.get("run_version", "n1.v2")),
            latest_surface_state=ChartSurfaceState.from_dict(latest_surface_payload)
            if isinstance(latest_surface_payload, dict) and latest_surface_payload
            else None,
            last_updated_at=str(
                payload.get("last_updated_at", datetime.now(UTC).isoformat().replace("+00:00", "Z"))
            ),
        )


def _run_state_path(session_id: str) -> Path:
    return TRACE_DIR / session_id / "run_state.json"


def run_state_exists(session_id: str) -> bool:
    return _run_state_path(session_id).exists()


def save_run_state(session: SessionContext, state: RunState) -> Path:
    state.last_updated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    path = _run_state_path(session.session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(state.to_dict(), handle, indent=2)

    with (path.parent / "task_contract.json").open("w", encoding="utf-8") as handle:
        json.dump(state.task_contract.model_dump(), handle, indent=2)
    with (path.parent / "contract_history.json").open("w", encoding="utf-8") as handle:
        json.dump([d.model_dump() for d in state.contract_history], handle, indent=2)
    with (path.parent / "ledgers.json").open("w", encoding="utf-8") as handle:
        json.dump(state.ledgers.to_dict(), handle, indent=2)
    with (path.parent / "bound_patient_context.json").open("w", encoding="utf-8") as handle:
        json.dump(state.bound_patient_context.to_dict(), handle, indent=2)
    with (path.parent / "version_bundle.json").open("w", encoding="utf-8") as handle:
        json.dump(state.version_bundle.to_dict(), handle, indent=2)
    with (path.parent / "latest_surface_state.json").open("w", encoding="utf-8") as handle:
        json.dump(state.latest_surface_state.to_dict() if state.latest_surface_state is not None else {}, handle, indent=2)
    with (path.parent / "lifecycle_state.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "lifecycle_state": state.lifecycle_state.value,
                "lifecycle_reason": state.lifecycle_reason,
            },
            handle,
            indent=2,
        )
    if state.checkpoints:
        with (path.parent / "checkpoint_latest.json").open("w", encoding="utf-8") as handle:
            json.dump(state.checkpoints[-1].to_dict(), handle, indent=2)
    return path


def load_run_state(session_id: str) -> RunState:
    path = _run_state_path(session_id)
    if not path.exists():
        raise RuntimeError(f"Run state not found for session '{session_id}'.")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid run state format at '{path}'.")
    return RunState.from_dict(payload)


def build_initial_run_state(
    *,
    session: SessionContext,
    draft_only: bool,
    contract: TaskContract,
    ledgers: RunLedgers,
    start_checkpoint: Checkpoint,
    version_bundle: RunVersionBundle | None = None,
) -> RunState:
    created_at = session.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return RunState(
        session_id=session.session_id,
        task_name=session.task_name,
        user_prompt=session.user_prompt,
        draft_only=draft_only,
        created_at=created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        task_contract=contract,
        bound_patient_context=BoundPatientContext(intended_patient_target=contract.patient_target),
        contract_history=[],
        runtime_directives=[],
        ledgers=ledgers,
        checkpoints=[start_checkpoint],
        autonomy_state=AutonomyState(),
        lifecycle_state=RunLifecycleState.ACTIVE,
        version_bundle=version_bundle or build_run_version_bundle(),
    )


def load_or_create_run_state(
    *,
    session: SessionContext,
    draft_only: bool,
    contract: TaskContract,
    ledgers: RunLedgers,
    start_checkpoint: Checkpoint,
    version_bundle: RunVersionBundle | None = None,
) -> tuple[RunState, bool]:
    if run_state_exists(session.session_id):
        return load_run_state(session.session_id), False
    state = build_initial_run_state(
        session=session,
        draft_only=draft_only,
        contract=contract,
        ledgers=ledgers,
        start_checkpoint=start_checkpoint,
        version_bundle=version_bundle,
    )
    save_run_state(session, state)
    return state, True


def append_checkpoint_to_state(state: RunState, checkpoint: Checkpoint) -> None:
    append_checkpoint_with_policy(state.checkpoints, checkpoint)


def mark_bound_patient_context(
    state: RunState,
    *,
    bound_patient_label: str | None,
    bound_patient_identifier: str | None,
    verification_source: str,
    verification_confidence: float,
) -> None:
    state.bound_patient_context.bound_patient_label = bound_patient_label
    state.bound_patient_context.bound_patient_identifier = bound_patient_identifier
    state.bound_patient_context.verification_source = verification_source
    state.bound_patient_context.verification_confidence = max(0.0, min(1.0, verification_confidence))
    state.bound_patient_context.last_verified_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    state.bound_patient_context.context_valid = True


def invalidate_patient_context(state: RunState, reason: str) -> None:
    state.bound_patient_context.context_valid = False
    state.bound_patient_context.verification_source = reason
    state.bound_patient_context.last_verified_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")


def apply_correction_to_state(
    state: RunState,
    delta: CorrectionDelta,
    updated_contract: TaskContract,
    checkpoint: Checkpoint,
) -> None:
    state.task_contract = updated_contract
    state.contract_history.append(delta)
    state.runtime_directives.extend(delta.runtime_directives)
    append_checkpoint_with_policy(state.checkpoints, checkpoint)


def session_from_run_state(state: RunState) -> SessionContext:
    created_at = datetime.now(UTC)
    if state.created_at:
        try:
            created_at = datetime.fromisoformat(state.created_at.replace("Z", "+00:00"))
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
        except ValueError:
            created_at = datetime.now(UTC)
    return SessionContext(
        task_name=state.task_name,
        user_prompt=state.user_prompt,
        session_id=state.session_id,
        created_at=created_at,
    )


def summarize_run_state(state: RunState) -> dict[str, object]:
    latest_checkpoint = state.checkpoints[-1].to_dict() if state.checkpoints else None
    return {
        "session_id": state.session_id,
        "task_name": state.task_name,
        "draft_only": state.draft_only,
        "objective_type": state.task_contract.objective_type.value,
        "preferred_surfaces": [surface.value for surface in state.task_contract.preferred_surfaces],
        "required_artifact_classes": [item.value for item in state.task_contract.required_artifact_classes],
        "acceptable_artifact_classes": [item.value for item in state.task_contract.acceptable_artifact_classes],
        "disallowed_artifact_classes": [item.value for item in state.task_contract.disallowed_artifact_classes],
        "artifact_match_mode": state.task_contract.artifact_match_mode.value,
        "date_floor": state.task_contract.date_floor,
        "uncertainties": list(state.task_contract.uncertainties),
        "contract_diagnostics": state.task_contract.diagnostics.model_dump(),
        "contract_history_count": len(state.contract_history),
        "runtime_directive_count": len(state.runtime_directives),
        "checkpoint_count": len(state.checkpoints),
        "search_episode_count": len(state.ledgers.search_episodes),
        "artifact_registry_count": len(state.ledgers.artifact_registry),
        "evidence_record_count": len(state.ledgers.evidence_records),
        "rejected_candidates": list(state.ledgers.rejected_candidates),
        "opened_candidates": list(state.ledgers.opened_candidates),
        "last_candidate_key": state.ledgers.last_candidate_key,
        "bound_patient_context": state.bound_patient_context.to_dict(),
        "latest_surface_state": state.latest_surface_state.to_dict() if state.latest_surface_state is not None else None,
        "autonomy_state": state.autonomy_state.to_dict(),
        "lifecycle_state": state.lifecycle_state.value,
        "lifecycle_reason": state.lifecycle_reason,
        "version_bundle": state.version_bundle.to_dict(),
        "compact_context": compact_run_context(state),
        "latest_checkpoint": latest_checkpoint,
        "last_updated_at": state.last_updated_at,
    }


__all__ = [
    "SessionContext",
    "BoundPatientContext",
    "RunVersionBundle",
    "RunState",
    "build_initial_run_state",
    "load_or_create_run_state",
    "append_checkpoint_to_state",
    "mark_bound_patient_context",
    "invalidate_patient_context",
    "save_run_state",
    "load_run_state",
    "run_state_exists",
    "apply_correction_to_state",
    "session_from_run_state",
    "summarize_run_state",
]




