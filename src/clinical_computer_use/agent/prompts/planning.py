"""Planning prompt module with contract-aware builders."""

from __future__ import annotations

import json

from clinical_computer_use.domain.myle.policy_guidance import build_myle_policy_guidance
from clinical_computer_use.domain.myle.topology import build_myle_topology_guidance
from clinical_computer_use.prompts import SYSTEM_PROMPT, build_myle_planning_prompt
from clinical_computer_use.schemas.task_contract import TaskContract


def build_contract_aware_planning_prompt(
    *,
    task_name: str,
    draft_only: bool,
    contract: TaskContract,
    run_state_summary: dict[str, object],
) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Current task: {task_name}\n"
        f"Draft-only mode: {draft_only}\n\n"
        f"{build_myle_topology_guidance()}\n\n"
        f"{build_myle_policy_guidance()}\n\n"
        "Operational rule: The compiled task contract is authoritative for execution planning. "
        "Do not override it with local heuristics from screenshots or nearby UI wording.\n\n"
        "Task contract JSON:\n"
        f"{json.dumps(contract.model_dump(), indent=2)}\n\n"
        "Run-state summary JSON:\n"
        f"{json.dumps(run_state_summary, indent=2)}\n\n"
        "Return a concise structured plan only. If requested behavior conflicts with contract constraints, "
        "surface that as uncertainty/review handoff."
    )


__all__ = ["SYSTEM_PROMPT", "build_myle_planning_prompt", "build_contract_aware_planning_prompt"]
