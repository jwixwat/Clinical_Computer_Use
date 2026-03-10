"""Observation prompt module with contract-aware builders."""

from __future__ import annotations

import json

from clinical_computer_use.domain.myle.policy_guidance import build_myle_policy_guidance
from clinical_computer_use.domain.myle.topology import build_myle_topology_guidance
from clinical_computer_use.prompts import build_myle_observation_prompt, build_myle_patient_bind_prompt
from clinical_computer_use.schemas.task_contract import TaskContract


def build_contract_aware_observation_prompt(
    *,
    contract: TaskContract,
    run_state_summary: dict[str, object],
    user_prompt: str,
) -> str:
    return (
        f"{build_myle_topology_guidance()}\n\n"
        f"{build_myle_policy_guidance()}\n\n"
        "You are observing a Myle screen in read-only mode. "
        "The task contract is authoritative.\n\n"
        f"User request (for context only): {user_prompt}\n\n"
        "Task contract JSON:\n"
        f"{json.dumps(contract.model_dump(), indent=2)}\n\n"
        "Run-state summary JSON:\n"
        f"{json.dumps(run_state_summary, indent=2)}\n\n"
        "Describe the screen and propose safe next actions that comply with contract constraints."
    )


def build_contract_aware_patient_bind_prompt(
    *,
    patient_query: str,
    contract: TaskContract,
    run_state_summary: dict[str, object],
) -> str:
    return (
        f"{build_myle_topology_guidance()}\n\n"
        f"{build_myle_policy_guidance()}\n\n"
        "You are assessing patient bind state from a screenshot. "
        "Confirm chart context against the contract patient target.\n\n"
        f"Patient query: {patient_query}\n\n"
        "Task contract JSON:\n"
        f"{json.dumps(contract.model_dump(), indent=2)}\n\n"
        "Run-state summary JSON:\n"
        f"{json.dumps(run_state_summary, indent=2)}"
    )


__all__ = [
    "build_myle_observation_prompt",
    "build_myle_patient_bind_prompt",
    "build_contract_aware_observation_prompt",
    "build_contract_aware_patient_bind_prompt",
]
