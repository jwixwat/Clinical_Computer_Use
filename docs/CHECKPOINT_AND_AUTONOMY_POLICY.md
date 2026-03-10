# Checkpoint And Autonomy Policy

## Canonical operational understanding block

Must be emitted at:

- run start
- after correction applied
- checkpoint/handoff boundaries
- approval requests

Block fields:

- interpreted objective
- patient target
- required/acceptable/disallowed artifact classes
- preferred surfaces
- date constraints
- uncertainties/missing fields
- explicit non-goals
- next safest actions

## Autonomy budget (N1)

- max `4` consecutive `T0` task-plane actions
- max `1` consecutive `T1` action
- force boundary if same-surface no-progress reaches `3`

Budget resets on:

- run start / resume
- emitted checkpoint
- correction applied
- approval response
- explicit broadening or restore/recovery

## Checkpoint noise criteria

Noise checkpoint:

- repeats same reason/stage with no semantic delta
- adds no takeover value

Guards:

- no consecutive same-reason/no-delta checkpoints
- max `2` non-risk checkpoints in rolling `6` step window
- checkpoint should include at least one material delta (contract/search/artifact/risk/completion)
