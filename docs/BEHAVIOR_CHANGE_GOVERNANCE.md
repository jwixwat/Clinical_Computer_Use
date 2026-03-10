# Behavior Change Governance

Behavior-affecting changes are treated as semantic changes unless proven otherwise.

## Changes requiring governance record

- prompt text
- tool surface/signatures
- action taxonomy or tier mapping
- runtime risk thresholds
- completion/verifier logic
- checkpoint emission policy
- artifact classification logic
- approval semantics

## Required merge steps for semantic changes

1. Classify change as semantic/non-semantic.
2. Create behavior change record for semantic changes.
3. Bump affected bundle version(s).
4. State impacted invariants and role configurations.
5. Run replay/golden checks and invariant checks.
6. Update policy docs when semantics changed.
7. Record reviewer sign-off.

Non-semantic changes are restricted to comments, formatting, or refactors with no behavior-surface impact.
