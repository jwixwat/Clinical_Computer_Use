"""
Task result schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TaskResult(BaseModel):
    task_name: str
    completed: bool = False
    review_required: bool = True
    summary: str = ""
    warnings: list[str] = Field(default_factory=list)
