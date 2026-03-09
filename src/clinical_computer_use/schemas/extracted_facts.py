"""
Structured extraction schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source_label: str = Field(..., description="Human-readable source reference")
    fact: str = Field(..., description="Fact extracted from the chart")


class ExtractedFacts(BaseModel):
    patient_label: str | None = None
    encounter_label: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
