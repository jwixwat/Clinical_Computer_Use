from clinical_computer_use.agent.contracts import compile_task_contract
from clinical_computer_use.runtime.checkpoints import make_start_checkpoint
from clinical_computer_use.runtime.ledgers import build_empty_ledgers
from clinical_computer_use.runtime.run_state import SessionContext, RunState, build_initial_run_state
from clinical_computer_use.runtime.surfaces import ChartSurfaceState
from clinical_computer_use.schemas.contract_types import SurfaceType


def test_run_state_serializes_latest_surface_state() -> None:
    session = SessionContext(task_name="insurance_form_draft", user_prompt="Find form")
    contract = compile_task_contract("Find external form", patient_target="123").contract
    state = build_initial_run_state(
        session=session,
        draft_only=True,
        contract=contract,
        ledgers=build_empty_ledgers(),
        start_checkpoint=make_start_checkpoint("start", ["search_documents"]),
    )
    state.latest_surface_state = ChartSurfaceState(
        surface_type=SurfaceType.PATIENT_DOCUMENTS,
        surface_confidence=0.94,
        active_url="https://chmg.medfarsolutions.com/html5/patients",
        chart_bounded=True,
        patient_bounded=True,
        patient_context_visible=True,
        surface_heading="All Documents",
        surface_anchors=["patient_documents_tab", "documents_row"],
        allowed_transitions=[SurfaceType.DOCUMENT_VIEWER_EXTERNAL],
        is_read_only_like=True,
        is_draft_like=False,
        is_viewer_like=False,
        stability_flags=["row_click_opens_external_viewer"],
        evidence=["documents_table"],
    )

    restored = RunState.from_dict(state.to_dict())
    assert restored.latest_surface_state is not None
    assert restored.latest_surface_state.surface_type == SurfaceType.PATIENT_DOCUMENTS
    assert restored.latest_surface_state.allowed_transitions == [SurfaceType.DOCUMENT_VIEWER_EXTERNAL]
