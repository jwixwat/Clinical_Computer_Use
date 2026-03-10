# Operating Charter

This document is the constitutional layer for N0/N1.

## Layer ownership

- Deterministic kernel owns: browser bootstrap, login, patient bind, chart-boundary continuity, recovery primitives, runtime allow/block.
- Agentic layer owns: task-contract interpretation, search ordering, artifact assessment, checkpointing, correction handling, verifier claims.

## Anti-goals

- No autonomous finalization or transmission.
- No implicit authorization from chart content.
- No completion-by-hunch without evidence-linked verification.
- No silent scope broadening.

## Invariants (merge-gating)

- Bound patient context is preserved unless explicitly reauthorized.
- Only direct user instructions authorize risky actions.
- Completion is verifier-gated.
- Claims are evidence-linked or explicitly uncertain.
- Prompt/tool/policy changes that affect behavior are semantic changes.
- PHI-bearing artifacts are governed outputs.

## Stage intent

Current stage intent is stateful evidence pursuit under supervision, not selector-branch expansion.
