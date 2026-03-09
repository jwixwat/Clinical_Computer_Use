"""
Schema for constrained browser actions in the supervised in-chart loop.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BrowserActionDecision(BaseModel):
    action_type: str = Field(
        ...,
        description="One of: click, type, scroll, finish",
    )
    target_id: str | None = Field(
        default=None,
        description="Agent-visible target id for click/type actions.",
    )
    text: str | None = Field(
        default=None,
        description="Text to type for type actions.",
    )
    scroll_direction: str | None = Field(
        default=None,
        description="One of: down, up for scroll actions.",
    )
    rationale: str = Field(
        ...,
        description="Why this action is the best next step.",
    )
    expected_outcome: str = Field(
        ...,
        description="What the model expects to see after this action.",
    )
    final_report: str | None = Field(
        default=None,
        description="Required when action_type is finish. Summarize findings and understanding.",
    )
