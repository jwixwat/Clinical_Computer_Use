"""Deterministic chart-surface modeling for N2.0 runtime control."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from clinical_computer_use.schemas.contract_types import SurfaceType


@dataclass(frozen=True)
class SurfaceDefinition:
    surface_type: SurfaceType
    chart_bounded: bool
    patient_bounded: bool
    read_only_like: bool
    draft_like: bool
    viewer_like: bool
    allowed_transitions: tuple[SurfaceType, ...] = ()


SURFACE_DEFINITIONS: dict[SurfaceType, SurfaceDefinition] = {
    SurfaceType.CALENDAR: SurfaceDefinition(
        surface_type=SurfaceType.CALENDAR,
        chart_bounded=False,
        patient_bounded=False,
        read_only_like=False,
        draft_like=False,
        viewer_like=False,
        allowed_transitions=(SurfaceType.CHART_HOME,),
    ),
    SurfaceType.CHART_HOME: SurfaceDefinition(
        surface_type=SurfaceType.CHART_HOME,
        chart_bounded=True,
        patient_bounded=True,
        read_only_like=True,
        draft_like=False,
        viewer_like=False,
        allowed_transitions=(
            SurfaceType.MEDICAL_SUMMARY,
            SurfaceType.MEDICAL_NOTE,
            SurfaceType.PATIENT_DOCUMENTS,
            SurfaceType.PATIENT_RESULTS,
            SurfaceType.PATIENT_MEDICATION,
        ),
    ),
    SurfaceType.MEDICAL_SUMMARY: SurfaceDefinition(
        surface_type=SurfaceType.MEDICAL_SUMMARY,
        chart_bounded=True,
        patient_bounded=True,
        read_only_like=True,
        draft_like=False,
        viewer_like=False,
        allowed_transitions=(
            SurfaceType.MEDICAL_NOTE,
            SurfaceType.PATIENT_DOCUMENTS,
            SurfaceType.PATIENT_RESULTS,
            SurfaceType.PATIENT_MEDICATION,
        ),
    ),
    SurfaceType.MEDICAL_NOTE: SurfaceDefinition(
        surface_type=SurfaceType.MEDICAL_NOTE,
        chart_bounded=True,
        patient_bounded=True,
        read_only_like=False,
        draft_like=True,
        viewer_like=False,
        allowed_transitions=(
            SurfaceType.MEDICAL_SUMMARY,
            SurfaceType.PATIENT_DOCUMENTS,
            SurfaceType.PATIENT_RESULTS,
        ),
    ),
    SurfaceType.DOCUMENTS: SurfaceDefinition(
        surface_type=SurfaceType.DOCUMENTS,
        chart_bounded=False,
        patient_bounded=False,
        read_only_like=True,
        draft_like=False,
        viewer_like=False,
    ),
    SurfaceType.PATIENT_DOCUMENTS: SurfaceDefinition(
        surface_type=SurfaceType.PATIENT_DOCUMENTS,
        chart_bounded=True,
        patient_bounded=True,
        read_only_like=True,
        draft_like=False,
        viewer_like=False,
        allowed_transitions=(SurfaceType.DOCUMENT_VIEWER_EXTERNAL,),
    ),
    SurfaceType.DOCUMENT_VIEWER_EXTERNAL: SurfaceDefinition(
        surface_type=SurfaceType.DOCUMENT_VIEWER_EXTERNAL,
        chart_bounded=False,
        patient_bounded=False,
        read_only_like=True,
        draft_like=False,
        viewer_like=True,
    ),
    SurfaceType.RESULTS: SurfaceDefinition(
        surface_type=SurfaceType.RESULTS,
        chart_bounded=False,
        patient_bounded=False,
        read_only_like=True,
        draft_like=False,
        viewer_like=False,
    ),
    SurfaceType.PATIENT_RESULTS: SurfaceDefinition(
        surface_type=SurfaceType.PATIENT_RESULTS,
        chart_bounded=True,
        patient_bounded=True,
        read_only_like=True,
        draft_like=False,
        viewer_like=False,
        allowed_transitions=(SurfaceType.RESULT_REVIEW, SurfaceType.RESULT_DETAIL_MODAL),
    ),
    SurfaceType.RESULT_REVIEW: SurfaceDefinition(
        surface_type=SurfaceType.RESULT_REVIEW,
        chart_bounded=True,
        patient_bounded=True,
        read_only_like=False,
        draft_like=True,
        viewer_like=False,
        allowed_transitions=(
            SurfaceType.PATIENT_RESULTS,
            SurfaceType.RESULT_DETAIL_MODAL,
            SurfaceType.DOCUMENT_VIEWER_EXTERNAL,
        ),
    ),
    SurfaceType.RESULT_DETAIL_MODAL: SurfaceDefinition(
        surface_type=SurfaceType.RESULT_DETAIL_MODAL,
        chart_bounded=True,
        patient_bounded=True,
        read_only_like=False,
        draft_like=True,
        viewer_like=False,
        allowed_transitions=(SurfaceType.PATIENT_RESULTS, SurfaceType.RESULT_REVIEW),
    ),
    SurfaceType.PATIENT_MEDICATION: SurfaceDefinition(
        surface_type=SurfaceType.PATIENT_MEDICATION,
        chart_bounded=True,
        patient_bounded=True,
        read_only_like=False,
        draft_like=True,
        viewer_like=False,
        allowed_transitions=(SurfaceType.MEDICAL_SUMMARY,),
    ),
    SurfaceType.FORMS: SurfaceDefinition(
        surface_type=SurfaceType.FORMS,
        chart_bounded=False,
        patient_bounded=False,
        read_only_like=True,
        draft_like=False,
        viewer_like=False,
    ),
    SurfaceType.VIEWER: SurfaceDefinition(
        surface_type=SurfaceType.VIEWER,
        chart_bounded=False,
        patient_bounded=False,
        read_only_like=True,
        draft_like=False,
        viewer_like=True,
    ),
    SurfaceType.UNKNOWN: SurfaceDefinition(
        surface_type=SurfaceType.UNKNOWN,
        chart_bounded=False,
        patient_bounded=False,
        read_only_like=False,
        draft_like=False,
        viewer_like=False,
    ),
}


@dataclass
class ChartSurfaceState:
    surface_type: SurfaceType
    surface_confidence: float
    active_url: str
    chart_bounded: bool
    patient_bounded: bool
    patient_context_visible: bool
    patient_context_matches_intended: bool | None = None
    surface_heading: str = ""
    surface_anchors: list[str] = field(default_factory=list)
    allowed_transitions: list[SurfaceType] = field(default_factory=list)
    is_read_only_like: bool = False
    is_draft_like: bool = False
    is_viewer_like: bool = False
    stability_flags: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_type": self.surface_type.value,
            "surface_confidence": self.surface_confidence,
            "active_url": self.active_url,
            "chart_bounded": self.chart_bounded,
            "patient_bounded": self.patient_bounded,
            "patient_context_visible": self.patient_context_visible,
            "patient_context_matches_intended": self.patient_context_matches_intended,
            "surface_heading": self.surface_heading,
            "surface_anchors": list(self.surface_anchors),
            "allowed_transitions": [surface.value for surface in self.allowed_transitions],
            "is_read_only_like": self.is_read_only_like,
            "is_draft_like": self.is_draft_like,
            "is_viewer_like": self.is_viewer_like,
            "stability_flags": list(self.stability_flags),
            "evidence": list(self.evidence),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChartSurfaceState":
        try:
            surface_type = SurfaceType(str(payload.get("surface_type", SurfaceType.UNKNOWN.value)))
        except ValueError:
            surface_type = SurfaceType.UNKNOWN
        transitions: list[SurfaceType] = []
        raw_transitions = payload.get("allowed_transitions", [])
        if isinstance(raw_transitions, list):
            for item in raw_transitions:
                try:
                    transitions.append(SurfaceType(str(item)))
                except ValueError:
                    continue
        return cls(
            surface_type=surface_type,
            surface_confidence=float(payload.get("surface_confidence", 0.0) or 0.0),
            active_url=str(payload.get("active_url", "")),
            chart_bounded=bool(payload.get("chart_bounded", False)),
            patient_bounded=bool(payload.get("patient_bounded", False)),
            patient_context_visible=bool(payload.get("patient_context_visible", False)),
            patient_context_matches_intended=(
                bool(payload["patient_context_matches_intended"])
                if payload.get("patient_context_matches_intended") is not None
                else None
            ),
            surface_heading=str(payload.get("surface_heading", "")),
            surface_anchors=[str(item) for item in payload.get("surface_anchors", []) or []],
            allowed_transitions=transitions,
            is_read_only_like=bool(payload.get("is_read_only_like", False)),
            is_draft_like=bool(payload.get("is_draft_like", False)),
            is_viewer_like=bool(payload.get("is_viewer_like", False)),
            stability_flags=[str(item) for item in payload.get("stability_flags", []) or []],
            evidence=[str(item) for item in payload.get("evidence", []) or []],
        )


def coarse_surface(surface: SurfaceType) -> SurfaceType:
    alias_map = {
        SurfaceType.MEDICAL_SUMMARY: SurfaceType.CHART_HOME,
        SurfaceType.MEDICAL_NOTE: SurfaceType.CHART_HOME,
        SurfaceType.PATIENT_DOCUMENTS: SurfaceType.DOCUMENTS,
        SurfaceType.DOCUMENT_VIEWER_EXTERNAL: SurfaceType.VIEWER,
        SurfaceType.PATIENT_RESULTS: SurfaceType.RESULTS,
        SurfaceType.RESULT_REVIEW: SurfaceType.RESULTS,
        SurfaceType.RESULT_DETAIL_MODAL: SurfaceType.RESULTS,
        SurfaceType.PATIENT_MEDICATION: SurfaceType.CHART_HOME,
    }
    return alias_map.get(surface, surface)


def restorable_surface_for_resume(surface: SurfaceType) -> SurfaceType:
    restore_map = {
        SurfaceType.MEDICAL_SUMMARY: SurfaceType.MEDICAL_SUMMARY,
        SurfaceType.MEDICAL_NOTE: SurfaceType.MEDICAL_NOTE,
        SurfaceType.PATIENT_DOCUMENTS: SurfaceType.PATIENT_DOCUMENTS,
        SurfaceType.DOCUMENT_VIEWER_EXTERNAL: SurfaceType.PATIENT_DOCUMENTS,
        SurfaceType.PATIENT_RESULTS: SurfaceType.PATIENT_RESULTS,
        SurfaceType.RESULT_REVIEW: SurfaceType.PATIENT_RESULTS,
        SurfaceType.RESULT_DETAIL_MODAL: SurfaceType.PATIENT_RESULTS,
        SurfaceType.PATIENT_MEDICATION: SurfaceType.PATIENT_MEDICATION,
    }
    return restore_map.get(surface, coarse_surface(surface))


def _build_surface_state(
    surface_type: SurfaceType,
    *,
    active_url: str,
    confidence: float,
    anchors: list[str],
    evidence: list[str],
    heading: str = "",
    stability_flags: list[str] | None = None,
    patient_context_visible: bool = False,
) -> ChartSurfaceState:
    definition = SURFACE_DEFINITIONS.get(surface_type, SURFACE_DEFINITIONS[SurfaceType.UNKNOWN])
    return ChartSurfaceState(
        surface_type=surface_type,
        surface_confidence=confidence,
        active_url=active_url,
        chart_bounded=definition.chart_bounded,
        patient_bounded=definition.patient_bounded,
        patient_context_visible=patient_context_visible,
        surface_heading=heading,
        surface_anchors=anchors,
        allowed_transitions=list(definition.allowed_transitions),
        is_read_only_like=definition.read_only_like,
        is_draft_like=definition.draft_like,
        is_viewer_like=definition.viewer_like,
        stability_flags=stability_flags or [],
        evidence=evidence,
    )


def resolve_surface_state(
    *,
    url: str,
    selector_hits: dict[str, bool] | None = None,
    headings: list[str] | None = None,
    visible_text: list[str] | None = None,
) -> ChartSurfaceState:
    selector_hits = selector_hits or {}
    headings = headings or []
    visible_text = visible_text or []
    normalized_url = (url or "").lower()
    path = normalized_url
    heading = headings[0] if headings else ""
    patient_context_visible = bool(selector_hits.get("patient_banner"))

    def _anchors(*names: str) -> list[str]:
        return [name for name in names if selector_hits.get(name)]

    def _has_text(fragment: str) -> bool:
        lowered = fragment.lower()
        return any(lowered in value.lower() for value in headings + visible_text)

    if "/html5/api/medicaldocuments/downloadfile/" in path:
        return _build_surface_state(
            SurfaceType.DOCUMENT_VIEWER_EXTERNAL,
            active_url=url,
            confidence=0.99,
            anchors=_anchors("document_viewer_plugin"),
            evidence=["downloadFile_url", "external_pdf_viewer"],
            heading=heading,
            stability_flags=["external_viewer", "read_only"],
            patient_context_visible=False,
        )

    if "/calendar" in path or selector_hits.get("calendar_grid") or selector_hits.get("calendar_search"):
        return _build_surface_state(
            SurfaceType.CALENDAR,
            active_url=url,
            confidence=0.97,
            anchors=_anchors("calendar_grid", "calendar_search", "calendar_nav"),
            evidence=["calendar_route_or_schedule_grid"],
            heading=heading,
            stability_flags=["global_workspace"],
            patient_context_visible=False,
        )

    if "/documents" in path and not patient_context_visible:
        return _build_surface_state(
            SurfaceType.DOCUMENTS,
            active_url=url,
            confidence=0.9,
            anchors=_anchors("system_documents_nav"),
            evidence=["system_documents_route"],
            heading=heading,
            patient_context_visible=False,
        )

    if "/results" in path and not patient_context_visible:
        return _build_surface_state(
            SurfaceType.RESULTS,
            active_url=url,
            confidence=0.9,
            anchors=_anchors("system_results_nav"),
            evidence=["system_results_route"],
            heading=heading,
            patient_context_visible=False,
        )

    if "/forms" in path and not patient_context_visible:
        return _build_surface_state(
            SurfaceType.FORMS,
            active_url=url,
            confidence=0.85,
            anchors=[],
            evidence=["system_forms_route"],
            heading=heading,
            patient_context_visible=False,
        )

    if "/html5/patients" in path or patient_context_visible or selector_hits.get("chart_right_rail"):
        if selector_hits.get("result_detail_modal"):
            return _build_surface_state(
                SurfaceType.RESULT_DETAIL_MODAL,
                active_url=url,
                confidence=0.95,
                anchors=_anchors("result_detail_modal"),
                evidence=["result_details_modal_visible"],
                heading=heading or "Result Details",
                stability_flags=["workflow_modal", "avoid_interaction"],
                patient_context_visible=patient_context_visible,
            )

        if selector_hits.get("result_review_back") or selector_hits.get("result_review_notes_panel"):
            return _build_surface_state(
                SurfaceType.RESULT_REVIEW,
                active_url=url,
                confidence=0.96,
                anchors=_anchors(
                    "result_review_back",
                    "result_review_full_results",
                    "result_review_notes_panel",
                    "result_review_bottom_actions",
                ),
                evidence=["result_row_opened", "back_to_results_visible"],
                heading=heading or "Result Review",
                stability_flags=["mixed_risk", "center_read_zone_only"],
                patient_context_visible=patient_context_visible,
            )

        if selector_hits.get("patient_documents_tab") and (
            selector_hits.get("documents_row") or _has_text("all documents")
        ):
            return _build_surface_state(
                SurfaceType.PATIENT_DOCUMENTS,
                active_url=url,
                confidence=0.95,
                anchors=_anchors("patient_documents_tab", "documents_row", "documents_categories"),
                evidence=["patient_documents_tab", "documents_table"],
                heading=heading or "All Documents",
                stability_flags=["row_click_opens_external_viewer"],
                patient_context_visible=patient_context_visible,
            )

        if selector_hits.get("patient_results_tab") and selector_hits.get("results_row"):
            return _build_surface_state(
                SurfaceType.PATIENT_RESULTS,
                active_url=url,
                confidence=0.95,
                anchors=_anchors("patient_results_tab", "results_row"),
                evidence=["patient_results_tab", "results_table"],
                heading=heading or "Results",
                stability_flags=["row_click_opens_result_review", "plus_opens_modal"],
                patient_context_visible=patient_context_visible,
            )

        if selector_hits.get("patient_medication_tab") and (
            selector_hits.get("medication_heading") or _has_text("medications")
        ):
            return _build_surface_state(
                SurfaceType.PATIENT_MEDICATION,
                active_url=url,
                confidence=0.94,
                anchors=_anchors("patient_medication_tab", "medication_heading"),
                evidence=["patient_medication_tab", "medication_table_layout"],
                heading=heading or "Medications",
                stability_flags=["mixed_risk", "add_medication_forbidden"],
                patient_context_visible=patient_context_visible,
            )

        if selector_hits.get("patient_medicalnote_tab") and selector_hits.get("note_block"):
            return _build_surface_state(
                SurfaceType.MEDICAL_NOTE,
                active_url=url,
                confidence=0.96,
                anchors=_anchors("patient_medicalnote_tab", "note_block", "left_note_search"),
                evidence=["note_block_layout", "note_sections_visible"],
                heading=heading or "Medical Note",
                stability_flags=["view_or_edit_note_surface"],
                patient_context_visible=patient_context_visible,
            )

        if selector_hits.get("patient_medicalsummary_tab") and (
            selector_hits.get("summary_label") or selector_hits.get("left_note_search") or _has_text("follow-ups")
        ):
            return _build_surface_state(
                SurfaceType.MEDICAL_SUMMARY,
                active_url=url,
                confidence=0.95,
                anchors=_anchors("patient_medicalsummary_tab", "summary_label", "left_note_search"),
                evidence=["summary_cards_visible", "chart_landing_state"],
                heading=heading or "Medical Summary",
                stability_flags=["default_chart_surface"],
                patient_context_visible=patient_context_visible,
            )

        if patient_context_visible:
            return _build_surface_state(
                SurfaceType.CHART_HOME,
                active_url=url,
                confidence=0.7,
                anchors=_anchors("patient_banner", "chart_right_rail"),
                evidence=["patient_banner_visible_but_subsurface_ambiguous"],
                heading=heading,
                stability_flags=["ambiguous_chart_shell"],
                patient_context_visible=True,
            )

    return _build_surface_state(
        SurfaceType.UNKNOWN,
        active_url=url,
        confidence=0.2,
        anchors=[],
        evidence=["no_surface_match"],
        heading=heading,
        patient_context_visible=patient_context_visible,
    )


def resolve_surface_from_url(url: str) -> ChartSurfaceState:
    return resolve_surface_state(url=url, selector_hits={}, headings=[], visible_text=[])


__all__ = [
    "ChartSurfaceState",
    "SURFACE_DEFINITIONS",
    "SurfaceDefinition",
    "coarse_surface",
    "resolve_surface_from_url",
    "resolve_surface_state",
    "restorable_surface_for_resume",
]
