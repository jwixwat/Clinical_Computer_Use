# N0/N1 Live Smoke (One Session)

This runbook validates constitutional N0/N1 behavior in one short EMR session.

## Goal

Validate:

- run-state persistence and version/lifecycle artifacts
- correction durability
- continue/resume behavior
- canonical handoff/understanding surface
- lifecycle controls (`stop`, `archive`, blocked continue)
- artifact policy/manifest and cleanup command

## Timebox

20-30 minutes.

## Preconditions

- Run from repo root: `C:\Users\joshu\Workspace\clinical_computer_use`
- Environment has:
  - `OPENAI_API_KEY`
  - `MYLE_USERNAME`
  - `MYLE_PASSWORD`
- Use a safe test patient and a read-only prompt.

## Step 1: Start live run

```powershell
python -m clinical_computer_use.main bind-and-agent-task insurance_form_draft "TEST PATIENT NAME OR ID" "Find an external insurance-related form after 2025-01-01, not a chart note, Documents first. Read-only; do not save/send/sign/fax." --max-steps 4
```

Copy printed session id and set:

```powershell
$session = "PASTE_SESSION_ID_HERE"
```

## Step 2: Run smoke validator helper (steps 3-8)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\n0_n1_live_smoke.ps1 -SessionId $session
```

Optional flags:

- `-SkipContinue` (skip continuation check)
- `-SkipLifecycle` (skip stop/archive checks)
- `-SkipCleanupDryRun` (skip cleanup dry-run)

## Expected pass criteria

1. `run_state.json`, `version_bundle.json`, `lifecycle_state.json`, `artifact_policy.json`, `artifact_manifest.jsonl`, and `events.jsonl` exist.
2. Correction increases `contract_history_count`; disallowed class includes `chart_note`.
3. Continue works pre-archive and emits resume events.
4. Handoff includes `operational_understanding`.
5. Stop/archive transitions are persisted; continue after archive fails.
6. Cleanup dry-run command succeeds.
7. No save/send/sign/fax/finalize action occurs.
