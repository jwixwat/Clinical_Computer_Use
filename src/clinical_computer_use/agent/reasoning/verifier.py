"""Verifier role scaffold."""

from dataclasses import dataclass


@dataclass
class VerificationResult:
    complete: bool
    reason: str

