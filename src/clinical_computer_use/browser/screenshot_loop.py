"""
Screenshot/action loop skeleton.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StepResult:
    step_index: int
    observation: str


def run_screenshot_loop(max_steps: int) -> list[StepResult]:
    """
    Placeholder for the future screenshot/action loop.
    """
    return [
        StepResult(
            step_index=0,
            observation=f"Scaffold only. No computer loop implemented. max_steps={max_steps}",
        )
    ]
