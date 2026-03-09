# clinical_computer_use

Supervised, chart-bounded clinical computer-use agent harness (Myle-focused), built to support high-variance tasks with explicit safety boundaries and human review.

This repo is intentionally separate from `GP_Automation`.

## Current scope

- deterministic kernel for browser bootstrap/login/patient bind
- chart-bounded navigation and recovery primitives
- supervised model-guided observation and constrained in-chart actions
- trace + screenshot capture per run
- draft-only / non-finalization posture

## Build direction

The active build coordination document is:

- [BLUEPRINT.md](BLUEPRINT.md)

That blueprint is the source of truth for:

- architecture and invariants
- stage ordering and gates
- completion and safety model
- regression/evaluation priorities

## Notes

- This project handles PHI-bearing workflows. Treat traces/screenshots/artifacts as sensitive outputs.
- No autonomous finalization (submit/sign/fax/send/bill) in current posture.
