"""
Trace and artifact writers.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .session import SessionContext


def write_json_trace(session: SessionContext, filename: str, payload: dict[str, Any]) -> Path:
    path = session.trace_dir / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path


def append_event(session: SessionContext, event_type: str, payload: dict[str, Any]) -> Path:
    path = session.trace_dir / "events.jsonl"
    line = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": event_type,
        "payload": payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line) + "\n")
    return path
