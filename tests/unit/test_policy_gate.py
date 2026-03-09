from clinical_computer_use.domain.myle.policy_guidance import build_myle_policy_config
from clinical_computer_use.safety.runtime_gate import gate_action


def test_gate_allows_read_like_action() -> None:
    policy = build_myle_policy_config(draft_only=True)
    result = gate_action("open_documents", policy)
    assert result.allowed is True
    assert result.requires_approval is False


def test_gate_blocks_submit() -> None:
    policy = build_myle_policy_config(draft_only=True)
    result = gate_action("submit", policy)
    assert result.allowed is False
    assert result.requires_approval is True

