"""Contract compiler result models."""

from __future__ import annotations

from dataclasses import dataclass

from clinical_computer_use.schemas.correction_delta import CorrectionDelta
from clinical_computer_use.schemas.task_contract import TaskContract


@dataclass
class ContractCompileResult:
    contract: TaskContract
    notes: list[str]


@dataclass
class ContractCorrectionResult:
    contract: TaskContract
    delta: CorrectionDelta
