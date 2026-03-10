# PHI Fixture And Replay Policy

This policy governs de-identified replay fixtures. It is separate from live artifact retention policy.

## Workflow

1. Select source run representing a real failure mode.
2. Copy into isolated de-identification workspace outside live execution path.
3. Apply transformation spec:
   - redact names, MRNs, DOB, contacts, addresses
   - scrub identifiers from filenames and metadata
   - apply consistent date shifting if temporal structure matters
   - preserve artifact-class and failure dynamics
4. Produce de-identification manifest of transformed fields.
5. Perform secondary review for residual PHI.
6. Promote to replay corpus only after review pass.

## Sign-off

- Clinical semantics sign-off.
- Fixture curator/repo maintainer sign-off.

If a single operator performs both roles, two separate documented passes are required.
