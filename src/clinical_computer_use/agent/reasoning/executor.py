"""Executor role scaffold."""

from dataclasses import dataclass


@dataclass
class ExecutorDecision:
    action: str
    rationale: str

