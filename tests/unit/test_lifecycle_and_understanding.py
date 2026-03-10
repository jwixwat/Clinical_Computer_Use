from clinical_computer_use.agent.contracts import compile_task_contract
from clinical_computer_use.agent.flows.run_state_flow import archive_run, stop_run
from clinical_computer_use.runtime.checkpoints import make_start_checkpoint
from clinical_computer_use.runtime.ledgers import build_empty_ledgers
from clinical_computer_use.runtime.run_state import SessionContext, build_initial_run_state, load_run_state, save_run_state
from clinical_computer_use.runtime.understanding import build_operational_understanding_block


def test_understanding_block_contains_required_sections() -> None:
    session = SessionContext(task_name="insurance_form_draft", user_prompt="Find external form")
    contract = compile_task_contract("Find external form, not a chart note", patient_target="p1").contract
    state = build_initial_run_state(
        session=session,
        draft_only=True,
        contract=contract,
        ledgers=build_empty_ledgers(),
        start_checkpoint=make_start_checkpoint("start"),
    )
    block = build_operational_understanding_block(state, next_safest_actions=["continue_search"])
    assert "objective_type" in block
    assert "explicit_non_goals" in block
    assert "next_safest_actions" in block


def test_stop_then_archive_lifecycle(monkeypatch, tmp_path) -> None:
    trace_root = (tmp_path / "traces").resolve()
    trace_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("clinical_computer_use.config.TRACE_DIR", trace_root)
    monkeypatch.setattr("clinical_computer_use.runtime.run_state.TRACE_DIR", trace_root)
    monkeypatch.setattr("clinical_computer_use.session.TRACE_DIR", trace_root)

    session = SessionContext(task_name="insurance_form_draft", user_prompt="Find form")
    contract = compile_task_contract("Find external form", patient_target="123").contract
    state = build_initial_run_state(
        session=session,
        draft_only=True,
        contract=contract,
        ledgers=build_empty_ledgers(),
        start_checkpoint=make_start_checkpoint("start"),
    )
    save_run_state(session, state)

    stop_run(session.session_id, reason="test_stop")
    stopped = load_run_state(session.session_id)
    assert stopped.lifecycle_state.value == "stopped"

    archive_run(session.session_id, reason="test_archive")
    archived = load_run_state(session.session_id)
    assert archived.lifecycle_state.value == "archived"

