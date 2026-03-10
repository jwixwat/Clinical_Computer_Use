# PHI Artifact Policy

This repository emits run artifacts that may contain PHI, including:

- traces (`traces/<session_id>/...`)
- screenshots (`screenshots/<session_id>/...`)
- run-state snapshots and checkpoints

## Baseline controls

- Every session writes `artifact_policy.json` in `traces/<session_id>/`.
- Every trace JSON and registered screenshot is appended to `artifact_manifest.jsonl`.
- Default retention is `14` days (configurable with `ARTIFACT_RETENTION_DAYS`).
- Export posture is `restricted_internal_only`.

## Cleanup

Use CLI cleanup to delete tracked artifacts by age:

```powershell
python -m clinical_computer_use.main cleanup-artifacts --older-than-days 14
```

Dry run:

```powershell
python -m clinical_computer_use.main cleanup-artifacts --older-than-days 14 --dry-run
```

Cleanup only acts on manifest-tracked paths under repository root.
