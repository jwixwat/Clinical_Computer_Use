"""Task contract schemas for contract-governed execution."""

from __future__ import annotations

from pydantic import BaseModel, Field

from clinical_computer_use.schemas.contract_types import (
    ArtifactClass,
    ArtifactMatchMode,
    CompletionCriterion,
    EvidenceRequirement,
    ObjectiveType,
    RiskTier,
    SurfaceType,
)


class ContractDiagnostics(BaseModel):
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    contradictions: list[str] = Field(default_factory=list)
    unsupported_constraints: list[str] = Field(default_factory=list)
    needs_clarification: bool = Field(default=False)
    notes: list[str] = Field(default_factory=list)


class TaskContract(BaseModel):
    patient_target: str | None = Field(default=None, description="Intended patient identifier or label from task ask")
    objective_type: ObjectiveType = Field(default=ObjectiveType.FIND, description="Operational objective type")

    # Artifact semantics are explicit to avoid ambiguity across N3/N4 verifier logic.
    required_artifact_classes: list[ArtifactClass] = Field(default_factory=list)
    acceptable_artifact_classes: list[ArtifactClass] = Field(default_factory=list)
    disallowed_artifact_classes: list[ArtifactClass] = Field(default_factory=list)
    search_priors: list[ArtifactClass] = Field(default_factory=list)
    artifact_match_mode: ArtifactMatchMode = Field(default=ArtifactMatchMode.FAMILY)

    preferred_surfaces: list[SurfaceType] = Field(default_factory=list)
    date_floor: str | None = Field(default=None, description="Inclusive YYYY-MM-DD date floor when applicable")
    date_ceiling: str | None = Field(default=None, description="Inclusive YYYY-MM-DD date ceiling when applicable")

    evidence_requirements: list[EvidenceRequirement] = Field(default_factory=list)
    completion_test: list[CompletionCriterion] = Field(default_factory=list)

    # Task-plane preference, distinct from global runtime policy gates.
    task_review_threshold: RiskTier | None = Field(default=None)

    uncertainties: list[str] = Field(default_factory=list)
    diagnostics: ContractDiagnostics = Field(default_factory=ContractDiagnostics)
    contract_version: str = Field(default="n1.v2")
    source_prompt: str = Field(default="", description="Original user instruction used to compile this contract")
