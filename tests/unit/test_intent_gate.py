from clinical_computer_use.agent.contracts import compile_task_contract
from clinical_computer_use.agent.reasoning.intent import check_decision_against_contract
from clinical_computer_use.runtime.ledgers import build_empty_ledgers, infer_surface_from_url, mark_artifact_opened, upsert_artifact_from_candidate
from clinical_computer_use.schemas.browser_action import BrowserActionDecision


def _decision(action_type: str, target_id: str | None = None, final_report: str | None = None) -> BrowserActionDecision:
    return BrowserActionDecision(
        action_type=action_type,
        target_id=target_id,
        rationale="test",
        expected_outcome="test",
        final_report=final_report,
    )


def test_intent_blocks_disallowed_artifact_class() -> None:
    contract = compile_task_contract("Find external form, not a note").contract
    ledgers = build_empty_ledgers()
    candidates = [{"agent_id": "a1", "tag": "tr", "type": "", "label": "Progress note 2026-02-01"}]

    result = check_decision_against_contract(
        _decision("click", target_id="a1"),
        contract=contract,
        ledgers=ledgers,
        candidates=candidates,
    )

    assert not result.allowed
    assert "disallowed_artifact_class" in result.reason


def test_intent_blocks_finish_without_evidence() -> None:
    contract = compile_task_contract("Find external form").contract
    ledgers = build_empty_ledgers()
    result = check_decision_against_contract(
        _decision("finish", final_report="done"),
        contract=contract,
        ledgers=ledgers,
        candidates=[],
    )
    assert not result.allowed


def test_intent_allows_finish_with_opened_candidate() -> None:
    contract = compile_task_contract("Find external form").contract
    ledgers = build_empty_ledgers()
    candidate = {"agent_id": "a2", "tag": "tr", "type": "", "label": "External document firearms form"}
    artifact = upsert_artifact_from_candidate(
        ledgers,
        candidate=candidate,
        source_surface=infer_surface_from_url("https://example.com/documents"),
        step=1,
    )
    mark_artifact_opened(ledgers, artifact.candidate_key, step=1)

    result = check_decision_against_contract(
        _decision("finish", final_report="done"),
        contract=contract,
        ledgers=ledgers,
        candidates=[],
    )
    assert result.allowed
