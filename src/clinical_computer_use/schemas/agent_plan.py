"""
Schema for the minimal supervised planning response.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProposedAction(BaseModel):
    action: str = Field(..., description="Short machine-readable action label")
    rationale: str = Field(..., description="Why this action is being proposed")


class AgentPlan(BaseModel):
    task_summary: str = Field(..., description="High-level summary of the user's requested task")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions the model is making")
    proposed_actions: list[ProposedAction] = Field(
        default_factory=list,
        description="Actions the model would like to take next",
    )
    uncertainties: list[str] = Field(
        default_factory=list,
        description="Uncertainties or missing information",
    )
    review_handoff: str = Field(
        ...,
        description="What the human should review or decide before continuation",
    )


class ObservedScreenPlan(BaseModel):
    screen_summary: str = Field(..., description="What is visible on the current screen")
    notable_elements: list[str] = Field(
        default_factory=list,
        description="Buttons, fields, menus, or content areas that matter",
    )
    proposed_next_actions: list[ProposedAction] = Field(
        default_factory=list,
        description="Read-only next actions the model would propose",
    )
    uncertainty_flags: list[str] = Field(
        default_factory=list,
        description="What is uncertain from the screenshot alone",
    )
    review_handoff: str = Field(
        ...,
        description="What the human should decide or verify next",
    )
