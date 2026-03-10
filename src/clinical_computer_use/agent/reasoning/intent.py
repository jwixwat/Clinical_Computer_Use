"""Intent-level checks that make run-state and contract causally binding."""

from __future__ import annotations

from dataclasses import dataclass

from clinical_computer_use.runtime.ledgers import RunLedgers, candidate_key
from clinical_computer_use.schemas.browser_action import BrowserActionDecision
from clinical_computer_use.schemas.contract_types import ArtifactClass
from clinical_computer_use.schemas.task_contract import TaskContract


_ARTIFACT_CLASS_HINTS: dict[ArtifactClass, tuple[str, ...]] = {
    ArtifactClass.CHART_NOTE: ("note", "progress note", "soap", "encounter"),
    ArtifactClass.EXTERNAL_DOCUMENT: ("document", "external", "attachment", "outside"),
    ArtifactClass.PDF_FORM: ("pdf", "form"),
    ArtifactClass.SCANNED_FORM: ("scan", "scanned", "image"),
    ArtifactClass.RESULT_ARTIFACT: ("result", "lab", "panel"),
    ArtifactClass.CONSULT_LETTER: ("consult", "referral"),
    ArtifactClass.BUILT_IN_FORM: ("template", "built-in", "builtin"),
}


@dataclass(frozen=True)
class IntentCheckResult:
    allowed: bool
    reason: str
    inferred_artifact_class: ArtifactClass | None = None
    candidate_key: str | None = None


def infer_artifact_class(label: str) -> ArtifactClass | None:
    text = (label or "").lower()
    for artifact_class, hints in _ARTIFACT_CLASS_HINTS.items():
        if any(hint in text for hint in hints):
            return artifact_class
    return None


def check_decision_against_contract(
    decision: BrowserActionDecision,
    *,
    contract: TaskContract,
    ledgers: RunLedgers,
    candidates: list[dict[str, str]],
) -> IntentCheckResult:
    if decision.action_type in {"click", "type"}:
        if not decision.target_id:
            return IntentCheckResult(allowed=False, reason="missing_target_id_for_interactive_action")

        candidate = next((item for item in candidates if item.get("agent_id") == decision.target_id), None)
        if candidate is None:
            return IntentCheckResult(allowed=False, reason="target_not_visible_in_current_candidate_set")

        key = candidate_key(candidate)
        existing = ledgers.artifact_registry.get(key)
        if existing is not None and existing.rejected_reason:
            return IntentCheckResult(
                allowed=False,
                reason="candidate_previously_rejected_under_current_contract",
                candidate_key=key,
            )

        inferred = infer_artifact_class(str(candidate.get("label", "")))
        if inferred and inferred in set(contract.disallowed_artifact_classes):
            return IntentCheckResult(
                allowed=False,
                reason=f"candidate_appears_to_be_disallowed_artifact_class:{inferred.value}",
                inferred_artifact_class=inferred,
                candidate_key=key,
            )

        return IntentCheckResult(
            allowed=True,
            reason="candidate_complies_with_contract_constraints",
            inferred_artifact_class=inferred,
            candidate_key=key,
        )

    if decision.action_type == "finish":
        has_evidence = bool(ledgers.evidence_records or ledgers.opened_candidates)
        if not has_evidence:
            return IntentCheckResult(
                allowed=False,
                reason="finish_blocked_no_evidence_or_opened_candidate_recorded",
            )
        return IntentCheckResult(allowed=True, reason="finish_claim_requires_verifier_gate")

    return IntentCheckResult(allowed=True, reason="non_interactive_action_allowed")
