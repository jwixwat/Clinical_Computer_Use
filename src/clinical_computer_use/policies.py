"""
Policy definitions for approved domains and blocked actions.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import ALLOWED_DOMAINS, MAX_AGENT_STEPS, MAX_RUN_MINUTES


@dataclass
class PolicyConfig:
    allowed_domains: tuple[str, ...] = ALLOWED_DOMAINS
    blocked_actions: tuple[str, ...] = (
        "submit",
        "approve",
        "complete",
        "send",
        "sign",
        "fax",
        "bill",
    )
    approval_required_actions: tuple[str, ...] = (
        "submit",
        "approve",
        "complete",
        "send",
        "sign",
        "fax",
        "bill",
    )
    max_steps: int = MAX_AGENT_STEPS
    max_run_minutes: int = MAX_RUN_MINUTES
    draft_only: bool = True
    require_source_citations: bool = True
    blocked_keywords: tuple[str, ...] = (
        "submit",
        "approve",
        "complete",
        "send",
        "sign",
        "fax",
        "bill",
    )


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    requires_approval: bool = False


def evaluate_action(action_name: str, policy: PolicyConfig) -> PolicyDecision:
    normalized = action_name.strip().lower()
    if normalized in policy.blocked_actions:
        return PolicyDecision(
            allowed=False,
            reason=f"Blocked action: {normalized}",
            requires_approval=normalized in policy.approval_required_actions,
        )
    for keyword in policy.blocked_keywords:
        if keyword in normalized:
            return PolicyDecision(
                allowed=False,
                reason=f"Blocked keyword in action: {keyword}",
                requires_approval=keyword in policy.approval_required_actions or normalized in policy.approval_required_actions,
            )
    return PolicyDecision(allowed=True, reason="Allowed")
