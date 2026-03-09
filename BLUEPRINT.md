# Clinical Computer Use Agent - Next Build Coordination

This document coordinates the **next build** of `clinical_computer_use` starting from the repo's current state: a working supervised harness with deterministic bootstrap/login/patient binding, chart-bounded safety scaffolding, trace capture, screenshot observation, and a first constrained in-chart action loop.

It is intentionally **non-technical**. There are no code diffs, schemas, or file-by-file implementation details here. Use it to align build order, architectural intent, validation gates, and "don't-break" invariants while you work with the repo agent more autonomously.

This is **not** a plan from project origin. It begins at **time = now** and treats the current deterministic kernel as an asset to preserve, not something to discard.

Complexity key: **S** = contained, **M** = cross-cutting, **L** = heavy robustness / tuning / evaluation.

---

## 1) Architectural README (compressed context)

### Where the repo is now

The repo has already cleared an important threshold: it has shown that a supervised browser harness can safely and repeatably control the Myle environment under explicit guardrails.

The current foundation already demonstrates:

* deterministic browser bootstrap / attach
* deterministic login
* deterministic patient binding from cold start
* chart-bounded continuity after binding
* read-only observation and screenshot capture
* a first constrained in-chart agent loop
* Myle-specific topology and policy guidance
* trace logging and artifact capture

That is a **real foundation**, not a toy. It proves controllability of the environment.

### What the next system must become

The next system should not be "a slightly smarter click loop." It should become a **supervised, chart-bounded, correction-tolerant clinical computer-use agent** that can:

* model the user's actual task rather than pattern-match nearby UI cues
* search the chart as an **evidence workspace**
* distinguish the requested artifact from semantically related but incorrect artifacts
* keep track of what it has already searched, rejected, and verified
* accept human correction mid-run and continue without losing state
* pause exactly at risk boundaries rather than either stopping too early or overshooting into unsafe action
* produce evidence-linked drafts and handoffs rather than unaudited output

### Core mental model

Treat the patient chart as a **bounded evidence workspace**, not as a generic webpage.

The agent should reason primarily over:

* **surfaces**: chart home, Documents, Results, forms/note context, active viewer
* **artifacts**: notes, PDFs, scanned documents, result entries, forms, consult letters, external attachments
* **evidence**: title, date, sender/source, content cues, extracted text, viewer screenshot, provenance
* **state**: current patient, task contract, search ledger, evidence ledger, rejected candidates, pending approvals
* **risk**: read/search/open, draft/edit, save/persist, transmit/finalize

The model should spend its intelligence budget on things like:

* what class of artifact is being sought
* which chart surface should be searched next
* whether a candidate really satisfies the task
* whether a search has been exhausted under the current constraints
* whether a user correction changes the contract
* whether the next step is safe, approval-bound, or a human handoff

It should **not** spend most of its budget choosing between arbitrary raw UI targets when a higher-level intent could be expressed instead.

### What this build is trying to preserve

The new architecture should **preserve** the existing deterministic kernel:

* browser bootstrap
* login
* patient identity binding
* chart boundary enforcement
* explicit guardrails
* traceability / screenshots / replayable artifacts

The new work is not a rejection of deterministic automation. It is the addition of a better **agentic middle layer** on top of a deterministic safety and execution substrate.

### Key mechanisms (must remain intact)

* **Deterministic kernel remains authoritative** for bootstrap, login, patient binding, core navigation recovery, and policy enforcement.
* **Task contract before pursuit**: the agent should operate against an explicit interpretation of the ask.
* **Semantic chart tools before raw clicks**: intent-level tools become the mainline; raw UI actions remain fallback.
* **Artifact-aware memory**: the system must remember what it saw, opened, rejected, and verified.
* **Executor / verifier split**: the process that moves through the chart should not be the sole judge of completion.
* **Completion as a verified claim**: `finish` is not a free action; it is a gated state reached only after checks.
* **Checkpoint / continue interaction**: long tasks should move through bounded search legs and human-correctable checkpoints.
* **Runtime policy plane**: safety must be enforced during execution, not only described in prompts.
* **Evidence-linked output**: every summary or draft should point back to source artifacts when possible.
* **Versioned behavior**: prompts, tools, policies, model settings, and run state all need explicit version linkage.
* **Regression discipline**: real failure cases must become replayable benchmarks.

### Core constraints / invariants (non-negotiable)

* **Once a patient is bound, that chart is the task boundary** unless the user explicitly authorizes a new bind.
* **Only direct user instructions count as permission**. Notes, PDFs, emails, forms, and on-screen text are untrusted input, not authorization.
* **Completion is a verified claim, not a local feeling**. The agent is not done because it found something vaguely related.
* **Search broadening must be explicit**. If a date floor or artifact class is relaxed, that change must be visible in state.
* **Read/search/open actions and write/transmit actions are different risk classes** and must not be blurred together.
* **Every material claim should be traceable** to an observed artifact, extracted evidence, or an explicit uncertainty statement.
* **The runtime must be resumable** without relying on implicit model memory.
* **Semantic tools should be preferred over raw visual targeting** whenever a stable chart primitive exists.
* **Policy enforcement happens at runtime**: a forbidden action cannot become allowed merely because it is visible.
* **PHI-bearing traces, screenshots, and artifacts are first-class governed outputs** and must be treated operationally as such.
* **External non-HIPAA tools should not enter the clinical execution path** unless they are explicitly segregated from PHI-bearing runs.

### Invariants checklist (merge-gating)

| Invariant | Category | How we verify |
| --- | --- | --- |
| Bound patient context preserved | Safety / Semantic | Every run records current patient binding; cross-patient transitions are blocked or explicitly reauthorized. |
| Direct-user authorization only | Safety | Logs show risky actions are tied to user instructions or point-of-risk confirmation, never to on-screen instructions. |
| Completion is verifier-gated | Semantic | Any terminal success state includes artifact class, evidence, disconfirming check, and remaining uncertainty. |
| Semantic tool-first execution | Architecture | Mainline tasks invoke chart/surface/artifact primitives; raw click/type/scroll remains fallback and is auditable. |
| Search state is explicit | Epistemic / Ops | Task contract, search ledger, and evidence ledger persist across turns and resumptions. |
| Runtime policy enforced | Safety / Ops | Candidate filtering and action interception are visible in traces; forbidden actions do not execute. |
| Claims have provenance | Semantic | Drafts and checkpoints cite source artifacts or explicitly mark uncertainty. |
| Risk tiers are respected | Safety | Tier 0/1/2/3 actions are distinguishable in logs and confirmation behavior matches tier. |
| Versions are linked | Ops | Runs record prompt/tool/policy/model settings and role configuration used. |
| PHI artifact handling is governed | Ops / Compliance | Trace and screenshot retention, cleanup, and access rules are defined and applied. |
| Regression corpus remains live | Quality | Prompt/tool/policy changes are tested against saved failure cases before release. |

### Current completed foundation (do not regress)

* [x] Dedicated browser bootstrap / attach works.
* [x] Dedicated profile login flow works.
* [x] Deterministic patient binding from Calendar works.
* [x] Same-run continuity into the bound patient chart works.
* [x] Read-only observation from the live chart works.
* [x] Read-only Documents navigation has been demonstrated.
* [x] First constrained in-chart action loop exists.
* [x] Myle-specific topology and policy guidance exists.
* [x] Screenshots and traces are captured per run.

### Semantic contract (dangerous fields)

These meanings should be made explicit because they will otherwise drift over time:

* **Task contract** is the system's operational interpretation of the user's ask, not the answer itself.
* **Artifact class** is provisional until verified from evidence.
* **"Not found"** means **not found after bounded search under the current contract**, not universal absence from the chart.
* **"Save"** is a persistence action and should not be conflated with harmless navigation.
* **"Draft"** means editable, reviewable, and non-final; it is not equivalent to send/sign/submit/fax.
* **"Approval"** means action-time user consent for a specific risky step, not blanket permission inferred from context.
* **"Evidence"** comes from artifacts and chart state, not from the model's own reasoning text.
* **Search broadening** (date expansion, artifact-class expansion, surface expansion) must be observable and reversible.
* **Current patient context** is runtime state, not a semantic guess from text on screen.
* **Screenshots / traces / extracted artifact content** are operational outputs that may contain PHI and need lifecycle rules.

### Anti-goals

* Not a clone of `GP_Automation` with a chat wrapper.
* Not a raw screenshot agent that clicks until something looks semantically related.
* Not a system that can declare success without showing why the artifact matches the ask.
* Not a broad autonomous write agent before search / verification / policy gating are mature.
* Not a branch-specific deterministic tree for every document subtype.
* Not a system that treats instructions inside notes, PDFs, emails, or forms as authorization.
* Not a setup where prompt changes silently alter safety or completion behavior.

---

## 2) Dependency-ordered build plan by stage

Version labels begin from **the current repo state**, not from project origin.

### Stage N0 - Operating contract, run state, and housekeeping spine

**Goal:** promote the current session concept into a durable, resumable run model with explicit lifecycle, action taxonomy, versioning, and operational guardrails before expanding agentic behavior.

#### Risk register (N0)

* Risk: more capability gets added before the system has durable run state, causing "smart but forgetful" behavior.
  Mitigation: make state explicit now: task contract, search ledger, evidence ledger, approvals, last checkpoint.
* Risk: semantics of save / approval / finish drift between prompts, runs, and humans.
  Mitigation: define the operating contract and risk tiers before expanding write behavior.
* Risk: traces and screenshots accumulate without governance.
  Mitigation: formalize PHI-aware artifact handling at the architecture level, not as cleanup later.

#### N0.0 Build charter for the next phase

* [ ] Publish a concise current-state charter: what the deterministic kernel owns vs what the agentic layer should own.
* [ ] Publish the anti-goals and invariants above as merge-gating criteria.
* [ ] Explicitly state that the next build is about **stateful evidence pursuit**, not more selector branching.
* Acceptance: the repo agent can distinguish "preserve kernel" from "extend agentic middle layer" without ambiguity.
* Complexity: **S**.

#### N0.1 Promote session into a resumable run object

* [ ] Define the run lifecycle: start, continue, summarize, approve next risky action, stop, archive, resume.
* [ ] Make run-local working memory first-class: task contract, search ledger, evidence ledger, pending approvals, rejected candidates, last checkpoint.
* [ ] Ensure resumptions do not depend on hidden model memory alone.
* Acceptance: a paused run can be resumed by another process or a later turn without losing what the system already searched or rejected.
* Complexity: **M**.

#### N0.2 Action taxonomy and risk ladder

* [ ] Publish a common action taxonomy that separates navigation/search/open from drafting/editing, persistence, and externalization.
* [ ] Define a stable risk ladder to use everywhere:
  * Tier 0 = navigate / search / read / open artifact
  * Tier 1 = draft / edit but unsaved
  * Tier 2 = save / persist chart state
  * Tier 3 = transmit / finalize / sign / fax / send / approve / bill
* [ ] Clarify which tiers are in current scope and which remain out of scope.
* Acceptance: every allowed or blocked action can be categorized consistently before execution.
* Complexity: **S/M**.

#### N0.3 Versioning discipline for agent behavior

* [ ] Link every run to prompt versions, tool surface versions, policy bundle version, model choice, and role-specific operating settings.
* [ ] Record which role configuration was used when different sub-agents or model settings are introduced.
* [ ] Treat prompt changes as semantic changes, not just wording edits.
* Acceptance: behavior drift can be traced to specific prompt/tool/policy/model changes.
* Complexity: **M**.

#### N0.4 PHI-aware operational housekeeping

* [ ] Define retention and cleanup policy for screenshots, traces, extracted text, and other captured artifacts.
* [ ] Define who or what processes may access these artifacts.
* [ ] Define a de-identified fixture / replay policy so regression work does not depend on live PHI.
* [ ] Define explicit rules for what may leave the isolated clinical execution path.
* Acceptance: operational artifact handling is intentional rather than accidental.
* Complexity: **M**.

#### N0.5 Human handoff packet standard

* [ ] Define the standard handoff shape for paused or review-bound tasks.
* [ ] Include: task understanding, current patient context, where the agent looked, what was found, what remains uncertain, what action is next, and whether approval is needed.
* Acceptance: humans receive consistent, short, evidence-linked handoffs rather than arbitrary narrative dumps.
* Complexity: **S/M**.

---

### Stage N1 - Task contract compiler and checkpoint / continue protocol

**Goal:** convert free-text clinical instructions into an explicit operational contract, then let user corrections modify that contract without resetting the run.

#### Risk register (N1)

* Risk: the model continues to act on a vague prompt and chases the first semantically nearby artifact.
  Mitigation: compile a task contract before pursuit.
* Risk: user correction arrives as free text but changes nothing structural.
  Mitigation: compile corrections into state deltas.
* Risk: the run either checkpoints too often or not enough.
  Mitigation: checkpoint only at semantic boundaries and risk edges.

#### N1.0 Task contract fields

* [ ] Define the minimum contract fields for every run:
  * patient target
  * objective type (`find`, `summarize`, `draft`, `annotate`, `fill`, etc.)
  * target artifact class
  * explicitly disallowed artifact classes
  * preferred search surfaces
  * date floor / date constraints
  * evidence requirements
  * completion test
  * approval boundaries
* [ ] Treat missing or ambiguous fields as explicit uncertainty, not silent assumptions.
* Acceptance: the system can represent "find the external firearms form, not a note, Documents first, recent first" as structured task state.
* Complexity: **M**.

#### N1.1 Contract compilation from user intent

* [ ] Add a contract-building step before the agent starts chart pursuit.
* [ ] Make the system state what it believes the task is, what is missing, and what it will treat as non-goals.
* [ ] Keep this compact enough to survive long runs.
* Acceptance: the system starts from a concrete operational interpretation rather than a vague prose prompt.
* Complexity: **M**.

#### N1.2 User correction compiler

* [ ] Accept natural free-text corrections from the user.
* [ ] Translate those into structured state updates such as:
  * reject candidate X
  * mark `chart_note` as disallowed
  * raise Documents above Results
  * add / remove date floor
  * require human review before save
* [ ] Preserve prior valid work rather than resetting from scratch.
* Acceptance: corrections become durable state changes, not just extra chat history.
* Complexity: **M/L**.

#### N1.3 Checkpoint protocol

* [ ] Define a standard checkpoint format with a small number of required fields:
  * what the agent thinks the task is
  * where it looked
  * what it found
  * why it is or is not done
  * the next safest one or two actions
* [ ] Use checkpoints when:
  * a likely candidate is found
  * a preferred surface is exhausted
  * the user correction changes the contract
  * a risky action is next
  * the agent believes the task is complete
* Acceptance: checkpoints are sparse, meaningful, and useful for real supervision.
* Complexity: **M**.

#### N1.4 Autonomy budget and context compaction

* [ ] Define how many low-risk steps the agent may take between checkpoints.
* [ ] Define how run history gets compacted into durable working memory instead of ballooning prompt context.
* [ ] Ensure the summary of prior work is sufficient for continuation and replay.
* Acceptance: long tasks remain coherent without either excessive interruption or context sprawl.
* Complexity: **M/L**.

---

### Stage N2 - Semantic chart workspace and tool layer

**Goal:** shift the model's control surface from arbitrary visible targets toward chart-level and artifact-level intents.

#### Risk register (N2)

* Risk: the agent keeps reasoning in terms of ephemeral element IDs rather than stable clinical concepts.
  Mitigation: introduce semantic chart tools as the mainline interface.
* Risk: selector churn or visual noise continues to dominate behavior.
  Mitigation: expose stable Myle-specific primitives where the topology is already understood.
* Risk: strong existing automation in `GP_Automation` gets ignored.
  Mitigation: reuse stable deterministic capabilities as callable skills instead of rediscovering them through visual clicking.

#### N2.0 Chart surface model

* [ ] Define the agent's internal map of chart surfaces:
  * chart home / summary
  * Documents
  * Results
  * note/forms context
  * active document / viewer
  * patient header / identity region
* [ ] Define allowed transitions and recovery routes between them.
* Acceptance: the agent can talk about chart surfaces as first-class concepts.
* Complexity: **S/M**.

#### N2.1 First semantic tool set

* [ ] Introduce intent-level primitives such as:
  * `get_chart_context`
  * `open_surface(...)`
  * `search_surface(...)`
  * `list_visible_artifacts`
  * `open_artifact(...)`
  * `inspect_open_artifact`
  * `capture_region(...)`
  * `return_to_chart_home`
* [ ] Keep raw click / type / scroll as fallback rather than mainline.
* Acceptance: most read-only chart pursuit can be expressed without the model inventing selectors or arbitrary click chains.
* Complexity: **M/L**.

#### N2.2 Documents and Results as first-class verticals

* [ ] Prioritize Documents and Results as the first robust search surfaces.
* [ ] Give the agent stable ways to enter them, search within them, list visible rows, and open candidates.
* [ ] Teach the agent when to prefer one surface over the other under the contract.
* Acceptance: the agent can deliberately search Documents first, then Results second, rather than bouncing around generically.
* Complexity: **M/L**.

#### N2.3 Recovery primitives and disorientation handling

* [ ] Add deterministic recovery moves for common failure states:
  * return to chart home
  * reopen Documents
  * reopen Results
  * refocus the active viewer
  * revalidate patient identity
* [ ] Prefer these over exploratory clicking when the state is uncertain.
* Acceptance: the agent can recover from disorientation without expanding global navigation or switching patients.
* Complexity: **M**.

#### N2.4 Reuse of stable deterministic skills

* [ ] Identify mature, stable `GP_Automation` capabilities that should become callable chart primitives.
* [ ] Keep them behind the same safety and runtime policy plane.
* [ ] Treat this as giving the agent a better API, not as reverting to macro trees.
* Acceptance: known-stable subflows stop consuming agent reasoning budget unnecessarily.
* Complexity: **M**.

---

### Stage N3 - Artifact registry, evidence ledger, and search memory

**Goal:** give the agent a durable working memory over artifacts and search history so it can continue intelligently and reject false positives without forgetting prior work.

#### Risk register (N3)

* Risk: the agent reopens the same plausible-but-wrong candidate repeatedly.
  Mitigation: artifact registry with reject reasons and reopen awareness.
* Risk: the agent broadens search without realizing it has changed the task.
  Mitigation: explicit search ledger with filters and broadening reasons.
* Risk: outputs cannot be audited back to source artifacts.
  Mitigation: provenance-linked evidence ledger.

#### N3.0 Artifact ontology

* [ ] Define the first-pass artifact taxonomy the agent can reason over, for example:
  * chart note
  * external document
  * scanned form
  * PDF form
  * consult letter
  * discharge summary
  * result artifact
  * built-in form
  * annotation target
* [ ] Allow provisional classification with confidence / uncertainty.
* Acceptance: the system can state "this is probably a chart note" versus "this is likely an external PDF form" in structured state.
* Complexity: **M**.

#### N3.1 Artifact registry

* [ ] Persist candidate entries with fields such as:
  * artifact identifier
  * source surface
  * visible metadata (title, date, sender/source, type cues)
  * whether opened
  * provisional class
  * relevance to current contract
  * reject reason
  * verification status
* [ ] Preserve artifact memory across continuation turns and resumptions.
* Acceptance: inspected candidates become durable objects in the run, not transient screen impressions.
* Complexity: **M/L**.

#### N3.2 Search ledger

* [ ] Persist where the agent searched, in what order, under what constraints.
* [ ] Record queries, date floors, surfaces searched, exhaustion status, and broadening rationale.
* [ ] Record when the agent switches from preferred to fallback surfaces and why.
* Acceptance: the system can explain the search path rather than only the current screen.
* Complexity: **M**.

#### N3.3 Evidence ledger and provenance

* [ ] Store evidence snippets, extracted viewer text, screenshots/crops, and other artifact observations with source linkage.
* [ ] Make every material draft/checkpoint claim point back to one or more artifacts.
* [ ] Distinguish evidence from model interpretation.
* Acceptance: outputs become explainable and reviewable from chart sources.
* Complexity: **M/L**.

#### N3.4 Rejection memory and duplicate control

* [ ] Explicitly track why candidates were rejected.
* [ ] Prevent duplicate reopen loops unless the task contract changes enough to justify reconsideration.
* [ ] Make reconsideration itself explicit in the ledger.
* Acceptance: the agent stops rediscovering the same wrong artifact under the same contract.
* Complexity: **M**.

---

### Stage N4 - Executor / verifier split and hard completion gating

**Goal:** stop premature success by separating chart pursuit from completion judgment and making completion require structured verification.

#### Risk register (N4)

* Risk: the same process that found a candidate is biased toward declaring it sufficient.
  Mitigation: split execution from verification.
* Risk: `finish` remains too cheap and the system stops at "related enough."
  Mitigation: make completion conditional on a contract-aware review.
* Risk: negative evidence is never considered.
  Mitigation: add mandatory falsification / alternative-interpretation checks.

#### N4.0 Role separation

* [ ] Separate at least two cognitive roles:
  * **executor** = chooses the next safe intent/tool call
  * **verifier** = judges whether the found candidate actually satisfies the task
* [ ] They may use the same model family, but they should not share the same prompt responsibilities.
* Acceptance: the run has an explicit verification boundary rather than one loop that both searches and self-certifies.
* Complexity: **M/L**.

#### N4.1 Candidate review schema

* [ ] Require candidate assessment to answer, in structured form:
  * what was requested
  * what artifact was found
  * what class it appears to be
  * what evidence supports that
  * why it might **not** satisfy the request
  * what alternate interpretations were considered
  * what remains uncertain
* [ ] Treat inability to answer these questions as non-completion.
* Acceptance: every strong completion claim is accompanied by an argument, not just a hunch.
* Complexity: **M**.

#### N4.2 Hard finish rules

* [ ] Make `finish` available only when the completion contract is satisfied.
* [ ] Require at least one explicit verification step before terminal success.
* [ ] Disallow completion when higher-probability candidates remain uninspected under the current search plan.
* [ ] Allow alternative terminal states instead of forcing success, such as:
  * verified match found
  * plausible candidate found; human review needed
  * not found after bounded search
  * blocked on ambiguity
  * blocked on risk / approval
* Acceptance: completion becomes a meaningful state transition rather than a generic escape hatch.
* Complexity: **L**.

#### N4.3 Bounded-search semantics

* [ ] Define what it means for a search to be exhausted under the current contract.
* [ ] Require the verifier to state whether preferred surfaces were exhausted before broader fallback claims.
* [ ] Make search broadening visible instead of silently moving the goalposts.
* Acceptance: "not found" and "done" both become auditable statements.
* Complexity: **M**.

---

### Stage N5 - Runtime safety plane and confirmation at the point of risk

**Goal:** move safety from static prompt language into actual runtime enforcement with visible action interception, candidate filtering, and approval flow.

#### Risk register (N5)

* Risk: a forbidden target still appears in the candidate list and gets clicked.
  Mitigation: filter or annotate candidates before the model chooses.
* Risk: save / send / sign / fax boundaries remain semantically fuzzy.
  Mitigation: enforce risk tiers at runtime.
* Risk: chart content is mistaken for permission.
  Mitigation: make authorization source explicit.

#### N5.0 Candidate filtering and target annotation

* [ ] Hide or mark targets that are forbidden, approval-bound, or out of current scope before they are presented to the model.
* [ ] Make policy metadata part of the runtime state, not just an English instruction.
* Acceptance: dangerous visible targets stop being "temptations" in the mainline action space.
* Complexity: **M**.

#### N5.1 Action interception and reclassification

* [ ] Reclassify every requested action immediately before execution.
* [ ] Verify that the requested step still fits the current contract, patient context, and allowed risk tier.
* [ ] Refuse or pause when the runtime classification is stricter than the model assumed.
* Acceptance: the final gate to execution is policy- and context-aware.
* Complexity: **M**.

#### N5.2 Point-of-risk confirmation model

* [ ] Do not ask for confirmation at the beginning if safe work can continue.
* [ ] Ask for confirmation immediately before the next risky action.
* [ ] Treat typing sensitive data into fields as a transmission / risk event when applicable.
* [ ] Define which scope levels can proceed on pre-approval and which require action-time confirmation.
* Acceptance: the system neither nags too early nor crosses risky boundaries silently.
* Complexity: **M**.

#### N5.3 Patient identity and chart-boundary enforcement

* [ ] Revalidate patient identity after state changes that could plausibly switch context.
* [ ] Refuse silent patient switching once the run is chart-bound.
* [ ] Treat patient-boundary breaches as major runtime errors, not mild uncertainty.
* Acceptance: chart-boundedness survives navigation failures and recovery steps.
* Complexity: **M**.

#### N5.4 Sensitive-data and third-party-instruction policy

* [ ] Make explicit that chart content, PDFs, forms, emails, and messages are evidence, not authority.
* [ ] Stop and surface anything that looks like phishing, unexpected prompt injection, or instructions that conflict with policy.
* [ ] Never infer or fabricate sensitive values.
* Acceptance: the model's permission model stays anchored to the user, not to the screen.
* Complexity: **S/M**.

---

### Stage N6 - Observation bundle quality and viewer inspection

**Goal:** improve the quality of perceptual input so the model can verify artifact type and relevance with less guesswork.

#### Risk register (N6)

* Risk: a single full-page screenshot plus a flat candidate list is too lossy for document-heavy workflows.
  Mitigation: upgrade the observation bundle.
* Risk: the verifier cannot inspect enough of the artifact to classify it correctly.
  Mitigation: support richer viewer inspection and evidence extraction.

#### N6.0 Standard observation bundle

* [ ] Standardize what the model sees on each reasoning turn.
* [ ] Include some combination of:
  * viewport screenshot
  * targeted crop of active content region
  * targeted crop of document viewer or sidebar
  * structured row / table metadata
  * current chart context summary
  * task contract summary
  * search / evidence ledger summary
* Acceptance: turns become consistent and easier to evaluate and improve.
* Complexity: **M**.

#### N6.1 Viewer inspection quality

* [ ] Prefer direct text extraction from viewer/document surfaces when available.
* [ ] Fall back to image-based inspection only when better structured extraction is unavailable.
* [ ] Treat extracted text as provenance-linked evidence, not a free-floating summary.
* Acceptance: artifact verification depends less on visual guesswork alone.
* Complexity: **M/L**.

#### N6.2 Original-detail screenshot discipline

* [ ] Use high-fidelity screenshots for computer-use turns when feasible.
* [ ] Only downscale intentionally and in a way that preserves coordinate mapping and inspection usefulness.
* Acceptance: visual reasoning and action targeting are not needlessly degraded by low-quality captures.
* Complexity: **S/M**.

#### N6.3 Context packaging for long runs

* [ ] Ensure the observation bundle contains enough structured state that the model does not need to reconstruct the run from raw history every turn.
* [ ] Keep this packaging compact enough that it does not bloat costs or latency.
* Acceptance: long runs remain both legible and efficient.
* Complexity: **M**.

---

### Stage N7 - First production-relevant vertical slices

**Goal:** prove the new architecture on concrete clinical task classes before widening scope.

#### Risk register (N7)

* Risk: the architecture becomes elegant but unproven on work you actually need.
  Mitigation: build a small number of high-value vertical slices and hold them to measurable standards.
* Risk: write flows expand before search / verification is trustworthy.
  Mitigation: sequence read-only and evidence synthesis first, then draft-only writing, then annotation.

#### N7.0 Read-only artifact pursuit slice

* [ ] Build a reliable slice for finding a requested document/form/artifact in the current patient chart.
* [ ] Require artifact-class-aware completion and evidence-linked handoff.
* [ ] Use this slice to directly attack the current "related note vs target document" failure mode.
* Acceptance: the new system clearly outperforms the current constrained loop on document-finding tasks.
* Complexity: **M/L**.

#### N7.1 Evidence synthesis slice

* [ ] Build a slice that searches for evidence under explicit constraints (for example, after a date floor), gathers relevant artifacts, and produces a cited draft summary or answer.
* [ ] Require provenance for each material statement.
* Acceptance: the system can do bounded chart evidence synthesis without pretending certainty it does not have.
* Complexity: **M/L**.

#### N7.2 Draft-only chart workflow slice

* [ ] Build one narrow drafting workflow that consumes cited evidence and populates a draft output inside the chart.
* [ ] Keep save behavior explicitly classified and reviewed under the risk ladder.
* [ ] Do not expand to send / sign / fax / finalize here.
* Acceptance: the repo proves it can be clinically useful in write-adjacent work without crossing finalization boundaries.
* Complexity: **L**.

#### N7.3 Annotation / form-fill slice

* [ ] Build a constrained annotation or built-in-form slice only after the read/search/verify path is stable.
* [ ] Allow text-box placement / field filling as draft-only work.
* [ ] Stop before certification, signing, faxing, or equivalent final acts.
* Acceptance: the agent can assist with form preparation while preserving explicit human review boundaries.
* Complexity: **L**.

---

### Stage N8 - Replay corpus, evals, and regression discipline

**Goal:** make progress measurable against real clinical failure modes rather than impressions of smoothness.

#### Risk register (N8)

* Risk: improvements in one place quietly worsen completion behavior, safety, or correction recovery elsewhere.
  Mitigation: promote real failure cases into a replayable corpus.
* Risk: the team optimizes for turn count or visual fluency instead of task correctness.
  Mitigation: define the right metrics early.

#### N8.0 Extend trace semantics

* [ ] Extend traces beyond screenshots and generic events to include:
  * task contract snapshots
  * search ledger updates
  * evidence ledger updates
  * candidate rejections
  * verifier decisions
  * approval requests / responses
  * terminal state reason
* Acceptance: runs become suitable for replay, audit, and benchmark extraction.
* Complexity: **M**.

#### N8.1 Real benchmark scenarios

* [ ] Build benchmark tasks from the actual work you care about, including:
  * find an external form when a related note exists
  * search with a date floor and broaden only when justified
  * choose Documents vs Results appropriately
  * recover after "not that one"
  * avoid reopening rejected candidates
  * refuse unsafe patient switching
  * stop correctly at save / send / sign / fax boundaries
* Acceptance: the benchmark set matches your real failure surface rather than generic browser tasks.
* Complexity: **M**.

#### N8.2 Core evaluation metrics

* [ ] Track metrics that actually reflect agent quality, such as:
  * false completion rate
  * artifact-class accuracy
  * correction recovery success
  * duplicate reopen rate
  * policy-violation attempt rate
  * citation / provenance coverage
  * time to useful handoff
  * turn count for comparable workflows
* Acceptance: architectural changes can be judged in a disciplined way.
* Complexity: **M**.

#### N8.3 Replay and golden-run discipline

* [ ] Create a replay harness for saved runs or de-identified equivalents.
* [ ] Establish golden runs / expected behaviors for representative tasks.
* [ ] Require prompt/tool/policy changes to be checked against them before release.
* Acceptance: regressions are caught before they reach live chart work.
* Complexity: **M/L**.

#### N8.4 Human acceptance review

* [ ] Add a lightweight human review process for checkpoint usefulness, handoff quality, and draft usefulness.
* [ ] Distinguish operational acceptability from model self-confidence.
* Acceptance: clinician trust becomes an explicit evaluation dimension.
* Complexity: **S/M**.

---

### Stage N9 - Operational hardening, release discipline, and governance

**Goal:** make the system safe to evolve over time without silent semantic drift, unsafe expansion, or unmanaged PHI-bearing artifacts.

#### Risk register (N9)

* Risk: the clinical execution environment remains more permissive than necessary.
  Mitigation: harden runtime isolation and environment boundaries.
* Risk: multi-role prompting and model changes create invisible behavioral drift.
  Mitigation: formalize release discipline and role governance.
* Risk: autonomy expands without a clear envelope.
  Mitigation: define explicit scope growth gates.

#### N9.0 Browser and runtime hardening

* [ ] Harden the dedicated browser/profile environment:
  * minimize extensions
  * minimize inherited environment
  * constrain allowed domains
  * control download / file exposure behavior
  * isolate the clinical execution surface as much as practical
* Acceptance: the runtime is intentionally narrow and easier to reason about.
* Complexity: **M**.

#### N9.1 Role governance and model operating policy

* [ ] Decide which sub-roles exist long-term (for example: contract compiler, executor, verifier, checkpoint summarizer).
* [ ] Pin their reasoning effort / operating settings intentionally instead of letting them drift.
* [ ] Record these settings in run metadata.
* Acceptance: role behavior is deliberate and reproducible.
* Complexity: **M**.

#### N9.2 Incident taxonomy and rollback discipline

* [ ] Define failure categories such as:
  * false completion
  * patient-boundary breach attempt
  * unsafe action attempt
  * evidence-provenance failure
  * duplicate reopen loop
  * verification collapse
  * runtime disorientation
* [ ] Define rollback triggers and panic-mode degradation behavior.
* Acceptance: operational failures produce systematic learning rather than ad hoc debugging.
* Complexity: **M**.

#### N9.3 Scope-growth governance

* [ ] Define what must be true before widening scope from read-only -> draft-only -> save-enabled -> higher-risk workflows.
* [ ] Prevent convenience-driven scope expansion ahead of evidence.
* [ ] Keep finalization / transmission actions behind explicit future gates.
* Acceptance: autonomy grows by demonstrated reliability, not optimism.
* Complexity: **S/M**.

#### N9.4 Release checklist

* [ ] Bind releases to:
  * regression corpus status
  * prompt/tool/policy version changes
  * safety invariants pass
  * role configuration changes
  * vertical-slice evaluation status
  * PHI artifact handling compliance
* Acceptance: release discipline exists before the system becomes truly useful enough to matter.
* Complexity: **M**.

---

## 3) Validation checkpoints (gates)

These gates are designed to prevent you from widening autonomy before the underlying state, verification, and policy planes are mature.

### Gate to N1 (after N0)

* [ ] Run state is resumable and explicit.
* [ ] Action taxonomy and risk ladder are published and stable.
* [ ] Prompt / tool / policy / model version linkage is recorded per run.
* [ ] PHI-aware artifact handling rules are written down and usable.
* [ ] Human handoff packet format exists.

### Gate to N2 (after N1)

* [ ] Task contract compilation works for real prompts.
* [ ] User corrections produce structured state deltas rather than prompt-only drift.
* [ ] Checkpoint protocol exists and is not too noisy.
* [ ] Context compaction preserves enough information for continuation.

### Gate to N3 (after N2)

* [ ] Documents and Results are accessible through semantic tool primitives.
* [ ] Disorientation recovery primitives exist.
* [ ] Raw click/type/scroll is no longer the conceptual mainline for common read-only tasks.
* [ ] Stable `GP_Automation` capabilities are beginning to appear as reusable skills where appropriate.

### Gate to N4 (after N3)

* [ ] Artifact ontology exists and is being used.
* [ ] Artifact registry and search ledger persist across turns.
* [ ] Evidence ledger links claims to source artifacts.
* [ ] Duplicate reopen control is functioning.

### Gate to N5 (after N4)

* [ ] Executor / verifier separation exists.
* [ ] Candidate review includes a falsification step.
* [ ] `finish` is hard-gated by completion logic.
* [ ] Terminal states distinguish verified success from "needs review" and "not found after bounded search."

### Gate to N6 / N7 (after N5)

* [ ] Candidate filtering and action interception are active at runtime.
* [ ] Risk-tier confirmation behavior works at the point of risk.
* [ ] Patient identity / chart-boundary enforcement is robust.
* [ ] On-screen instructions are never treated as authorization.

### Gate to N8 (after N6 / N7)

* [ ] Observation bundle quality is materially better than full-page screenshot alone.
* [ ] At least one read-only document pursuit slice and one evidence-synthesis or draft-only slice are working under the new architecture.
* [ ] Vertical slices outperform the current constrained loop on the intended task class.

### Gate to N9 / broader use (after N8)

* [ ] Regression corpus and replay harness exist.
* [ ] False completion, correction recovery, provenance coverage, and policy-violation attempt rate are tracked.
* [ ] Prompt/tool/policy changes are tested against saved clinical-like failure cases.
* [ ] Release and rollback discipline exists.
* [ ] PHI-aware operational handling is mature enough for sustained iteration.

---

## 4) Recommended immediate priority order

If you want the shortest path from the current harness to something **materially more useful**, the priority order should be:

1. **N0 + N1**: resumable run state, task contract, correction compiler, checkpoint protocol
2. **N2 + N3**: semantic Documents / Results tools, artifact registry, evidence/search ledger
3. **N4**: verifier-gated completion and hard finish
4. **N5**: runtime safety plane and point-of-risk confirmation
5. **N7**: prove the architecture on one real read-only slice and one real draft-only slice
6. **N8 + N9**: replay corpus, eval discipline, and operational hardening

This order matters.

If you expand drafting or annotation before state, artifact memory, and verification are solid, you will get a more powerful version of the current weakness: an agent that can do more things for the wrong reasons.

---

## 5) One ordering note (why this is the fastest manifold)

The fastest path is **not** to keep adding branch-specific deterministic workflows, and it is **not** to simply make the raw action loop more autonomous.

The fastest path is to front-load:

* explicit run state
* explicit task contract
* semantic chart tools
* artifact/evidence memory
* verifier-gated completion
* runtime policy enforcement

Those pieces change **what the model is allowed to think with**.

Once those are in place, the same underlying environment control will start behaving much more intelligently because the agent will finally have:

* a stable understanding of the task
* memory of what it has already checked
* a concept of artifact classes
* a way to reject false positives without forgetting why
* a harder definition of completion
* a better safety boundary at the point of risk

That is the transition from a promising supervised harness to a genuinely useful, correction-tolerant clinical computer-use agent.
