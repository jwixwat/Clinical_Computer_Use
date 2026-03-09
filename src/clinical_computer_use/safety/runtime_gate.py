"""Runtime action gate scaffold."""

from dataclasses import dataclass

from clinical_computer_use.safety.policy import PolicyConfig, evaluate_action


@dataclass(frozen=True)
class RuntimeGateResult:
    allowed: bool
    requires_approval: bool
    reason: str


def gate_action(action_name: str, policy: PolicyConfig) -> RuntimeGateResult:
    """Policy gate for runtime interception seam (parity behavior in phase 1)."""
    decision = evaluate_action(action_name, policy)
    return RuntimeGateResult(
        allowed=decision.allowed,
        requires_approval=decision.requires_approval,
        reason=decision.reason,
    )

