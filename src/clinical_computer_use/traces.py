"""
Trace and artifact writers.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .runtime.artifact_policy import append_artifact_manifest, ensure_artifact_policy
from .session import SessionContext


def write_json_trace(session: SessionContext, filename: str, payload: dict[str, Any]) -> Path:
    ensure_artifact_policy(session)
    path = session.trace_dir / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    append_artifact_manifest(
        session,
        artifact_type="trace_json",
        path=path,
        metadata={"filename": filename},
    )
    return path


def append_event(session: SessionContext, event_type: str, payload: dict[str, Any]) -> Path:
    ensure_artifact_policy(session)
    path = session.trace_dir / "events.jsonl"
    line = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "type": event_type,
        "payload": payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line) + "\n")
    return path
