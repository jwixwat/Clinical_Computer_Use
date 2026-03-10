"""Human handoff packet builder."""

from __future__ import annotations

from dataclasses import dataclass

from clinical_computer_use.runtime.run_state import RunState


@dataclass
class HandoffPacket:
    session_id: str
    task_name: str
    task_understanding: str
    operational_understanding: dict[str, object]
    current_patient_context: dict[str, object]
    where_looked: list[str]
    findings: list[str]
    uncertainties: list[str]
    next_actions: list[str]
    approval_needed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "task_name": self.task_name,
            "task_understanding": self.task_understanding,
            "operational_understanding": self.operational_understanding,
            "current_patient_context": self.current_patient_context,
            "where_looked": self.where_looked,
            "findings": self.findings,
            "uncertainties": self.uncertainties,
            "next_actions": self.next_actions,
            "approval_needed": self.approval_needed,
        }


def build_handoff_packet(state: RunState) -> HandoffPacket:
    latest_checkpoint = state.checkpoints[-1] if state.checkpoints else None
    task_understanding = latest_checkpoint.task_understanding if latest_checkpoint else ""
    operational_understanding = latest_checkpoint.operational_understanding if latest_checkpoint else {}
    next_actions = latest_checkpoint.next_actions if latest_checkpoint else []
    where_looked = [episode.surface.value for episode in state.ledgers.search_episodes]

    findings: list[str] = []
    for key, record in list(state.ledgers.artifact_registry.items())[:10]:
        status = "verified" if record.verified else "candidate"
        if record.rejected_reason:
            status = f"rejected:{record.rejected_reason}"
        findings.append(f"{key} [{record.provisional_class.value}] {status}")

    uncertainties = list(state.task_contract.uncertainties) + list(state.ledgers.uncertainties)
    approval_needed = any("review" in action.lower() or "approval" in action.lower() for action in next_actions)

    return HandoffPacket(
        session_id=state.session_id,
        task_name=state.task_name,
        task_understanding=task_understanding,
        operational_understanding=operational_understanding,
        current_patient_context=state.bound_patient_context.to_dict(),
        where_looked=where_looked,
        findings=findings,
        uncertainties=uncertainties,
        next_actions=next_actions,
        approval_needed=approval_needed,
    )
