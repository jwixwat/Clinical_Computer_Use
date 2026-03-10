"""Correction delta schemas with distinct mutation planes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from clinical_computer_use.schemas.contract_types import (
    ArtifactDispositionType,
    ChangeOperation,
    ContractChangeField,
    RuntimeDirectiveType,
)


class ContractChange(BaseModel):
    field: ContractChangeField = Field(..., description="Contract field being updated")
    operation: ChangeOperation = Field(..., description="set/add/remove")
    value: str | list[str] | None = Field(default=None, description="Assigned or merged value")


class ArtifactDispositionDelta(BaseModel):
    disposition: ArtifactDispositionType
    candidate_key: str | None = None
    reason: str = ""


class RuntimeDirectiveDelta(BaseModel):
    directive: RuntimeDirectiveType
    value: str | None = None
    reason: str = ""


class CorrectionDelta(BaseModel):
    correction_text: str
    contract_changes: list[ContractChange] = Field(default_factory=list)
    artifact_dispositions: list[ArtifactDispositionDelta] = Field(default_factory=list)
    runtime_directives: list[RuntimeDirectiveDelta] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
