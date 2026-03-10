"""Verifier role implementation for completion gating."""

from __future__ import annotations

from dataclasses import dataclass

from clinical_computer_use.runtime.ledgers import RunLedgers, unresolved_higher_priority_candidates
from clinical_computer_use.schemas.contract_types import CompletionCriterion
from clinical_computer_use.schemas.task_contract import TaskContract


@dataclass
class VerificationResult:
    complete: bool
    reason: str
    missing_criteria: list[str]
    supporting_artifacts: list[str]
    unresolved_candidates: list[str]
    uncertainties: list[str]


def _artifact_class_match(contract: TaskContract, artifact_class_value: str) -> bool:
    required = {item.value for item in contract.required_artifact_classes}
    acceptable = {item.value for item in contract.acceptable_artifact_classes}
    disallowed = {item.value for item in contract.disallowed_artifact_classes}

    if artifact_class_value in disallowed:
        return False
    if required:
        return artifact_class_value in required
    if acceptable:
        return artifact_class_value in acceptable
    return artifact_class_value != "unknown"


def verify_completion_claim(
    *,
    contract: TaskContract,
    ledgers: RunLedgers,
    final_report: str,
) -> VerificationResult:
    missing: list[str] = []
    uncertainties: list[str] = []

    supporting_artifacts = [key for key, record in ledgers.artifact_registry.items() if record.opened_count > 0]
    if not supporting_artifacts:
        missing.append(CompletionCriterion.EVIDENCE_LINKED.value)

    class_match = False
    for key in supporting_artifacts:
        record = ledgers.artifact_registry[key]
        if _artifact_class_match(contract, record.provisional_class.value):
            class_match = True
            break
    if not class_match:
        missing.append(CompletionCriterion.ARTIFACT_CLASS_VERIFIED.value)

    if not final_report.strip():
        missing.append(CompletionCriterion.OBJECTIVE_ADDRESSED.value)

    unresolved = unresolved_higher_priority_candidates(ledgers, contract.preferred_surfaces)
    if unresolved:
        missing.append(CompletionCriterion.FALSIFICATION_PERFORMED.value)
        uncertainties.append("higher_probability_candidates_uninspected")

    if not ledgers.uncertainties and "uncertain" not in final_report.lower():
        # Allow this criterion only when there are no known uncertainties.
        pass

    complete = len(missing) == 0
    reason = "completion_verified" if complete else "completion_blocked_missing_verification_criteria"
    return VerificationResult(
        complete=complete,
        reason=reason,
        missing_criteria=missing,
        supporting_artifacts=supporting_artifacts,
        unresolved_candidates=unresolved,
        uncertainties=uncertainties,
    )
