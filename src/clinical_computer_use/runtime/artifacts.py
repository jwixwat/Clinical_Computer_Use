"""Compatibility artifact writer module."""

from __future__ import annotations

from pathlib import Path

from clinical_computer_use.runtime.artifact_policy import (
    CleanupResult,
    append_artifact_manifest,
    cleanup_artifacts,
    ensure_artifact_policy,
)
from clinical_computer_use.session import SessionContext
from clinical_computer_use.traces import append_event, write_json_trace


def ensure_artifact_policy_for_session(session: SessionContext) -> Path:
    path = session.trace_dir / "artifact_policy.json"
    ensure_artifact_policy(session)
    return path


def register_artifact(
    session: SessionContext,
    *,
    artifact_type: str,
    artifact_path: Path,
    metadata: dict[str, object] | None = None,
) -> Path:
    return append_artifact_manifest(
        session,
        artifact_type=artifact_type,
        path=artifact_path,
        metadata=metadata,
    )


def cleanup_tracked_artifacts(*, older_than_days: int, dry_run: bool = True) -> CleanupResult:
    return cleanup_artifacts(older_than_days=older_than_days, dry_run=dry_run)


__all__ = [
    "append_event",
    "write_json_trace",
    "ensure_artifact_policy_for_session",
    "register_artifact",
    "cleanup_tracked_artifacts",
    "CleanupResult",
]
