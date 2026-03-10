"""Canonical operational understanding block used at supervision boundaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clinical_computer_use.runtime.run_state import RunState


def build_operational_understanding_block(
    state: "RunState",
    *,
    next_safest_actions: list[str] | None = None,
) -> dict[str, object]:
    contract = state.task_contract
    non_goals: list[str] = []
    if contract.disallowed_artifact_classes:
        non_goals.append(
            "disallowed_artifact_classes:" + ",".join(sorted(item.value for item in contract.disallowed_artifact_classes))
        )
    non_goals.extend(
        [
            "tier2_save_persist_not_in_default_n0_n1_execution_scope",
            "tier3_transmit_finalize_forbidden_in_n0_n1",
        ]
    )
    return {
        "objective_type": contract.objective_type.value,
        "patient_target": contract.patient_target,
        "required_artifact_classes": [item.value for item in contract.required_artifact_classes],
        "acceptable_artifact_classes": [item.value for item in contract.acceptable_artifact_classes],
        "disallowed_artifact_classes": [item.value for item in contract.disallowed_artifact_classes],
        "preferred_surfaces": [item.value for item in contract.preferred_surfaces],
        "date_constraints": {"date_floor": contract.date_floor, "date_ceiling": contract.date_ceiling},
        "missing_fields_or_uncertainties": list(contract.uncertainties) + list(state.ledgers.uncertainties),
        "explicit_non_goals": non_goals,
        "next_safest_actions": next_safest_actions or [],
    }


def render_operational_understanding_text(block: dict[str, object]) -> str:
    lines = ["Operational understanding:"]
    lines.append(f"- objective_type: {block.get('objective_type')}")
    lines.append(f"- patient_target: {block.get('patient_target')}")
    lines.append(f"- preferred_surfaces: {', '.join(block.get('preferred_surfaces', []))}")
    lines.append(f"- required_classes: {', '.join(block.get('required_artifact_classes', [])) or 'none'}")
    lines.append(f"- disallowed_classes: {', '.join(block.get('disallowed_artifact_classes', [])) or 'none'}")
    constraints = block.get("date_constraints", {})
    if isinstance(constraints, dict):
        lines.append(
            f"- date_floor/date_ceiling: {constraints.get('date_floor')} / {constraints.get('date_ceiling')}"
        )
    missing = block.get("missing_fields_or_uncertainties", [])
    if isinstance(missing, list) and missing:
        lines.append(f"- uncertainties: {', '.join(str(item) for item in missing[:6])}")
    non_goals = block.get("explicit_non_goals", [])
    if isinstance(non_goals, list) and non_goals:
        lines.append(f"- non_goals: {', '.join(str(item) for item in non_goals[:4])}")
    return "\n".join(lines)

