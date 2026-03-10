from clinical_computer_use.agent.contracts import compile_task_contract
from clinical_computer_use.agent.flows.run_state_flow import apply_run_correction
from clinical_computer_use.runtime.checkpoints import make_start_checkpoint
from clinical_computer_use.runtime.ledgers import ArtifactRecord, SurfaceType, build_empty_ledgers
from clinical_computer_use.runtime.run_state import SessionContext, build_initial_run_state, load_run_state, save_run_state


def test_apply_correction_marks_last_candidate_rejected(monkeypatch, tmp_path) -> None:
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
        start_checkpoint=make_start_checkpoint("start", ["search_documents"]),
    )
    key = "tr||progress note"
    state.ledgers.last_candidate_key = key
    state.ledgers.artifact_registry[key] = ArtifactRecord(candidate_key=key, source_surface=SurfaceType.DOCUMENTS, label="Progress note")
    save_run_state(session, state)

    apply_run_correction(session.session_id, "Not that one. Not a note.")

    updated = load_run_state(session.session_id)
    assert key in updated.ledgers.rejected_candidates
