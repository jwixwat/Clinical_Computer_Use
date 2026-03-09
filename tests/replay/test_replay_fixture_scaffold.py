from __future__ import annotations

import json
from pathlib import Path


def test_redacted_replay_fixture_loads() -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "redacted" / "sample_replay_event.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert payload["task_name"] == "insurance_form_draft"
    assert payload["event"]["type"] == "checkpoint"

