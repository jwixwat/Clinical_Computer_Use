"""Runtime policy-plane context, distinct from task contract semantics."""

from __future__ import annotations

from dataclasses import dataclass

from clinical_computer_use.schemas.contract_types import RiskTier
from clinical_computer_use.schemas.correction_delta import RuntimeDirectiveDelta


@dataclass
class PolicyContext:
    require_review_at_or_above: RiskTier = RiskTier.TIER3

    def to_dict(self) -> dict[str, object]:
        return {"require_review_at_or_above": self.require_review_at_or_above.value}


def build_policy_context(runtime_directives: list[RuntimeDirectiveDelta]) -> PolicyContext:
    threshold = RiskTier.TIER3
    for directive in runtime_directives:
        if directive.directive.value == "require_review_at_or_above" and directive.value:
            try:
                threshold = RiskTier(directive.value)
            except ValueError:
                continue
    return PolicyContext(require_review_at_or_above=threshold)
