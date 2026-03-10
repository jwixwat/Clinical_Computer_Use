"""Action prompt module with contract-aware builders."""

from __future__ import annotations

import json

from clinical_computer_use.domain.myle.policy_guidance import build_myle_policy_guidance
from clinical_computer_use.domain.myle.topology import build_myle_topology_guidance
from clinical_computer_use.prompts import build_myle_action_prompt
from clinical_computer_use.schemas.task_contract import TaskContract


def build_contract_aware_action_prompt(
    *,
    contract: TaskContract,
    run_state_summary: dict[str, object],
    step_index: int,
    candidates: list[dict[str, str]],
) -> str:
    candidate_lines: list[str] = []
    for item in candidates[:80]:
        candidate_lines.append(
            f"- id={item['agent_id']} tag={item['tag']} type={item.get('type', '')} label={item['label']}"
        )
    candidate_text = "\n".join(candidate_lines) if candidate_lines else "- none"

    return (
        f"{build_myle_topology_guidance()}\n\n"
        f"{build_myle_policy_guidance()}\n\n"
        "Operational rule: Task contract + run-state are authoritative. "
        "Use visible candidates only as execution affordances, not semantic authority.\n\n"
        "Task contract JSON:\n"
        f"{json.dumps(contract.model_dump(), indent=2)}\n\n"
        "Run-state summary JSON:\n"
        f"{json.dumps(run_state_summary, indent=2)}\n\n"
        f"Current step: {step_index}\n\n"
        "Visible candidate targets:\n"
        f"{candidate_text}\n\n"
        "Choose one action: click, type, scroll, or finish. "
        "Do not violate disallowed artifact classes; runtime policy will gate risk actions separately."
    )


__all__ = ["build_myle_action_prompt", "build_contract_aware_action_prompt"]
