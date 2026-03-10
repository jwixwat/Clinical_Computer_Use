from clinical_computer_use.agent.contracts import apply_correction, compile_task_contract
from clinical_computer_use.runtime.checkpoints import make_start_checkpoint
from clinical_computer_use.runtime.ledgers import build_empty_ledgers
from clinical_computer_use.runtime.run_state import (
    SessionContext,
    apply_correction_to_state,
    build_initial_run_state,
    load_run_state,
    save_run_state,
)
from clinical_computer_use.schemas.contract_types import ArtifactClass


def test_run_state_round_trip(monkeypatch, tmp_path) -> None:
    trace_root = (tmp_path / "traces").resolve()
    trace_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("clinical_computer_use.config.TRACE_DIR", trace_root)
    monkeypatch.setattr("clinical_computer_use.runtime.run_state.TRACE_DIR", trace_root)

    session = SessionContext(task_name="insurance_form_draft", user_prompt="Find form")
    contract = compile_task_contract("Find external form", patient_target="123").contract
    start_cp = make_start_checkpoint("start", ["search_documents"])
    state = build_initial_run_state(
        session=session,
        draft_only=True,
        contract=contract,
        ledgers=build_empty_ledgers(),
        start_checkpoint=start_cp,
    )
    save_run_state(session, state)

    loaded = load_run_state(session.session_id)
    assert loaded.session_id == session.session_id
    assert loaded.task_contract.patient_target == "123"
    assert loaded.bound_patient_context.intended_patient_target == "123"
    assert loaded.version_bundle.model
    assert loaded.version_bundle.git_commit
    assert loaded.lifecycle_state.value == "active"
    assert loaded.autonomy_state.consecutive_t0 == 0

    correction = apply_correction(loaded.task_contract, "Not a note")
    apply_correction_to_state(loaded, correction.delta, correction.contract, start_cp)
    save_run_state(session, loaded)

    loaded2 = load_run_state(session.session_id)
    assert len(loaded2.contract_history) == 1
    assert ArtifactClass.CHART_NOTE in loaded2.task_contract.disallowed_artifact_classes
    assert (trace_root / session.session_id / "version_bundle.json").exists()
