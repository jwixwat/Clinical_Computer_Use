# N2.0 Surface Model Spec

Status: temporary working spec
Scope boundary: N2.0 only, do not advance into N2.1 tooling

## Intent

N2.0 implements a semantic chart surface model for Myle.

It does not add semantic surface tools, richer action policies, viewer extraction, artifact parsing, or N2.1 behavior. The output is a typed, persisted understanding of where the agent is inside Myle and what kind of chart surface it is currently viewing, with enough structure to support N2.1 safely.

## Goal

Replace the current mostly URL/DOM-heuristic surface inference with a first-class deterministic surface layer that can answer:

- what chart surface is currently active
- whether that surface is chart-bounded
- whether that surface is patient-bounded
- what transitions are valid from that surface
- what surface-specific UI anchors are present
- whether the surface is stable enough for agent reasoning

## In Scope

### 1. Surface ontology

Define canonical Myle surfaces as typed enums/models.

Minimum surface set:

- `calendar`
- `chart_home`
- `documents`
- `results`
- `forms`
- `viewer`
- `unknown`

Sub-surfaces may be added only if they are stable, distinct navigation states supported by evidence from the intake process.

### 2. Surface descriptor model

Add a structured model such as `ChartSurfaceState` with fields in this family:

- `surface_type`
- `surface_confidence`
- `active_url`
- `patient_context_visible`
- `patient_context_matches_intended`
- `surface_heading`
- `surface_anchors`
- `allowed_transitions`
- `is_read_only_like`
- `is_draft_like`
- `is_viewer_like`
- `stability_flags`
- `detection_reasons`

This model must be serializable into run state and traces.

### 3. Surface detection pipeline

Implement a deterministic resolver that combines:

- URL patterns
- stable selectors, ideally `data-cy`
- visible headings
- visible active-tab signals
- patient identity anchors

The resolver must return both:

- inferred surface identity
- evidence/reasons for that inference
- confidence and ambiguity indicators

### 4. Surface registry and topology

Build a Myle-specific topology module that describes:

- canonical surfaces
- surface identifiers and aliases
- expected anchors per surface
- legal transitions between surfaces
- patient-bounded vs non-patient-bounded classification
- chart-bounded vs non-chart-bounded classification

This should live as explicit configuration/data rather than being embedded ad hoc inside flows.

### 5. Harness integration

`PlaywrightHarness` should expose surface-model-aware methods such as:

- `inspect_surface()`
- `assert_surface(expected)`
- `current_surface_state()`

Resume and restore logic should depend on the resolved surface model, not only URL heuristics.

### 6. Run-state integration

Persist the latest resolved surface state into run state/checkpoint artifacts.

Search episodes and related runtime records should reference typed surface identity from the new model.

### 7. Tests

Add tests for:

- URL-only detection
- selector-based overrides
- ambiguity handling
- unknown surface fallback
- legal transition maps
- patient-bounded vs non-patient-bounded classification
- chart-bounded vs non-chart-bounded classification

## Explicit Non-Goals

- No semantic extraction of document/result rows yet
- No artifact parsing
- No richer candidate ranking
- No viewer OCR or deep inspection
- No new autonomous actions beyond using the surface model
- No N2.1 tool-layer work

## Implementation Notes

Expected implementation shape:

- new surface schema/models
- new Myle topology/registry module
- deterministic resolver over browser state plus DOM anchors
- harness integration
- run-state persistence updates
- tests for topology and resolver behavior

Expected evidence source:

- user-provided screenshots
- stable selectors/anchors
- URL fragments where reliable
- user explanation of transition behavior and ambiguity cases

## Open Inputs Required Before Implementation

We still need to collect:

- canonical surface list in actual Myle usage
- stable selectors and distinguishing anchors per surface
- transition map between surfaces
- patient identity anchors
- route/URL fragment behavior
- ambiguity and overlay/modal cases
- decision on surface granularity, especially for viewer/detail states
- role/site/environment variance

The intake for those details lives in `docs/N2_0_SURFACE_INTAKE.md`.
