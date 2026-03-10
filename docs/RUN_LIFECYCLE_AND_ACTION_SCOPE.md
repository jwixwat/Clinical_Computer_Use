# Run Lifecycle And Action Scope

## Lifecycle state machine

- `active`: execution may proceed.
- `paused`: waiting on clarification, correction, or approval.
- `stopped`: run leg intentionally halted; resumable.
- `archived`: sealed run; non-resumable by default.
- `purged`: PHI-bearing artifacts removed per policy.

Legal resume states: `active`, `paused`, `stopped`.  
Resume is blocked from `archived` and `purged`.

## Control-plane vs task-plane

- Control-plane actions: `start_run`, `continue_run`, `summarize_run`, `handoff_run`, `stop_run`, `archive_run`, `apply_correction`, `bind_patient_initial`, `restore_surface_for_resume`.
- Task-plane actions are clinical-task execution intents and map to risk tiers.

## Task-plane tier mapping

- `T0`: navigate/search/read/open/list/inspect.
- `T1`: draft/edit unsaved.
- `T2`: save/persist.
- `T3`: transmit/finalize/sign/fax/send/approve/bill.

## N0/N1 execution envelope

- `T0`: allowed within autonomy budget.
- `T1`: allowed only for unsaved draft contexts.
- `T2`: always classified and surfaced; blocked/review-bound by default.
- `T3`: forbidden in N0/N1 execution.
