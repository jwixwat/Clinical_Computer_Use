"""Artifact policy, manifesting, and cleanup helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from typing import Any

from clinical_computer_use.config import ARTIFACT_POLICY_VERSION, ARTIFACT_RETENTION_DAYS, ROOT, TRACE_DIR
from clinical_computer_use.session import SessionContext


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class ArtifactPolicy:
    policy_version: str
    retention_days: int
    contains_phi: bool
    export_policy: str
    notes: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_version": self.policy_version,
            "retention_days": self.retention_days,
            "contains_phi": self.contains_phi,
            "export_policy": self.export_policy,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ArtifactPolicy":
        notes = payload.get("notes", [])
        return cls(
            policy_version=str(payload.get("policy_version", ARTIFACT_POLICY_VERSION)),
            retention_days=int(payload.get("retention_days", ARTIFACT_RETENTION_DAYS)),
            contains_phi=bool(payload.get("contains_phi", True)),
            export_policy=str(payload.get("export_policy", "restricted_internal_only")),
            notes=[str(item) for item in notes] if isinstance(notes, list) else [],
        )


def build_default_artifact_policy() -> ArtifactPolicy:
    return ArtifactPolicy(
        policy_version=ARTIFACT_POLICY_VERSION,
        retention_days=ARTIFACT_RETENTION_DAYS,
        contains_phi=True,
        export_policy="restricted_internal_only",
        notes=[
            "traces_and_screenshots_may_contain_phi",
            "external_sharing_requires_governance_review",
        ],
    )


def _policy_path(session: SessionContext) -> Path:
    return session.trace_dir / "artifact_policy.json"


def _manifest_path(session: SessionContext) -> Path:
    return session.trace_dir / "artifact_manifest.jsonl"


def ensure_artifact_policy(session: SessionContext) -> ArtifactPolicy:
    path = _policy_path(session)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            return ArtifactPolicy.from_dict(payload)
    policy = build_default_artifact_policy()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(policy.to_dict(), handle, indent=2)
    return policy


def append_artifact_manifest(
    session: SessionContext,
    *,
    artifact_type: str,
    path: Path,
    metadata: dict[str, Any] | None = None,
) -> Path:
    policy = ensure_artifact_policy(session)
    entry = {
        "timestamp": _utc_now_iso(),
        "artifact_type": artifact_type,
        "path": str(path.resolve()),
        "retention_days": policy.retention_days,
        "contains_phi": policy.contains_phi,
        "policy_version": policy.policy_version,
        "metadata": metadata or {},
    }
    manifest = _manifest_path(session)
    with manifest.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    return manifest


@dataclass
class CleanupResult:
    scanned_entries: int
    eligible_entries: int
    deleted_paths: list[str]
    skipped_paths: list[str]
    dry_run: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "scanned_entries": self.scanned_entries,
            "eligible_entries": self.eligible_entries,
            "deleted_paths": self.deleted_paths,
            "skipped_paths": self.skipped_paths,
            "dry_run": self.dry_run,
        }


def _safe_for_cleanup(path: Path) -> bool:
    resolved = path.resolve()
    root = ROOT.resolve()
    return resolved == root or root in resolved.parents


def cleanup_artifacts(*, older_than_days: int, dry_run: bool = True) -> CleanupResult:
    cutoff = datetime.now(UTC) - timedelta(days=max(0, older_than_days))
    scanned_entries = 0
    eligible_entries = 0
    deleted_paths: list[str] = []
    skipped_paths: list[str] = []

    for session_dir in TRACE_DIR.glob("*"):
        manifest_path = session_dir / "artifact_manifest.jsonl"
        if not manifest_path.exists():
            continue
        try:
            lines = manifest_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        for line in lines:
            if not line.strip():
                continue
            scanned_entries += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            timestamp = payload.get("timestamp")
            path_value = payload.get("path")
            if not isinstance(timestamp, str) or not isinstance(path_value, str):
                continue
            try:
                created = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                continue
            if created > cutoff:
                continue
            target_path = Path(path_value)
            if not _safe_for_cleanup(target_path):
                skipped_paths.append(path_value)
                continue
            eligible_entries += 1
            if dry_run:
                skipped_paths.append(path_value)
                continue
            try:
                if target_path.exists():
                    target_path.unlink()
                    deleted_paths.append(path_value)
                else:
                    skipped_paths.append(path_value)
            except Exception:
                skipped_paths.append(path_value)

    return CleanupResult(
        scanned_entries=scanned_entries,
        eligible_entries=eligible_entries,
        deleted_paths=deleted_paths,
        skipped_paths=skipped_paths,
        dry_run=dry_run,
    )

