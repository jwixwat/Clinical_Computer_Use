"""Agent reasoning roles."""

from clinical_computer_use.agent.reasoning.intent import IntentCheckResult, check_decision_against_contract, infer_artifact_class
from clinical_computer_use.agent.reasoning.verifier import VerificationResult, verify_completion_claim

__all__ = [
    "IntentCheckResult",
    "check_decision_against_contract",
    "infer_artifact_class",
    "VerificationResult",
    "verify_completion_claim",
]
