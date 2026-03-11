from clinical_computer_use.runtime.surfaces import (
    ChartSurfaceState,
    coarse_surface,
    resolve_surface_from_url,
    resolve_surface_state,
    restorable_surface_for_resume,
)
from clinical_computer_use.schemas.contract_types import SurfaceType


def test_url_only_calendar_resolution() -> None:
    state = resolve_surface_from_url("https://chmg.medfarsolutions.com/html5/calendar")
    assert state.surface_type == SurfaceType.CALENDAR
    assert not state.patient_bounded


def test_url_only_external_document_viewer_resolution() -> None:
    state = resolve_surface_from_url(
        "https://chmg.medfarsolutions.com/html5/api/medicalDocuments/downloadFile/doc/file.pdf?sessionId=abc"
    )
    assert state.surface_type == SurfaceType.DOCUMENT_VIEWER_EXTERNAL
    assert state.is_viewer_like
    assert not state.patient_bounded


def test_medical_summary_resolution_on_patients_route() -> None:
    state = resolve_surface_state(
        url="https://chmg.medfarsolutions.com/html5/patients",
        selector_hits={
            "patient_banner": True,
            "chart_right_rail": True,
            "patient_medicalsummary_tab": True,
            "left_note_search": True,
            "summary_label": True,
        },
        headings=["Active Problems"],
        visible_text=["FOLLOW-UPS"],
    )
    assert state.surface_type == SurfaceType.MEDICAL_SUMMARY
    assert state.patient_bounded
    assert state.chart_bounded


def test_medical_note_resolution_beats_summary_when_note_blocks_visible() -> None:
    state = resolve_surface_state(
        url="https://chmg.medfarsolutions.com/html5/patients",
        selector_hits={
            "patient_banner": True,
            "chart_right_rail": True,
            "patient_medicalnote_tab": True,
            "left_note_search": True,
            "note_block": True,
        },
        headings=["PROGRESS NOTE"],
        visible_text=["ASSESSMENT", "PLAN"],
    )
    assert state.surface_type == SurfaceType.MEDICAL_NOTE
    assert state.is_draft_like


def test_result_review_resolution_beats_results_list() -> None:
    state = resolve_surface_state(
        url="https://chmg.medfarsolutions.com/html5/patients",
        selector_hits={
            "patient_banner": True,
            "patient_results_tab": True,
            "results_row": True,
            "result_review_back": True,
            "result_review_notes_panel": True,
            "result_review_bottom_actions": True,
        },
        headings=["FULL RESULTS"],
        visible_text=["Back to Results"],
    )
    assert state.surface_type == SurfaceType.RESULT_REVIEW
    assert state.patient_bounded
    assert not state.is_read_only_like


def test_result_detail_modal_resolution() -> None:
    state = resolve_surface_state(
        url="https://chmg.medfarsolutions.com/html5/patients",
        selector_hits={"patient_banner": True, "result_detail_modal": True},
        headings=["Result Details"],
        visible_text=["Submit"],
    )
    assert state.surface_type == SurfaceType.RESULT_DETAIL_MODAL


def test_coarse_and_restorable_surface_aliases() -> None:
    assert coarse_surface(SurfaceType.PATIENT_DOCUMENTS) == SurfaceType.DOCUMENTS
    assert coarse_surface(SurfaceType.RESULT_REVIEW) == SurfaceType.RESULTS
    assert restorable_surface_for_resume(SurfaceType.DOCUMENT_VIEWER_EXTERNAL) == SurfaceType.PATIENT_DOCUMENTS
    assert restorable_surface_for_resume(SurfaceType.RESULT_DETAIL_MODAL) == SurfaceType.PATIENT_RESULTS


def test_surface_state_round_trip() -> None:
    original = ChartSurfaceState(
        surface_type=SurfaceType.MEDICAL_SUMMARY,
        surface_confidence=0.95,
        active_url="https://chmg.medfarsolutions.com/html5/patients",
        chart_bounded=True,
        patient_bounded=True,
        patient_context_visible=True,
        surface_heading="Medical Summary",
        surface_anchors=["patient_banner", "summary_label"],
        allowed_transitions=[SurfaceType.MEDICAL_NOTE, SurfaceType.PATIENT_RESULTS],
        is_read_only_like=True,
        is_draft_like=False,
        is_viewer_like=False,
        stability_flags=["default_chart_surface"],
        evidence=["summary_cards_visible"],
    )
    restored = ChartSurfaceState.from_dict(original.to_dict())
    assert restored.surface_type == original.surface_type
    assert restored.allowed_transitions == original.allowed_transitions
    assert restored.surface_anchors == original.surface_anchors
