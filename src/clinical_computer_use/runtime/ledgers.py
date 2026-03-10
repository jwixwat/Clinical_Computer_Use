"""Typed search/artifact/evidence ledgers for resumable runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from urllib.parse import urlparse

from clinical_computer_use.schemas.contract_types import ArtifactClass, SurfaceType


def infer_surface_from_url(url: str) -> SurfaceType:
    normalized = (url or "").lower()
    if "documents" in normalized:
        return SurfaceType.DOCUMENTS
    if "results" in normalized:
        return SurfaceType.RESULTS
    if "calendar" in normalized:
        return SurfaceType.CALENDAR
    if "viewer" in normalized:
        return SurfaceType.VIEWER
    if "forms" in normalized:
        return SurfaceType.FORMS
    if urlparse(normalized).path in ("", "/"):
        return SurfaceType.CHART_HOME
    return SurfaceType.UNKNOWN


def candidate_key(candidate: dict[str, str]) -> str:
    return "|".join(
        [
            str(candidate.get("tag", "")).strip().lower(),
            str(candidate.get("type", "")).strip().lower(),
            str(candidate.get("label", "")).strip().lower(),
        ]
    )


@dataclass
class SearchEpisode:
    step: int
    surface: SurfaceType
    query: str = ""
    date_floor: str | None = None
    date_ceiling: str | None = None
    result_count: int = 0
    exhausted: bool = False
    broadened: bool = False
    broadening_reason: str = ""
    fallback_from_surface: SurfaceType | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["surface"] = self.surface.value
        if self.fallback_from_surface is not None:
            payload["fallback_from_surface"] = self.fallback_from_surface.value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SearchEpisode":
        try:
            surface = SurfaceType(str(payload.get("surface", SurfaceType.UNKNOWN.value)))
        except ValueError:
            surface = SurfaceType.UNKNOWN

        fallback = payload.get("fallback_from_surface")
        fallback_surface: SurfaceType | None = None
        if fallback is not None:
            try:
                fallback_surface = SurfaceType(str(fallback))
            except ValueError:
                fallback_surface = SurfaceType.UNKNOWN

        return cls(
            step=int(payload.get("step", 0) or 0),
            surface=surface,
            query=str(payload.get("query", "")),
            date_floor=str(payload.get("date_floor")) if payload.get("date_floor") is not None else None,
            date_ceiling=str(payload.get("date_ceiling")) if payload.get("date_ceiling") is not None else None,
            result_count=int(payload.get("result_count", 0) or 0),
            exhausted=bool(payload.get("exhausted", False)),
            broadened=bool(payload.get("broadened", False)),
            broadening_reason=str(payload.get("broadening_reason", "")),
            fallback_from_surface=fallback_surface,
        )


@dataclass
class ArtifactRecord:
    candidate_key: str
    source_surface: SurfaceType
    label: str
    title: str = ""
    date: str | None = None
    sender: str = ""
    provisional_class: ArtifactClass = ArtifactClass.UNKNOWN
    relevance_score: float = 0.0
    opened_count: int = 0
    rejected_reason: str = ""
    verified: bool = False
    last_seen_step: int = 0

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_surface"] = self.source_surface.value
        payload["provisional_class"] = self.provisional_class.value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ArtifactRecord":
        try:
            source_surface = SurfaceType(str(payload.get("source_surface", SurfaceType.UNKNOWN.value)))
        except ValueError:
            source_surface = SurfaceType.UNKNOWN
        try:
            provisional_class = ArtifactClass(str(payload.get("provisional_class", ArtifactClass.UNKNOWN.value)))
        except ValueError:
            provisional_class = ArtifactClass.UNKNOWN
        return cls(
            candidate_key=str(payload.get("candidate_key", "")),
            source_surface=source_surface,
            label=str(payload.get("label", "")),
            title=str(payload.get("title", "")),
            date=str(payload.get("date")) if payload.get("date") is not None else None,
            sender=str(payload.get("sender", "")),
            provisional_class=provisional_class,
            relevance_score=float(payload.get("relevance_score", 0.0) or 0.0),
            opened_count=int(payload.get("opened_count", 0) or 0),
            rejected_reason=str(payload.get("rejected_reason", "")),
            verified=bool(payload.get("verified", False)),
            last_seen_step=int(payload.get("last_seen_step", 0) or 0),
        )


@dataclass
class EvidenceRecord:
    evidence_id: str
    step: int
    source_surface: SurfaceType
    artifact_key: str | None
    kind: str
    content: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_surface"] = self.source_surface.value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "EvidenceRecord":
        try:
            source_surface = SurfaceType(str(payload.get("source_surface", SurfaceType.UNKNOWN.value)))
        except ValueError:
            source_surface = SurfaceType.UNKNOWN
        return cls(
            evidence_id=str(payload.get("evidence_id", "")),
            step=int(payload.get("step", 0) or 0),
            source_surface=source_surface,
            artifact_key=str(payload.get("artifact_key")) if payload.get("artifact_key") is not None else None,
            kind=str(payload.get("kind", "")),
            content=str(payload.get("content", "")),
        )


@dataclass
class RunLedgers:
    search_episodes: list[SearchEpisode] = field(default_factory=list)
    artifact_registry: dict[str, ArtifactRecord] = field(default_factory=dict)
    evidence_records: list[EvidenceRecord] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
    broadenings: list[str] = field(default_factory=list)
    last_candidate_key: str | None = None
    step_counter: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "search_episodes": [episode.to_dict() for episode in self.search_episodes],
            "artifact_registry": {key: value.to_dict() for key, value in self.artifact_registry.items()},
            "evidence_records": [record.to_dict() for record in self.evidence_records],
            "claims": list(self.claims),
            "uncertainties": list(self.uncertainties),
            "broadenings": list(self.broadenings),
            "last_candidate_key": self.last_candidate_key,
            "step_counter": self.step_counter,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RunLedgers":
        raw_search = payload.get("search_episodes", [])
        search_episodes: list[SearchEpisode] = []
        if isinstance(raw_search, list):
            for item in raw_search:
                if isinstance(item, dict):
                    search_episodes.append(SearchEpisode.from_dict(item))

        raw_registry = payload.get("artifact_registry", {})
        artifact_registry: dict[str, ArtifactRecord] = {}
        if isinstance(raw_registry, dict):
            for key, value in raw_registry.items():
                if isinstance(value, dict):
                    artifact_registry[str(key)] = ArtifactRecord.from_dict(value)

        raw_evidence = payload.get("evidence_records", [])
        evidence_records: list[EvidenceRecord] = []
        if isinstance(raw_evidence, list):
            for item in raw_evidence:
                if isinstance(item, dict):
                    evidence_records.append(EvidenceRecord.from_dict(item))

        return cls(
            search_episodes=search_episodes,
            artifact_registry=artifact_registry,
            evidence_records=evidence_records,
            claims=[str(x) for x in payload.get("claims", [])] if isinstance(payload.get("claims", []), list) else [],
            uncertainties=[str(x) for x in payload.get("uncertainties", [])]
            if isinstance(payload.get("uncertainties", []), list)
            else [],
            broadenings=[str(x) for x in payload.get("broadenings", [])] if isinstance(payload.get("broadenings", []), list) else [],
            last_candidate_key=str(payload.get("last_candidate_key")) if payload.get("last_candidate_key") is not None else None,
            step_counter=int(payload.get("step_counter", 0) or 0),
        )

    @property
    def rejected_candidates(self) -> list[str]:
        return [key for key, record in self.artifact_registry.items() if record.rejected_reason]

    @property
    def opened_candidates(self) -> list[str]:
        return [key for key, record in self.artifact_registry.items() if record.opened_count > 0]


def build_empty_ledgers() -> RunLedgers:
    return RunLedgers()


def next_step(ledgers: RunLedgers) -> int:
    ledgers.step_counter += 1
    return ledgers.step_counter


def note_search_episode(
    ledgers: RunLedgers,
    *,
    surface: SurfaceType,
    query: str = "",
    date_floor: str | None = None,
    date_ceiling: str | None = None,
    result_count: int = 0,
    exhausted: bool = False,
    broadened: bool = False,
    broadening_reason: str = "",
    fallback_from_surface: SurfaceType | None = None,
    step: int | None = None,
) -> SearchEpisode:
    effective_step = step if step is not None else ledgers.step_counter
    episode = SearchEpisode(
        step=effective_step,
        surface=surface,
        query=query,
        date_floor=date_floor,
        date_ceiling=date_ceiling,
        result_count=result_count,
        exhausted=exhausted,
        broadened=broadened,
        broadening_reason=broadening_reason,
        fallback_from_surface=fallback_from_surface,
    )
    ledgers.search_episodes.append(episode)
    if broadened and broadening_reason:
        ledgers.broadenings.append(broadening_reason)
    return episode


def _infer_provisional_class_from_label(label: str) -> ArtifactClass:
    text = (label or "").lower()
    if "progress note" in text or "note" in text:
        return ArtifactClass.CHART_NOTE
    if "pdf" in text:
        return ArtifactClass.PDF_FORM
    if "scann" in text:
        return ArtifactClass.SCANNED_FORM
    if "result" in text or "lab" in text:
        return ArtifactClass.RESULT_ARTIFACT
    if "consult" in text:
        return ArtifactClass.CONSULT_LETTER
    if "form" in text:
        return ArtifactClass.BUILT_IN_FORM
    if "document" in text:
        return ArtifactClass.EXTERNAL_DOCUMENT
    return ArtifactClass.UNKNOWN


def upsert_artifact_from_candidate(
    ledgers: RunLedgers,
    *,
    candidate: dict[str, str],
    source_surface: SurfaceType,
    step: int,
) -> ArtifactRecord:
    key = candidate_key(candidate)
    label = str(candidate.get("label", ""))
    existing = ledgers.artifact_registry.get(key)
    if existing is None:
        existing = ArtifactRecord(
            candidate_key=key,
            source_surface=source_surface,
            label=label,
            provisional_class=_infer_provisional_class_from_label(label),
            last_seen_step=step,
        )
        ledgers.artifact_registry[key] = existing
    else:
        existing.last_seen_step = step
        if not existing.label and label:
            existing.label = label
        if existing.provisional_class == ArtifactClass.UNKNOWN and label:
            existing.provisional_class = _infer_provisional_class_from_label(label)
    ledgers.last_candidate_key = key
    return existing


def mark_artifact_opened(ledgers: RunLedgers, key: str, step: int) -> None:
    record = ledgers.artifact_registry.get(key)
    if record is None:
        return
    record.opened_count += 1
    record.last_seen_step = step


def mark_artifact_rejected(ledgers: RunLedgers, key: str, reason: str, step: int) -> None:
    record = ledgers.artifact_registry.get(key)
    if record is None:
        return
    record.rejected_reason = reason
    record.last_seen_step = step


def mark_artifact_verified(ledgers: RunLedgers, key: str, step: int) -> None:
    record = ledgers.artifact_registry.get(key)
    if record is None:
        return
    record.verified = True
    record.last_seen_step = step


def add_evidence_record(
    ledgers: RunLedgers,
    *,
    source_surface: SurfaceType,
    kind: str,
    content: str,
    artifact_key: str | None = None,
    step: int | None = None,
) -> EvidenceRecord:
    effective_step = step if step is not None else ledgers.step_counter
    evidence = EvidenceRecord(
        evidence_id=f"e{len(ledgers.evidence_records) + 1}",
        step=effective_step,
        source_surface=source_surface,
        artifact_key=artifact_key,
        kind=kind,
        content=content,
    )
    ledgers.evidence_records.append(evidence)
    return evidence


def add_claim(ledgers: RunLedgers, claim: str) -> None:
    value = claim.strip()
    if value:
        ledgers.claims.append(value)


def add_uncertainty(ledgers: RunLedgers, uncertainty: str) -> None:
    value = uncertainty.strip()
    if value:
        ledgers.uncertainties.append(value)


def note_broadening(ledgers: RunLedgers, reason: str) -> None:
    value = reason.strip()
    if value:
        ledgers.broadenings.append(value)


def unresolved_higher_priority_candidates(ledgers: RunLedgers, preferred_surfaces: list[SurfaceType]) -> list[str]:
    rank: dict[SurfaceType, int] = {surface: idx for idx, surface in enumerate(preferred_surfaces)}
    unresolved: list[tuple[int, str]] = []
    for key, record in ledgers.artifact_registry.items():
        if record.verified:
            continue
        if record.rejected_reason:
            continue
        priority = rank.get(record.source_surface, len(preferred_surfaces) + 1)
        unresolved.append((priority, key))
    unresolved.sort(key=lambda item: item[0])
    return [key for _, key in unresolved]
