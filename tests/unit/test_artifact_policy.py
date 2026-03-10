from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from clinical_computer_use.runtime.artifacts import (
    cleanup_tracked_artifacts,
    ensure_artifact_policy_for_session,
    register_artifact,
    write_json_trace,
)
from clinical_computer_use.session import SessionContext


def test_manifest_and_policy_written(monkeypatch, tmp_path) -> None:
    root = tmp_path / "artifact_policy"
    trace_root = root / "traces"
    screenshot_root = root / "screenshots"
    trace_root.mkdir(parents=True, exist_ok=True)
    screenshot_root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("clinical_computer_use.config.TRACE_DIR", trace_root)
    monkeypatch.setattr("clinical_computer_use.config.SCREENSHOT_DIR", screenshot_root)
    monkeypatch.setattr("clinical_computer_use.session.TRACE_DIR", trace_root)
    monkeypatch.setattr("clinical_computer_use.session.SCREENSHOT_DIR", screenshot_root)
    monkeypatch.setattr("clinical_computer_use.runtime.artifact_policy.TRACE_DIR", trace_root)
    monkeypatch.setattr("clinical_computer_use.runtime.artifact_policy.ROOT", root)

    session = SessionContext(task_name="insurance_form_draft", user_prompt="test")
    ensure_artifact_policy_for_session(session)
    write_json_trace(session, "summary.json", {"ok": True})

    screenshot = session.screenshot_dir / "sample.png"
    screenshot.write_text("binary_placeholder", encoding="utf-8")
    register_artifact(session, artifact_type="screenshot", artifact_path=screenshot, metadata={"flow": "test"})

    policy_path = session.trace_dir / "artifact_policy.json"
    manifest_path = session.trace_dir / "artifact_manifest.jsonl"
    assert policy_path.exists()
    assert manifest_path.exists()

    entries = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    types = {entry["artifact_type"] for entry in entries}
    assert "trace_json" in types
    assert "screenshot" in types


def test_cleanup_tracked_artifacts_deletes_old_entries(monkeypatch, tmp_path) -> None:
    root = tmp_path / "artifact_cleanup"
    trace_root = root / "traces"
    trace_root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("clinical_computer_use.runtime.artifact_policy.TRACE_DIR", trace_root)
    monkeypatch.setattr("clinical_computer_use.runtime.artifact_policy.ROOT", root)

    session_dir = trace_root / "session-old"
    session_dir.mkdir(parents=True, exist_ok=True)
    old_file = root / "screenshots" / "session-old" / "old.png"
    old_file.parent.mkdir(parents=True, exist_ok=True)
    old_file.write_text("x", encoding="utf-8")

    old_timestamp = (datetime.now(UTC) - timedelta(days=40)).isoformat().replace("+00:00", "Z")
    manifest_path = session_dir / "artifact_manifest.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "timestamp": old_timestamp,
                "artifact_type": "screenshot",
                "path": str(old_file.resolve()),
                "retention_days": 14,
                "contains_phi": True,
                "policy_version": "phi.v1",
                "metadata": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    dry = cleanup_tracked_artifacts(older_than_days=14, dry_run=True)
    assert dry.eligible_entries == 1
    assert old_file.exists()

    real = cleanup_tracked_artifacts(older_than_days=14, dry_run=False)
    assert real.eligible_entries == 1
    assert not old_file.exists()

