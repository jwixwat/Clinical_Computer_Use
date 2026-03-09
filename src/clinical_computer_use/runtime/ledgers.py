"""Ledger scaffold models for future resumable runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class SearchLedger:
    surfaces_searched: list[str] = field(default_factory=list)
    queries_used: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    broadenings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class EvidenceLedger:
    evidence_items: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class RunLedgers:
    search: SearchLedger = field(default_factory=SearchLedger)
    evidence: EvidenceLedger = field(default_factory=EvidenceLedger)
    rejected_candidates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "search": self.search.to_dict(),
            "evidence": self.evidence.to_dict(),
            "rejected_candidates": list(self.rejected_candidates),
        }


def build_empty_ledgers() -> RunLedgers:
    return RunLedgers()
