"""Closed-vocabulary runtime and contract enums."""

from __future__ import annotations

from enum import Enum


class ObjectiveType(str, Enum):
    FIND = "find"
    SUMMARIZE = "summarize"
    DRAFT = "draft"
    ANNOTATE = "annotate"
    FILL = "fill"


class SurfaceType(str, Enum):
    CHART_HOME = "chart_home"
    DOCUMENTS = "documents"
    RESULTS = "results"
    FORMS = "forms"
    VIEWER = "viewer"
    CALENDAR = "calendar"
    MEDICAL_SUMMARY = "medical_summary"
    MEDICAL_NOTE = "medical_note"
    PATIENT_DOCUMENTS = "patient_documents"
    PATIENT_RESULTS = "patient_results"
    PATIENT_MEDICATION = "patient_medication"
    RESULT_REVIEW = "result_review"
    RESULT_DETAIL_MODAL = "result_detail_modal"
    DOCUMENT_VIEWER_EXTERNAL = "document_viewer_external"
    UNKNOWN = "unknown"


class ArtifactClass(str, Enum):
    CHART_NOTE = "chart_note"
    EXTERNAL_DOCUMENT = "external_document"
    SCANNED_FORM = "scanned_form"
    PDF_FORM = "pdf_form"
    CONSULT_LETTER = "consult_letter"
    DISCHARGE_SUMMARY = "discharge_summary"
    RESULT_ARTIFACT = "result_artifact"
    BUILT_IN_FORM = "built_in_form"
    ANNOTATION_TARGET = "annotation_target"
    UNKNOWN = "unknown"


class ArtifactMatchMode(str, Enum):
    EXACT = "exact"
    FAMILY = "family"


class RiskTier(str, Enum):
    TIER0 = "tier0_read_search_open"
    TIER1 = "tier1_draft_edit_unsaved"
    TIER2 = "tier2_save_persist"
    TIER3 = "tier3_transmit_finalize"


class CompletionCriterion(str, Enum):
    OBJECTIVE_ADDRESSED = "requested_objective_addressed_under_current_contract"
    ARTIFACT_CLASS_VERIFIED = "artifact_class_consistency_checked"
    EVIDENCE_LINKED = "material_claims_linked_to_evidence"
    FALSIFICATION_PERFORMED = "alternative_interpretation_falsified"
    UNCERTAINTY_EXPLICIT = "uncertainties_reported_when_evidence_is_weak"


class EvidenceRequirement(str, Enum):
    LINK_CLAIMS = "link_material_claims_to_chart_evidence"
    CITE_SOURCES = "cite_source_artifact_for_material_claims"
    SURFACE_UNCERTAINTY = "surface_uncertainties_explicitly"


class ContractChangeField(str, Enum):
    PATIENT_TARGET = "patient_target"
    OBJECTIVE_TYPE = "objective_type"
    REQUIRED_ARTIFACT_CLASSES = "required_artifact_classes"
    ACCEPTABLE_ARTIFACT_CLASSES = "acceptable_artifact_classes"
    DISALLOWED_ARTIFACT_CLASSES = "disallowed_artifact_classes"
    SEARCH_PRIORS = "search_priors"
    PREFERRED_SURFACES = "preferred_surfaces"
    DATE_FLOOR = "date_floor"
    DATE_CEILING = "date_ceiling"
    ARTIFACT_MATCH_MODE = "artifact_match_mode"
    TASK_REVIEW_THRESHOLD = "task_review_threshold"


class ChangeOperation(str, Enum):
    SET = "set"
    ADD = "add"
    REMOVE = "remove"


class ArtifactDispositionType(str, Enum):
    REJECT_CANDIDATE = "reject_candidate"
    RECONSIDER_CANDIDATE = "reconsider_candidate"


class RuntimeDirectiveType(str, Enum):
    REQUIRE_REVIEW_AT_OR_ABOVE = "require_review_at_or_above"
    CONTINUE_SEARCH = "continue_search"
    CHECKPOINT_NOW = "checkpoint_now"


class RunLifecycleState(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ARCHIVED = "archived"
    PURGED = "purged"
