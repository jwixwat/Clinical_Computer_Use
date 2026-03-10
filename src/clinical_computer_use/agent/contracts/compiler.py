"""Deterministic contract and correction compiler with typed semantics."""

from __future__ import annotations

import re

from clinical_computer_use.agent.contracts.models import ContractCompileResult, ContractCorrectionResult
from clinical_computer_use.schemas.contract_types import (
    ArtifactClass,
    ArtifactDispositionType,
    ArtifactMatchMode,
    ChangeOperation,
    CompletionCriterion,
    ContractChangeField,
    EvidenceRequirement,
    ObjectiveType,
    RiskTier,
    RuntimeDirectiveType,
    SurfaceType,
)
from clinical_computer_use.schemas.correction_delta import (
    ArtifactDispositionDelta,
    ContractChange,
    CorrectionDelta,
    RuntimeDirectiveDelta,
)
from clinical_computer_use.schemas.task_contract import ContractDiagnostics, TaskContract

_DATE_RE = re.compile(r"(?:after|since|from)\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)


def _dedupe_enum[T](values: list[T]) -> list[T]:
    seen: set[str] = set()
    ordered: list[T] = []
    for item in values:
        marker = str(item)
        if marker in seen:
            continue
        seen.add(marker)
        ordered.append(item)
    return ordered


def _detect_objective_type(text: str) -> ObjectiveType:
    if any(k in text for k in ("summarize", "summary", "report back", "understanding")):
        return ObjectiveType.SUMMARIZE
    if any(k in text for k in ("draft", "pre-fill", "prefill")):
        return ObjectiveType.DRAFT
    if any(k in text for k in ("annotate", "annotation")):
        return ObjectiveType.ANNOTATE
    if any(k in text for k in ("fill", "populate")):
        return ObjectiveType.FILL
    return ObjectiveType.FIND


def _detect_required_and_acceptable_classes(text: str) -> tuple[list[ArtifactClass], list[ArtifactClass], list[ArtifactClass]]:
    required: list[ArtifactClass] = []
    acceptable: list[ArtifactClass] = []
    priors: list[ArtifactClass] = []

    if "form" in text:
        acceptable.extend(
            [
                ArtifactClass.EXTERNAL_DOCUMENT,
                ArtifactClass.PDF_FORM,
                ArtifactClass.SCANNED_FORM,
                ArtifactClass.BUILT_IN_FORM,
            ]
        )
        priors.extend([ArtifactClass.EXTERNAL_DOCUMENT, ArtifactClass.PDF_FORM, ArtifactClass.SCANNED_FORM])

    if "external" in text and "form" in text:
        required.append(ArtifactClass.EXTERNAL_DOCUMENT)
    if "pdf" in text and "form" in text:
        required.append(ArtifactClass.PDF_FORM)
    if "scanned" in text or "scan" in text:
        acceptable.append(ArtifactClass.SCANNED_FORM)
    if "document" in text or "documents" in text:
        acceptable.append(ArtifactClass.EXTERNAL_DOCUMENT)
    if "note" in text and "not" not in text:
        acceptable.append(ArtifactClass.CHART_NOTE)
    if any(k in text for k in ("results", "result", "lab")):
        acceptable.append(ArtifactClass.RESULT_ARTIFACT)
        priors.append(ArtifactClass.RESULT_ARTIFACT)
    if "consult" in text:
        acceptable.append(ArtifactClass.CONSULT_LETTER)

    if not priors:
        priors = [ArtifactClass.EXTERNAL_DOCUMENT, ArtifactClass.RESULT_ARTIFACT, ArtifactClass.CHART_NOTE]

    return _dedupe_enum(required), _dedupe_enum(acceptable), _dedupe_enum(priors)


def _detect_disallowed_classes(text: str) -> list[ArtifactClass]:
    disallowed: list[ArtifactClass] = []
    if "not a note" in text or "not note" in text or "not a chart note" in text:
        disallowed.append(ArtifactClass.CHART_NOTE)
    if "not a result" in text or "not result" in text:
        disallowed.append(ArtifactClass.RESULT_ARTIFACT)
    return _dedupe_enum(disallowed)


def _detect_preferred_surfaces(text: str) -> list[SurfaceType]:
    if "documents first" in text:
        return [SurfaceType.DOCUMENTS, SurfaceType.RESULTS, SurfaceType.CHART_HOME]
    if "results first" in text:
        return [SurfaceType.RESULTS, SurfaceType.DOCUMENTS, SurfaceType.CHART_HOME]

    has_documents = "documents" in text or "document" in text
    has_results = "results" in text or "result" in text
    if has_documents and has_results:
        return [SurfaceType.DOCUMENTS, SurfaceType.RESULTS, SurfaceType.CHART_HOME]
    if has_documents:
        return [SurfaceType.DOCUMENTS, SurfaceType.CHART_HOME, SurfaceType.RESULTS]
    if has_results:
        return [SurfaceType.RESULTS, SurfaceType.CHART_HOME, SurfaceType.DOCUMENTS]
    return [SurfaceType.CHART_HOME, SurfaceType.DOCUMENTS, SurfaceType.RESULTS]


def _detect_date_floor(text: str) -> str | None:
    match = _DATE_RE.search(text)
    return match.group(1) if match else None


def _build_diagnostics(
    *,
    patient_target: str | None,
    required: list[ArtifactClass],
    acceptable: list[ArtifactClass],
    disallowed: list[ArtifactClass],
) -> ContractDiagnostics:
    contradictions: list[str] = []
    unsupported_constraints: list[str] = []
    notes: list[str] = ["deterministic_contract_compiler_v2"]

    for item in required:
        if item in disallowed:
            contradictions.append(f"required_artifact_class_conflicts_with_disallowed:{item.value}")

    if not patient_target:
        notes.append("missing_patient_target")
    if not required and not acceptable:
        unsupported_constraints.append("artifact_class_not_inferred_from_prompt")

    needs_clarification = bool(contradictions or unsupported_constraints)
    confidence = 0.85
    if not patient_target:
        confidence -= 0.15
    if unsupported_constraints:
        confidence -= 0.2
    if contradictions:
        confidence -= 0.35

    return ContractDiagnostics(
        confidence=max(0.0, min(1.0, confidence)),
        contradictions=contradictions,
        unsupported_constraints=unsupported_constraints,
        needs_clarification=needs_clarification,
        notes=notes,
    )


def compile_task_contract(user_prompt: str, patient_target: str | None = None) -> ContractCompileResult:
    text = user_prompt.strip().lower()
    objective_type = _detect_objective_type(text)
    required, acceptable, search_priors = _detect_required_and_acceptable_classes(text)
    disallowed_classes = _detect_disallowed_classes(text)
    preferred_surfaces = _detect_preferred_surfaces(text)
    date_floor = _detect_date_floor(text)

    evidence_requirements: list[EvidenceRequirement] = [EvidenceRequirement.LINK_CLAIMS]
    if any(k in text for k in ("cite", "citation", "source")):
        evidence_requirements.append(EvidenceRequirement.CITE_SOURCES)
    if any(k in text for k in ("uncertain", "uncertainty")):
        evidence_requirements.append(EvidenceRequirement.SURFACE_UNCERTAINTY)

    completion_test = [
        CompletionCriterion.OBJECTIVE_ADDRESSED,
        CompletionCriterion.ARTIFACT_CLASS_VERIFIED,
        CompletionCriterion.EVIDENCE_LINKED,
        CompletionCriterion.FALSIFICATION_PERFORMED,
        CompletionCriterion.UNCERTAINTY_EXPLICIT,
    ]

    uncertainties: list[str] = []
    if not patient_target:
        uncertainties.append("patient_target_not_explicitly_provided")
    if not required and not acceptable:
        uncertainties.append("target_artifact_class_not_explicitly_stated")

    diagnostics = _build_diagnostics(
        patient_target=patient_target,
        required=required,
        acceptable=acceptable,
        disallowed=disallowed_classes,
    )
    if diagnostics.needs_clarification:
        uncertainties.append("contract_requires_clarification_before_high_confidence_execution")

    contract = TaskContract(
        patient_target=patient_target,
        objective_type=objective_type,
        required_artifact_classes=required,
        acceptable_artifact_classes=acceptable,
        disallowed_artifact_classes=disallowed_classes,
        search_priors=search_priors,
        artifact_match_mode=ArtifactMatchMode.FAMILY,
        preferred_surfaces=preferred_surfaces,
        date_floor=date_floor,
        evidence_requirements=_dedupe_enum(evidence_requirements),
        completion_test=completion_test,
        task_review_threshold=RiskTier.TIER2,
        uncertainties=_dedupe_str(uncertainties),
        diagnostics=diagnostics,
        source_prompt=user_prompt,
    )

    notes = [
        "deterministic_contract_compiler_v2",
        "policy_plane_is_runtime_authority_for_block_and_approval",
        "use_correction_compiler_to_apply_stateful_deltas_without_reset",
    ]
    return ContractCompileResult(contract=contract, notes=notes)


def _dedupe_str(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in values:
        v = item.strip().lower()
        if not v or v in seen:
            continue
        seen.add(v)
        ordered.append(v)
    return ordered


def _coerce_enum_list[T](enum_cls: type[T], value: str | list[str] | None) -> list[T]:
    if value is None:
        return []
    raw = value if isinstance(value, list) else [value]
    result: list[T] = []
    for item in raw:
        try:
            result.append(enum_cls(str(item)))
        except ValueError:
            continue
    return _dedupe_enum(result)


def _apply_contract_change(contract: TaskContract, change: ContractChange) -> None:
    field_name = change.field.value
    op = change.operation

    if field_name == ContractChangeField.PATIENT_TARGET.value:
        if op == ChangeOperation.SET:
            contract.patient_target = str(change.value) if change.value is not None else None
        return

    if field_name == ContractChangeField.DATE_FLOOR.value:
        if op == ChangeOperation.SET:
            contract.date_floor = str(change.value) if change.value is not None else None
        return

    if field_name == ContractChangeField.DATE_CEILING.value:
        if op == ChangeOperation.SET:
            contract.date_ceiling = str(change.value) if change.value is not None else None
        return

    if field_name == ContractChangeField.ARTIFACT_MATCH_MODE.value:
        if op == ChangeOperation.SET and change.value is not None:
            try:
                contract.artifact_match_mode = ArtifactMatchMode(str(change.value))
            except ValueError:
                return
        return

    if field_name == ContractChangeField.TASK_REVIEW_THRESHOLD.value:
        if op == ChangeOperation.SET:
            if change.value is None:
                contract.task_review_threshold = None
            else:
                try:
                    contract.task_review_threshold = RiskTier(str(change.value))
                except ValueError:
                    return
        return

    if field_name == ContractChangeField.PREFERRED_SURFACES.value:
        values = _coerce_enum_list(SurfaceType, change.value)
        if op == ChangeOperation.SET:
            contract.preferred_surfaces = values
        elif op == ChangeOperation.ADD:
            contract.preferred_surfaces = _dedupe_enum(list(contract.preferred_surfaces) + values)
        elif op == ChangeOperation.REMOVE:
            remove = {item.value for item in values}
            contract.preferred_surfaces = [item for item in contract.preferred_surfaces if item.value not in remove]
        return

    if field_name == ContractChangeField.REQUIRED_ARTIFACT_CLASSES.value:
        values = _coerce_enum_list(ArtifactClass, change.value)
        if op == ChangeOperation.SET:
            contract.required_artifact_classes = values
        elif op == ChangeOperation.ADD:
            contract.required_artifact_classes = _dedupe_enum(list(contract.required_artifact_classes) + values)
        elif op == ChangeOperation.REMOVE:
            remove = {item.value for item in values}
            contract.required_artifact_classes = [item for item in contract.required_artifact_classes if item.value not in remove]
        return

    if field_name == ContractChangeField.ACCEPTABLE_ARTIFACT_CLASSES.value:
        values = _coerce_enum_list(ArtifactClass, change.value)
        if op == ChangeOperation.SET:
            contract.acceptable_artifact_classes = values
        elif op == ChangeOperation.ADD:
            contract.acceptable_artifact_classes = _dedupe_enum(list(contract.acceptable_artifact_classes) + values)
        elif op == ChangeOperation.REMOVE:
            remove = {item.value for item in values}
            contract.acceptable_artifact_classes = [item for item in contract.acceptable_artifact_classes if item.value not in remove]
        return

    if field_name == ContractChangeField.DISALLOWED_ARTIFACT_CLASSES.value:
        values = _coerce_enum_list(ArtifactClass, change.value)
        if op == ChangeOperation.SET:
            contract.disallowed_artifact_classes = values
        elif op == ChangeOperation.ADD:
            contract.disallowed_artifact_classes = _dedupe_enum(list(contract.disallowed_artifact_classes) + values)
        elif op == ChangeOperation.REMOVE:
            remove = {item.value for item in values}
            contract.disallowed_artifact_classes = [item for item in contract.disallowed_artifact_classes if item.value not in remove]
        return

    if field_name == ContractChangeField.SEARCH_PRIORS.value:
        values = _coerce_enum_list(ArtifactClass, change.value)
        if op == ChangeOperation.SET:
            contract.search_priors = values
        elif op == ChangeOperation.ADD:
            contract.search_priors = _dedupe_enum(list(contract.search_priors) + values)
        elif op == ChangeOperation.REMOVE:
            remove = {item.value for item in values}
            contract.search_priors = [item for item in contract.search_priors if item.value not in remove]


def apply_correction(contract: TaskContract, correction_text: str) -> ContractCorrectionResult:
    text = correction_text.strip().lower()
    contract_changes: list[ContractChange] = []
    artifact_dispositions: list[ArtifactDispositionDelta] = []
    runtime_directives: list[RuntimeDirectiveDelta] = []
    notes: list[str] = []

    if "not that one" in text:
        artifact_dispositions.append(
            ArtifactDispositionDelta(
                disposition=ArtifactDispositionType.REJECT_CANDIDATE,
                candidate_key=None,
                reason="user_rejected_current_candidate",
            )
        )
        notes.append("user_rejected_current_candidate")

    if "not a note" in text or "not note" in text or "not a chart note" in text:
        contract_changes.append(
            ContractChange(
                field=ContractChangeField.DISALLOWED_ARTIFACT_CLASSES,
                operation=ChangeOperation.ADD,
                value=[ArtifactClass.CHART_NOTE.value],
            )
        )

    if "documents first" in text or "go to documents" in text:
        contract_changes.append(
            ContractChange(
                field=ContractChangeField.PREFERRED_SURFACES,
                operation=ChangeOperation.SET,
                value=[SurfaceType.DOCUMENTS.value, SurfaceType.RESULTS.value, SurfaceType.CHART_HOME.value],
            )
        )

    if "results first" in text or "go to results" in text:
        contract_changes.append(
            ContractChange(
                field=ContractChangeField.PREFERRED_SURFACES,
                operation=ChangeOperation.SET,
                value=[SurfaceType.RESULTS.value, SurfaceType.DOCUMENTS.value, SurfaceType.CHART_HOME.value],
            )
        )

    date_match = _DATE_RE.search(text)
    if date_match:
        contract_changes.append(
            ContractChange(
                field=ContractChangeField.DATE_FLOOR,
                operation=ChangeOperation.SET,
                value=date_match.group(1),
            )
        )

    if "remove date floor" in text or "no date floor" in text:
        contract_changes.append(
            ContractChange(
                field=ContractChangeField.DATE_FLOOR,
                operation=ChangeOperation.SET,
                value=None,
            )
        )

    if "exact class" in text or "must be exact" in text:
        contract_changes.append(
            ContractChange(
                field=ContractChangeField.ARTIFACT_MATCH_MODE,
                operation=ChangeOperation.SET,
                value=ArtifactMatchMode.EXACT.value,
            )
        )

    if "require review before save" in text or "review before save" in text:
        runtime_directives.append(
            RuntimeDirectiveDelta(
                directive=RuntimeDirectiveType.REQUIRE_REVIEW_AT_OR_ABOVE,
                value=RiskTier.TIER2.value,
                reason="user_requested_review_before_persistence",
            )
        )

    if "checkpoint now" in text:
        runtime_directives.append(
            RuntimeDirectiveDelta(
                directive=RuntimeDirectiveType.CHECKPOINT_NOW,
                reason="user_requested_immediate_checkpoint",
            )
        )

    patient_match = re.search(r"patient\s*[:=]\s*([a-z0-9\-\s]+)", correction_text, re.IGNORECASE)
    if patient_match:
        contract_changes.append(
            ContractChange(
                field=ContractChangeField.PATIENT_TARGET,
                operation=ChangeOperation.SET,
                value=patient_match.group(1).strip(),
            )
        )

    if not contract_changes and not artifact_dispositions and not runtime_directives:
        notes.append("no_structured_delta_detected")

    updated = TaskContract.model_validate(contract.model_dump())
    for change in contract_changes:
        _apply_contract_change(updated, change)

    delta = CorrectionDelta(
        correction_text=correction_text,
        contract_changes=contract_changes,
        artifact_dispositions=artifact_dispositions,
        runtime_directives=runtime_directives,
        notes=notes,
    )
    return ContractCorrectionResult(contract=updated, delta=delta)
