# N2.0 Surface Intake

Status: temporary working intake
Purpose: collect the specific Myle surface facts needed to implement N2.0

Instructions:

- We will fill this incrementally together.
- One screenshot or one surface at a time is fine.
- Use short notes where possible.
- If something is unknown, write `unsure`.

## General Notes

App/Environment: Myle at `https://chmg.medfarsolutions.com/html5/...`
Role/User Type: physician-facing clinical user; exact role label still unspecified
Clinic/Site: Capitol Hill Medical Group appears in booking modal; site variance still unconfirmed
Anything variant-dependent: provider can be switched, but user reports the calendar layout remains the same
Viewer behavior overall:
- patient-bound document rows open a separate external Chrome PDF viewer via `/html5/api/medicalDocuments/downloadFile/...`
- this external viewer is read-only and isomorphic across documents
- patient-bound result rows open an in-chart `result_review` surface, not the same external viewer
- patient-results `[ + ]` opens a write/comment modal and should not be used
Tabs always visible even when inactive?: yes
Any major UI differences across users/sites?: user reports only one calendar layout; broader role/site variance still unconfirmed

## Surface Scope Decision

Surface Count In Scope: pending
Surface Names In Scope: pending
Should `viewer` be one surface or multiple?: pending
If multiple, list them:
Working abstraction notes:
- patient-chart shell is persistent across patient-bound chart sub-surfaces
- `/html5/patients` is a shared route for multiple patient-bound chart sub-surfaces
- chart-local right-rail navigation is the primary within-chart transition mechanism
- top global nav exits patient context and should not be conflated with chart-local transitions
- preferred modeling direction:
  - `patient_chart_shell` as persistent frame concept
  - concrete patient-bound surfaces modeled separately: `medical_summary`, `medical_note`, `patient_documents`, `patient_results`, `patient_medication`, `result_review`
  - external read-only viewer modeled separately as `document_viewer_external`
- shared right-rail container observed:
  - `<ul class="vnav"> ... <a data-cy="patientTab-*"> ... </a> ... </ul>`
- observed chart-local right-rail members:
  - `patientTab-appointment`
  - `patientTab-history`
  - `patientTab-documents`
  - `patientTab-profile`
  - `patientTab-results`
  - `patientTab-reporting`
  - `patientTab-medication`
  - `patientTab-medicalsummary`

## Surface Worksheet

### Surface 1

Surface: calendar
Screenshot: central schedule/system view screenshot provided in thread; additional screenshots show booking modal opened from tile click and collapsed-left-pane variant
URL / Route Fragment: `https://chmg.medfarsolutions.com/html5/calendar`
Top-level / Nested / Modal / Viewer: top-level system view
Chart-bounded: no
Patient-bounded: no
Read-only / Draft-like / Mixed: mixed
Primary purpose of this surface: global schedule and patient-entry workspace; user can review schedule, search patients, open patient charts, or open appointment booking details

How do I know I am on this surface?
Primary selector(s):
- active nav tab: `<li class="active CalendarMenuLabel" data-cy="nav-tab-calendar"><a href="/html5/calendar">Calendar</a></li>`
- patient search input: `<input data-cy="sidebar-patient-search" type="text" id="__patientSearchField" placeholder="Search" value="">`
- day button: `<button class="button  cancel push-right-5 active" data-cy="calendar-onDay-button">Day</button>`
- week button: `<button class="button cancel push-right-5 " data-cy="calendar-onWeek-button">Week</button>`
- next date button: `<button data-cy="calendar-next-button" class="btn btn-primary">&gt;</button>`
Secondary selector(s):
- appointment name link inside schedule tile: `<a class="redirect-patient"> ...patient name... </a>`
- left-search dropdown patient result example: `<div tabindex="0" data-cy="sidebar-patient-0" class="sidebar-item"> ... </div>`
- mini-calendar day link example: `<a tabindex="-1" class="k-link" href="#" data-value="2026/2/11" title="Wednesday, March 11, 2026">11</a>`
- mini-calendar month label example: `<a href="#" role="button" aria-live="assertive" aria-atomic="true" class="k-link k-nav-fast" aria-disabled="false">March 2026</a>`
- collapsible left-pane handle: `<div class="aside-handle"><div class="slide-menu-icon blue"><span></span><span></span><span></span></div></div>`
- month button: `<button class="button cancel " data-cy="calendar-onMonth-button">Month</button>`
Heading text / selector:
- no single page heading identified yet
- visible anchors include Day/Week/Month controls, top date navigator, and provider/day schedule header
Unique anchors:
- time-grid schedule is always present even when no patients are booked
- left patient search/sidebar
- mini month calendar in left sidebar
- Day/Week/Month controls at top-left of main pane
- active top navigation tab is `CALENDAR`
- schedule grid container includes `.k-scheduler-content` and event nodes like `.k-event`
Empty-state anchors:
- user reports the schedule grid remains visible even when there are no scheduled patients
Loading-state anchors:
- unknown
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: none persistent at surface level
Patient ID / MRN selector: none persistent at surface level
DOB selector: none persistent at surface level
Is patient identity always visible?: no
If not, when is it hidden?: this is not a patient chart; patient names may appear in appointment tiles or search results, but there is no persistent bound-patient header
Anything that could mislead identity verification?: yes; visible patient names inside tiles/search results must not be treated as patient-bound context

How to navigate to this surface
Usually reached from: top navigation; likely post-login fundamental landing/system workspace for this role
Click path: top nav `CALENDAR`
Selector for tab/button/link to reach it: `li[data-cy="nav-tab-calendar"] a[href="/html5/calendar"]`
Does it open in same page, same tab, modal, or new tab?: same page/route transition

Valid next surfaces from here
Next surface 1: chart_home
How: click patient name directly inside appointment tile
Selector: appointment link example `<a class="redirect-patient"> ...patient name... </a>`
Next surface 2: chart_home
How: type patient identifier in left search field, then click a specific patient from the dropdown list
Selector: search input `input[data-cy="sidebar-patient-search"]`, then dropdown result like `div[data-cy='sidebar-patient-0'].sidebar-item`
Next surface 3: booking modal or booking detail surface
How: click more generally on an appointment tile rather than directly on patient name
Selector: event tile containers such as `.k-event` containing child `[data-role='cdevent']`

Can this surface be confused with another one?
Possible confusion with:
- other top-level system views such as Documents or Results
- booking modal opened on top of calendar
Why confusing:
- top horizontal system bar is always visible across chart and non-chart contexts
- booking modal overlays calendar rather than fully replacing context
What reliably distinguishes it:
- route `/html5/calendar`
- active `data-cy="nav-tab-calendar"`
- schedule time-grid plus Day/Week/Month controls
- left patient search/sidebar plus mini month calendar

Known ambiguity / edge cases
Same URL as another surface?: no; user reports the route is reliably distinct from Documents and patient chart routes
Inactive tabs still rendered?: yes
Modal overlays another surface?: yes; booking view opens as an overlay/modal on top of calendar when tile body is clicked
Empty state looks different?: appointment content may be empty, but the grid still exists
Role-specific variation?: user reports a single calendar layout; broader variance still unconfirmed
Other notes:
- changing date or interacting within calendar does not change the route
- switching Day/Week/Month appears to change page state, not route
- left sidebar can collapse via handle without changing the underlying surface identity
- top navigation remains visible even after entering a patient chart
- top provider/day header appears visually but user could not find a stable inspectable selector for it

Anything unsafe or important for runtime:
- this is a high-risk source of false patient binding because patient names are visible before any chart is opened
- click target specificity matters: patient-name click opens chart; general appointment-tile click opens booking modal instead
- calendar should be classified as non-chart, non-patient surface despite containing patient references
- booking modal is present in product behavior but currently considered out of scope for N2.0 interaction

### Surface 2

Surface: chart_home
Screenshot: patient chart first-view screenshot provided in thread
URL / Route Fragment: `https://chmg.medfarsolutions.com/html5/patients`
Top-level / Nested / Modal / Viewer: patient-bound chart root surface / canonical first patient chart view
Chart-bounded: yes
Patient-bounded: yes
Read-only / Draft-like / Mixed: read-only at first hierarchy
Primary purpose of this surface: canonical patient-bound chart landing surface after opening a patient from calendar or search; summary workspace for demographics, note rail, and chart sub-surface transitions

How do I know I am on this surface?
Primary selector(s):
- patient banner container: `<div class="tb pateint-header" data-cy="patient-banner-container">`
- patient name: `h4[data-cy="patientBanner-patientName"]`
- patient health card number: `[data-cy="patientBanner-nam"]`
- patient DOB: `[data-cy="patientBanner-dob"]`
- patient file number: `[data-cy="patientBanner-fileName"]`
- patient banner buttons container: `[data-cy="patient-banner-buttons"]`
- close button: `button[data-cy="patientBanner-close"]`
Secondary selector(s):
- medical summary sub-surface button: `a[data-cy="patientTab-medicalsummary"]`
- note sub-surface button: `a[data-cy="patientTab-medicalnote"]`
- medications sub-surface button: `a[data-cy="patientTab-medication"]`
- reporting sub-surface button: `a[data-cy="patientTab-reporting"]`
- results sub-surface button: `a[data-cy="patientTab-results"]`
- profile sub-surface button: `a[data-cy="patientTab-profile"]`
- patient documents sub-surface button: `a[data-cy="patientTab-documents"]`
- history sub-surface button: `a[data-cy="patientTab-history"]`
- portal / print / close buttons present in patient banner controls
- patient banner close: `button[data-cy="patientBanner-close"]`
- create new note: `button[data-cy="create-new-note"]`
- note search: `input[data-cy="medicalNote-search"]`
Heading text / selector:
- no single page heading; identity is established by persistent patient banner plus patient chart controls
Unique anchors:
- persistent patient demographic header
- patient-bound action and tab controls in header/right rail
- medical summary layout includes note rail on left plus chart summary panels in center/right
- route remains `/html5/patients` across patient chart sub-surfaces
- chart-local right-rail navigation is always present regardless of which patient-bound sub-surface is active
Empty-state anchors:
- unknown for entire surface; individual sections may be empty
Loading-state anchors:
- unknown
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: `h4[data-cy="patientBanner-patientName"]`
Patient ID / MRN selector:
- health card: `[data-cy="patientBanner-nam"]`
- file number: `[data-cy="patientBanner-fileName"]`
DOB selector: `[data-cy="patientBanner-dob"]`
Is patient identity always visible?: yes, user reports patient demographic header is constant/invariable for chart views
If not, when is it hidden?: not hidden at this hierarchy based on current information
Anything that could mislead identity verification?: top horizontal nav remains visible and can leave patient context entirely; route `/html5/patients` itself is not sufficient to distinguish all patient sub-surfaces without local anchors

How to navigate to this surface
Usually reached from: calendar appointment patient-name click or calendar left-search patient selection
Click path: from system surface into patient chart
Selector for tab/button/link to reach it: no single route button; opened via patient-opening actions from other surfaces
Does it open in same page, same tab, modal, or new tab?: same tab

Valid next surfaces from here
Next surface 1: medical_summary
How: click chart medical summary control
Selector: `a[data-cy="patientTab-medicalsummary"]`
Next surface 2: medical_note
How: click note control or select/open note from note rail
Selector: `a[data-cy="patientTab-medicalnote"]`; note rail row selectors documented below
Next surface 3: patient_documents / patient_results / patient_medication / patient_profile / patient_reporting / patient_history
How: click chart-specific sub-surface controls
Selector:
- `a[data-cy="patientTab-documents"]`
- `a[data-cy="patientTab-results"]`
- `a[data-cy="patientTab-medication"]`
- `a[data-cy="patientTab-profile"]`
- `a[data-cy="patientTab-reporting"]`
- `a[data-cy="patientTab-history"]`

Can this surface be confused with another one?
Possible confusion with:
- other patient-bound sub-surfaces that share the same `/html5/patients` route
- system-wide top-nav surfaces if relying only on the persistent global nav
Why confusing:
- route is constant/invariable across patient chart sub-surfaces
- global top nav remains visible inside patient chart
- left note rail is not present on all chart sub-surfaces
What reliably distinguishes it:
- persistent patient banner
- presence of patient chart sub-surface buttons
- when specifically on medical summary / note view, left note rail is present
- sub-surface-local anchors are required in addition to route

Known ambiguity / edge cases
Same URL as another surface?: yes; user reports the `/html5/patients` URL is constant across patient chart views/sub-surfaces
Inactive tabs still rendered?: global top nav always rendered; chart sub-surface button rendering state still not fully documented
Modal overlays another surface?: unknown from current evidence
Empty state looks different?: individual chart sections may differ; overall chart shell persists
Role-specific variation?: user reports all charts are the same
Other notes:
- left note rail is present only in medical summary and note view, not in documents/results/other chart sub-surfaces
- left note rail can collapse via `<div class="slide-menu-icon blue d"><div class=""><span></span><span></span><span></span></div></div>`
- top-nav Documents/Results/Rx Renewals/Communications/Calendar leave patient context and open system-wide surfaces
- close button returns to prior patient-chart context if another chart is open; otherwise defaults to calendar
- if no note has been created yet, the vertical chart-local note button may be absent
- summary sections use labels such as:
  - `label.MedicalSummary_medicalItemLabel__MAyez` for `Active Problems`, `Medical History`, `Active Medication`, `Allergies and Intolerances`, `Social Habits`, `Alerts and Special Needs`, `Immunizations`, `Family History`
  - plain `label` observed for `Surgical History`, `Psychiatric History`, `Obstetrical History`

Anything unsafe or important for runtime:
- never infer patient sub-surface identity from route alone
- top-nav system transitions must be treated as chart-exit actions that drop patient-bound context
- note rail presence is a strong local anchor for medical summary / note view only, not for all patient chart sub-surfaces
- writing is not available at this first hierarchy except by entering lower-level note/edit flows; results/reporting may lead to lower writable sub-surfaces later
- chart shell and chart sub-surface should likely be modeled separately

### Surface 3

Surface: medical_summary
Screenshot: summary screenshots provided in thread
URL / Route Fragment: `https://chmg.medfarsolutions.com/html5/patients`
Top-level / Nested / Modal / Viewer: patient-bound chart sub-surface
Chart-bounded: yes
Patient-bounded: yes
Read-only / Draft-like / Mixed: read-only at this hierarchy
Primary purpose of this surface: patient summary overview with note rail plus summary cards for active problems, medication, history, allergies, social habits, immunizations, and related chart facts

How do I know I am on this surface?
Primary selector(s):
- chart-local summary button: `a[data-cy="patientTab-medicalsummary"]`
- note search box: `input[data-cy="medicalNote-search"]`
- create new note button present in note rail: `button[data-cy="create-new-note"]`
- summary labels include `label.MedicalSummary_medicalItemLabel__MAyez`
Secondary selector(s):
- summary labels observed:
  - `Active Problems`
  - `Medical History`
  - `Active Medication`
  - `Surgical History`
  - `Psychiatric History`
  - `Obstetrical History`
  - `Allergies and Intolerances`
  - `Social Habits`
  - `Alerts and Special Needs`
  - `Immunizations`
  - `Family History`
- note rail tabs:
  - `My notes`
  - `Clinic visits`
Heading text / selector:
- no single heading; surface inferred by note rail + summary-card layout
Unique anchors:
- left note rail present
- center/right summary cards present
- patient banner persists
- chart-local right rail persists
Empty-state anchors:
- cards may be individually empty while surface shell persists
Loading-state anchors:
- unknown
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: `h4[data-cy="patientBanner-patientName"]`
Patient ID / MRN selector:
- `[data-cy="patientBanner-nam"]`
- `[data-cy="patientBanner-fileName"]`
DOB selector: `[data-cy="patientBanner-dob"]`
Is patient identity always visible?: yes
If not, when is it hidden?: not at current hierarchy
Anything that could mislead identity verification?: system top nav remains visible and exits chart context if used

How to navigate to this surface
Usually reached from: initial patient-chart landing after opening patient from calendar/search
Click path: click chart-local summary control if not already active
Selector for tab/button/link to reach it: `a[data-cy="patientTab-medicalsummary"]`
Does it open in same page, same tab, modal, or new tab?: same tab

Valid next surfaces from here
Next surface 1: medical_note
How: click note button or open/select note
Selector: `a[data-cy="patientTab-medicalnote"]`
Next surface 2: patient_problem_detail or other summary-detail surface
How: click into summary sections; read-only detail surface at first interaction
Selector: section-specific interaction still to be refined
Next surface 3: patient_documents / patient_results / patient_medication
How: use chart-local right rail
Selector:
- `a[data-cy="patientTab-documents"]`
- `a[data-cy="patientTab-results"]`
- `a[data-cy="patientTab-medication"]`

Can this surface be confused with another one?
Possible confusion with:
- medical_note
- other patient-bound chart sub-surfaces sharing route
Why confusing:
- same patient shell and route
- note rail also present in note view
What reliably distinguishes it:
- summary-card layout with labels such as `Active Problems` and `Active Medication`

Known ambiguity / edge cases
Same URL as another surface?: yes
Inactive tabs still rendered?: chart-local right rail persists
Modal overlays another surface?: unknown
Empty state looks different?: yes at card level, but shell persists
Role-specific variation?: user reports charts are the same
Other notes:
- section `+` interactions first open read-only/detail surfaces rather than direct editing
- note button may be absent if no note exists yet
- summary `+` affordances are not safe generic actions; they can enter write-centric detail flows and should be avoided by current agent policy

Anything unsafe or important for runtime:
- this surface should stay read-only for current intended agent use
- summary section `+` should not be assumed to be a direct write affordance

### Surface 4

Surface: medical_note
Screenshot: note screenshots provided in thread
URL / Route Fragment: `https://chmg.medfarsolutions.com/html5/patients`
Top-level / Nested / Modal / Viewer: patient-bound chart sub-surface
Chart-bounded: yes
Patient-bounded: yes
Read-only / Draft-like / Mixed: mixed
Primary purpose of this surface: patient note viewing and note-entry/editing surface

How do I know I am on this surface?
Primary selector(s):
- chart-local note button: `a[data-cy="patientTab-medicalnote"]`
- modify action: `button[data-cy="medicalNote-modify"]`
- delete action: `button[data-cy="medicalNote-delete"]`
- approve action: `button[data-cy="medicalNote-link-approve-mainButton"]`
Secondary selector(s):
- note-content sections such as `MEDICAL SUMMARY`, `PROGRESS NOTE`, `ASSESSMENT`, `PLAN`
- note actions may include `Modify`, `Approve`, `Save`, `Sign`, `Print`, `Fax`
- representative prior-note list rows use containers like:
  - `<div class="med-note" note-list-item-id="..."> ... </div>`
  - outer wrapper `<div class="pointer"><div class="med-note" ...> ... </div></div>`
- opened note blocks use containers like:
  - `<div class="note-block medical-note-block"> ... </div>`
  - `<div class="note-block-header"> ... </div>`
  - `<div class="patient-note"> ... </div>`
- observed stable opened-note content anchors include:
  - `[data-cy="medicalNote-reason"]`
  - `[data-cy="medicalNote-history"]`
  - `[data-cy="medicalNote-exam"]`
  - `[data-cy="medicalNote-followupPlan"]`
- observed action-oriented anchors that may appear inside notes and should not be used for read-only evidence pursuit include:
  - `[data-cy="medicalNote-add-reason"]`
  - `[data-cy="medicalNote-add-history"]`
  - `[data-cy="medicalNote-add-exam"]`
  - `[data-cy="medicalNote-add-followupPlan"]`
  - `[data-cy="communicationsSection-links"]`
  - `[data-cy="privateBillSection-billSection"]`
  - `[data-cy="planActionLinks-sign"]`
  - `[data-cy="planActionLinks-print"]`
Heading text / selector:
- note title/date/provider header appears at top of note content
Unique anchors:
- note content dominates center pane
- left note rail remains present
- note-specific actions at bottom/right of note surface
Empty-state anchors:
- unknown
Loading-state anchors:
- unknown
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: `h4[data-cy="patientBanner-patientName"]`
Patient ID / MRN selector:
- `[data-cy="patientBanner-nam"]`
- `[data-cy="patientBanner-fileName"]`
DOB selector: `[data-cy="patientBanner-dob"]`
Is patient identity always visible?: yes
If not, when is it hidden?: not at current hierarchy
Anything that could mislead identity verification?: surface is patient-bound, but risk comes from local note-finalization actions

How to navigate to this surface
Usually reached from: medical summary note selection or chart-local note button
Click path: select note from note rail or click chart note control
Selector for tab/button/link to reach it: `a[data-cy="patientTab-medicalnote"]`
Does it open in same page, same tab, modal, or new tab?: same tab

Valid next surfaces from here
Next surface 1: note_edit
How: click `Modify`
Selector: `button[data-cy="medicalNote-modify"]`
Next surface 2: medical_summary
How: chart-local summary control
Selector: `a[data-cy="patientTab-medicalsummary"]`
Next surface 3: patient_documents / patient_results / patient_medication
How: chart-local right rail
Selector:
- `a[data-cy="patientTab-documents"]`
- `a[data-cy="patientTab-results"]`
- `a[data-cy="patientTab-medication"]`

Can this surface be confused with another one?
Possible confusion with:
- medical_summary
- note_edit
Why confusing:
- same note rail and patient shell
- note vs edit mode may share most layout
What reliably distinguishes it:
- note-content sections dominate center pane
- presence of `Modify`, `Delete`, `Approve`

Known ambiguity / edge cases
Same URL as another surface?: yes
Inactive tabs still rendered?: chart-local right rail persists
Modal overlays another surface?: unknown
Empty state looks different?: note existence affects surface availability
Role-specific variation?: user reports charts are the same
Other notes:
- `Save` is only available after entering modify/edit mode
- `Delete Note` should never be used
- `Approve` / `Complete` / `Sign` / `Fax` are finalization/risky actions and should never be used in current posture
- `Modify` is the intended route into lower drafting flows
- `Save` in edit mode is allowed as temporary persistence, not finalization
- older prior notes in the left rail open into the same general note-reading layout, but may omit the bottom modify/save/approve bar entirely
- observed read-only prior-note list snippets include `Toenail concern`, `Rx refills`, `Ageing treatment`, `Ultrasound review - call to patient`
- older prior notes can now be anchored in the opened center pane by:
  - `.note-block.medical-note-block`
  - `.note-block-header`
  - `.patient-note`
- old-note read-only viewing appears to use the same broad note layout, with the main distinction being absence of the bottom edit/finalization bar rather than a completely different DOM shape
- read-only old notes may still expose embedded links such as `Sign`, `Print`, `Fax`, billing, communications, or `[+]` add links inside sections; these should remain out of bounds

Anything unsafe or important for runtime:
- `Modify` is allowed as the entry to draft workflows
- `Delete Note` is forbidden
- `Approve` / `Complete` / `Sign` / `Fax` are forbidden
- `Save` is only conditionally available in edit mode and should be treated as temporary persistence, not finalization

### Surface 5

Surface: patient_medication
Screenshot: medication screenshot provided in thread
URL / Route Fragment: `https://chmg.medfarsolutions.com/html5/patients`
Top-level / Nested / Modal / Viewer: patient-bound chart sub-surface
Chart-bounded: yes
Patient-bounded: yes
Read-only / Draft-like / Mixed: mixed
Primary purpose of this surface: patient medication list and medication history table

How do I know I am on this surface?
Primary selector(s):
- `a[data-cy="patientTab-medication"]`
Secondary selector(s):
- heading `Medications`
- medication table/grid dominates center pane
- `Add New Medication` button present
Heading text / selector:
- visible heading `Medications`
Unique anchors:
- medication history/list table
- patient banner persists
Empty-state anchors:
- unknown
Loading-state anchors:
- unknown
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: `h4[data-cy="patientBanner-patientName"]`
Patient ID / MRN selector:
- `[data-cy="patientBanner-nam"]`
- `[data-cy="patientBanner-fileName"]`
DOB selector: `[data-cy="patientBanner-dob"]`
Is patient identity always visible?: yes
If not, when is it hidden?: not at current hierarchy
Anything that could mislead identity verification?: no special ambiguity beyond shared route

How to navigate to this surface
Usually reached from: chart-local medication control
Click path: click medications button in chart-local right rail
Selector for tab/button/link to reach it: `a[data-cy="patientTab-medication"]`
Does it open in same page, same tab, modal, or new tab?: same tab

Valid next surfaces from here
Next surface 1: medication_add_or_edit
How: click `Add New Medication` or update actions
Selector: still to be refined
Next surface 2: medical_summary
How: chart-local summary control
Selector: `a[data-cy="patientTab-medicalsummary"]`
Next surface 3: other patient-bound chart sub-surfaces
How: chart-local right rail
Selector: corresponding `patientTab-*` controls

Can this surface be confused with another one?
Possible confusion with:
- system-wide medication-related documents
- other patient table/list sub-surfaces
Why confusing:
- shared patient route and shell
What reliably distinguishes it:
- heading `Medications`
- medication table structure

Known ambiguity / edge cases
Same URL as another surface?: yes
Inactive tabs still rendered?: chart-local right rail persists
Modal overlays another surface?: unknown
Empty state looks different?: unknown
Role-specific variation?: user reports charts are the same
Other notes:
- despite current agent policy to avoid medication editing, the surface contains `Add New Medication`, so it is operationally mixed
- `Add New Medication` opens a write-centric sub-surface and should not be used for current intended tasks

Anything unsafe or important for runtime:
- should not be treated as read-only in a generic sense because it exposes add/edit affordances
- current intended agent use should avoid medication add/remove flows

### Surface 6

Surface: patient_documents
Screenshot: patient documents screenshot provided in thread
URL / Route Fragment: `https://chmg.medfarsolutions.com/html5/patients`
Top-level / Nested / Modal / Viewer: patient-bound chart sub-surface
Chart-bounded: yes
Patient-bounded: yes
Read-only / Draft-like / Mixed: mixed
Primary purpose of this surface: patient-specific document list and document-management workspace

How do I know I am on this surface?
Primary selector(s):
- `a[data-cy="patientTab-documents"]`
Secondary selector(s):
- heading `All Documents`
- left document category rail
- documents/results-style table with patient banner still visible
Heading text / selector:
- visible heading `All Documents`
Unique anchors:
- left document taxonomy/category rail
- patient banner persists
- patient document table/grid
Empty-state anchors:
- unknown
Loading-state anchors:
- unknown
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: `h4[data-cy="patientBanner-patientName"]`
Patient ID / MRN selector:
- `[data-cy="patientBanner-nam"]`
- `[data-cy="patientBanner-fileName"]`
DOB selector: `[data-cy="patientBanner-dob"]`
Is patient identity always visible?: yes
If not, when is it hidden?: not at current hierarchy
Anything that could mislead identity verification?: must be distinguished from top-nav system-wide Documents by checking patient banner presence

How to navigate to this surface
Usually reached from: chart-local documents control
Click path: click received-documents button in chart-local right rail
Selector for tab/button/link to reach it: `a[data-cy="patientTab-documents"]`
Does it open in same page, same tab, modal, or new tab?: same tab

Valid next surfaces from here
Next surface 1: document_viewer_external
How: click a document row anywhere except the far-left checkbox
Selector: representative document row `.myle-table-row`
Next surface 2: medical_summary
How: chart-local summary control
Selector: `a[data-cy="patientTab-medicalsummary"]`
Next surface 3: other patient-bound chart sub-surfaces
How: chart-local right rail
Selector: corresponding `patientTab-*` controls

Can this surface be confused with another one?
Possible confusion with:
- system-wide documents
- patient results
Why confusing:
- tables in both system and patient document contexts
- shared route for patient sub-surfaces
What reliably distinguishes it:
- patient banner visible
- heading `All Documents`
- left document category rail

Known ambiguity / edge cases
Same URL as another surface?: yes
Inactive tabs still rendered?: chart-local right rail persists
Modal overlays another surface?: unknown
Empty state looks different?: unknown
Role-specific variation?: user reports charts are the same
Other notes:
- document rows are represented by `.myle-table-row`
- clicking anywhere on the row except the far-left checkbox opens the external document viewer
- all observed patient documents open in the same external PDF viewer
- document action column contains high-risk affordances such as `Approve`, `Tasks`, and `Annotate`; these should be policy-gated later

Anything unsafe or important for runtime:
- surface is patient-bound and likely central to form/document pursuit
- contains action affordances like approve/task/annotate; these should be policy-gated later
- row-open is the admissible read path; action-column interactions are not

### Surface 7

Surface: document_viewer_external
Screenshot: external Chrome PDF viewer screenshots provided in thread
URL / Route Fragment: `https://chmg.medfarsolutions.com/html5/api/medicalDocuments/downloadFile/...`
Top-level / Nested / Modal / Viewer: external viewer / separate browser tab or window
Chart-bounded: chart-originated, but no longer rendered inside chart shell
Patient-bounded: no visible patient-bound anchors; identity should be carried by provenance from the originating patient document row
Read-only / Draft-like / Mixed: read-only
Primary purpose of this surface: safe read-only viewing of patient document PDF contents

How do I know I am on this surface?
Primary selector(s):
- route prefix `/html5/api/medicalDocuments/downloadFile/`
- browser PDF plugin embed:
  - `<embed id="plugin" type="application/x-google-chrome-pdf" ...>`
Secondary selector(s):
- Chrome PDF toolbar
- page-thumbnail rail
- PDF page content region
Heading text / selector:
- no app heading; browser title/tab reflects document filename/PDF
Unique anchors:
- Chrome-native PDF viewer UI
- no patient banner
- no chart-local right rail
- no writable chart controls
Empty-state anchors:
- unknown
Loading-state anchors:
- browser PDF loading behavior only
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: none reliable in viewer chrome
Patient ID / MRN selector: none reliable in viewer chrome
DOB selector: none reliable in viewer chrome
Is patient identity always visible?: no
If not, when is it hidden?: always hidden at shell level; identity must be carried by provenance from originating patient document context
Anything that could mislead identity verification?: yes; this is chart-originated but not visually patient-bounded

How to navigate to this surface
Usually reached from: patient-bound documents surface or linked PDF/document inside result review
Click path: click a patient-document row; or click a linked PDF/document in result review
Selector for tab/button/link to reach it: originating document row `.myle-table-row` or linked PDF/document target
Does it open in same page, same tab, modal, or new tab?: separate browser tab/window-like viewer

Valid next surfaces from here
Next surface 1: patient_documents
How: close external viewer and return to originating chart tab
Selector: browser close/back to original tab
Next surface 2: result_review
How: close external viewer and return to originating chart tab
Selector: browser close/back to original tab
Next surface 3:
How:
Selector:

Can this surface be confused with another one?
Possible confusion with:
- in-chart document viewer
- generic browser PDF
Why confusing:
- content is chart-originated but rendered fully outside the patient chart shell
What reliably distinguishes it:
- route prefix `/html5/api/medicalDocuments/downloadFile/`
- Chrome PDF viewer embed/toolbar
- absence of patient banner and chart controls

Known ambiguity / edge cases
Same URL as another surface?: unique document identifiers vary after `/downloadFile/`, but the route family is stable
Inactive tabs still rendered?: not applicable
Modal overlays another surface?: no
Empty state looks different?: unknown
Role-specific variation?: user reports no exceptions; every observed patient document opens this same way
Other notes:
- scrolling and page navigation are allowed
- print and download are forbidden for agent policy
- user reports there do not appear to be non-PDF exceptions

Anything unsafe or important for runtime:
- classify as read-only external viewer
- admissible interactions should be limited to reading, scrolling, and safe page navigation
- print/download should be forbidden
- patient identity must be inherited from the originating artifact context, not inferred from visible viewer chrome

### Surface 8

Surface: patient_results
Screenshot: patient results screenshot provided in thread
URL / Route Fragment: `https://chmg.medfarsolutions.com/html5/patients`
Top-level / Nested / Modal / Viewer: patient-bound chart sub-surface
Chart-bounded: yes
Patient-bounded: yes
Read-only / Draft-like / Mixed: mixed
Primary purpose of this surface: patient-specific results list workspace for locating and opening result review surfaces

How do I know I am on this surface?
Primary selector(s):
- `a[data-cy="patientTab-results"]`
Secondary selector(s):
- heading `Results`
- results table/grid dominates center pane
- patient banner persists
Heading text / selector:
- visible heading `Results`
Unique anchors:
- patient results table/grid
- patient banner present
Empty-state anchors:
- unknown
Loading-state anchors:
- unknown
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: `h4[data-cy="patientBanner-patientName"]`
Patient ID / MRN selector:
- `[data-cy="patientBanner-nam"]`
- `[data-cy="patientBanner-fileName"]`
DOB selector: `[data-cy="patientBanner-dob"]`
Is patient identity always visible?: yes
If not, when is it hidden?: not at current hierarchy
Anything that could mislead identity verification?: must be distinguished from top-nav system-wide Results by checking patient banner presence

How to navigate to this surface
Usually reached from: chart-local results control
Click path: click results button in chart-local right rail
Selector for tab/button/link to reach it: `a[data-cy="patientTab-results"]`
Does it open in same page, same tab, modal, or new tab?: same tab

Valid next surfaces from here
Next surface 1: result_review
How: click a result row anywhere on the row
Selector: representative result row `.myle-table-row`
Next surface 2: medical_summary
How: chart-local summary control
Selector: `a[data-cy="patientTab-medicalsummary"]`
Next surface 3: other patient-bound chart sub-surfaces
How: chart-local right rail
Selector: corresponding `patientTab-*` controls

Can this surface be confused with another one?
Possible confusion with:
- system-wide results
- patient documents
Why confusing:
- both are table/list-heavy
- shared route for patient sub-surfaces
What reliably distinguishes it:
- patient banner visible
- heading `Results`

Known ambiguity / edge cases
Same URL as another surface?: yes
Inactive tabs still rendered?: chart-local right rail persists
Modal overlays another surface?: unknown
Empty state looks different?: unknown
Role-specific variation?: user reports charts are the same
Other notes:
- result rows are represented by `.myle-table-row`
- clicking the row generally opens `result_review`
- row `[ + ]` does not open the result itself; it opens a modal detail/write interaction rather than a full standalone surface
- this modal includes fields like `Details` and `Notes` plus `Submit`
- same exact results-list layout is used for every result type with no observed exceptions

Anything unsafe or important for runtime:
- row `[ + ]` actions are not admissible for current use
- list-row open is the intended read path into result review

### Surface 9

Surface: result_review
Screenshot: result review screenshots provided in thread
URL / Route Fragment: `https://chmg.medfarsolutions.com/html5/patients`
Top-level / Nested / Modal / Viewer: patient-bound chart sub-surface
Chart-bounded: yes
Patient-bounded: yes
Read-only / Draft-like / Mixed: mixed
Primary purpose of this surface: read full clinical result contents while also exposing dangerous workflow and documentation controls

How do I know I am on this surface?
Primary selector(s):
- back link: `<a style="margin: 0px; text-decoration: none;"> Back to Results </a>`
- visible section text `ADDITIONAL INFORMATION`
- visible section text `FULL RESULTS`
- visible text `Result Details`
Secondary selector(s):
- central analyte/results table with columns like `Analysis`, `Results`, `Units`, `REF.`, `FLAG`, `Graph`, `Notes/Actions`
- linked PDF/document near top of center pane, e.g.:
  - `<a id="3E7FB627-7E5F-413E-BD86-5BB0C7A5BD22" style="margin: 0px 15px 0px 0px; text-decoration: none;"> Occult Blood Fecal-20260204171355-1.PDF </a>`
- right documentation panel with note textareas such as:
  - `textarea[id^="lab_note_FollowUp"]`
  - `textarea[id^="lab_note_consult_"]`
  - `textarea[id^="lab_note_requete"]`
  - `textarea[id^="lab_note_Imagerie"]`
  - `textarea[id^="lab_note_Laboratoire"]`
  - `textarea[id^="lab_note_reason"]`
- bottom action buttons such as `Hold`, `File`, `File + Open`, `File + Approve`
Heading text / selector:
- no single page heading, but `Back to Results` plus invariant result-review regions establish identity
Unique anchors:
- left blue back rail
- central full clinical result content
- right documentation/note-writing panel
- bottom workflow action bar
Empty-state anchors:
- unknown
Loading-state anchors:
- unknown
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: `h4[data-cy="patientBanner-patientName"]`
Patient ID / MRN selector:
- `[data-cy="patientBanner-nam"]`
- `[data-cy="patientBanner-fileName"]`
DOB selector: `[data-cy="patientBanner-dob"]`
Is patient identity always visible?: yes
If not, when is it hidden?: not from current evidence
Anything that could mislead identity verification?: the right panel invites chart-writing/documentation actions and should not be treated as part of the safe reading zone

How to navigate to this surface
Usually reached from: patient results list
Click path: click a result row anywhere on the row
Selector for tab/button/link to reach it: representative result row `.myle-table-row`
Does it open in same page, same tab, modal, or new tab?: same tab

Valid next surfaces from here
Next surface 1: patient_results
How: click `Back to Results`
Selector: `<a style="margin: 0px; text-decoration: none;"> Back to Results </a>`
Next surface 2: document_viewer_external
How: click linked PDF/document near top of result review
Selector: linked PDF/document target in center pane
Next surface 3: result_detail_modal
How: click any `[ + ]` detail/comment affordance, including `Result Details [ + ]`
Selector: `[ + ]` links

Can this surface be confused with another one?
Possible confusion with:
- patient_results list
- result_detail_modal
- generic chart workflow page
Why confusing:
- shares same route and patient shell
- contains both read content and write-capable documentation controls
What reliably distinguishes it:
- left `Back to Results` rail
- central full result content
- right documentation panel
- bottom file/hold/approve controls

Known ambiguity / edge cases
Same URL as another surface?: yes
Inactive tabs still rendered?: chart shell persists
Modal overlays another surface?: result-details modal can overlay related result context, but the main review surface itself is not a modal
Empty state looks different?: unknown
Role-specific variation?: user reports same exact result-review layout for every result type
Other notes:
- same layout is used for literally every result reviewed
- clicking linked PDF in result review opens the same external document viewer used by patient documents
- small `[ + ]` controls beside analytes or result-details affordances open the same write/comment modal and should not be used
- right panel is effectively another note-writing/documentation function and should not be used

Anything unsafe or important for runtime:
- safe zone: central read-only result content
- unsafe zones:
  - right documentation panel
  - bottom action bar (`Hold`, `File`, `File + Open`, `File + Approve`)
  - `[ + ]` detail/comment links
- agent should never type into the right panel and never trigger bottom workflow actions
- if this surface is used, policy should constrain interaction to reading/scrolling and safe navigation only

### Surface 10

Surface: result_detail_modal
Screenshot: results modal screenshot provided in thread
URL / Route Fragment: inherits `https://chmg.medfarsolutions.com/html5/patients`
Top-level / Nested / Modal / Viewer: patient-bound modal state over `patient_results`
Chart-bounded: yes
Patient-bounded: yes
Read-only / Draft-like / Mixed: mixed
Primary purpose of this surface: modal detail/note entry over a patient result row

How do I know I am on this surface?
Primary selector(s):
- modal title `Result Details`
Secondary selector(s):
- text inputs/areas for `Details` and `Notes`
- buttons `Cancel` and `Submit`
Heading text / selector:
- visible heading `Result Details`
Unique anchors:
- overlay modal over patient results table
- patient banner still visible behind modal
Empty-state anchors:
- unknown
Loading-state anchors:
- unknown
Error-state anchors:
- unknown

Patient identity on this surface
Patient name selector: `h4[data-cy="patientBanner-patientName"]` in underlying shell
Patient ID / MRN selector:
- `[data-cy="patientBanner-nam"]`
- `[data-cy="patientBanner-fileName"]`
DOB selector: `[data-cy="patientBanner-dob"]`
Is patient identity always visible?: yes in underlying shell
If not, when is it hidden?: not from current evidence
Anything that could mislead identity verification?: modal state could be mistaken for standalone surface if overlay context is ignored

How to navigate to this surface
Usually reached from: patient results row action
Click path: click result row `[ + ]`
Selector for tab/button/link to reach it: result-row action link `[ + ]`
Does it open in same page, same tab, modal, or new tab?: modal

Valid next surfaces from here
Next surface 1: patient_results
How: cancel/close modal
Selector: `Cancel` or modal close
Next surface 2: submitted result workflow state
How: click `Submit`
Selector: `Submit`

Can this surface be confused with another one?
Possible confusion with:
- full patient result detail screen
- generic modal
Why confusing:
- appears above the results table rather than on a distinct route
What reliably distinguishes it:
- title `Result Details`
- overlay form fields `Details` and `Notes`

Known ambiguity / edge cases
Same URL as another surface?: yes
Inactive tabs still rendered?: underlying chart shell persists
Modal overlays another surface?: yes
Empty state looks different?: not applicable
Role-specific variation?: unknown
Other notes:
- this is a write-capable modal and should not be used for current intended tasks
- every results `[ + ]` interaction appears to open this same workflow/comments modal and never the true clinical result view

Anything unsafe or important for runtime:
- treat as write-capable/risk boundary surface
- should be blocked or checkpointed for current use cases

## Cross-Surface Transition Notes

calendar -> patient chart:
- click patient name inside appointment tile opens patient chart
- typing a patient identifier in the left search pane and selecting a dropdown result also opens patient chart
patient chart home -> documents:
patient chart home -> results:
documents -> viewer:
- click patient-document row anywhere except the far-left checkbox
- opens separate external read-only Chrome PDF viewer under `/html5/api/medicalDocuments/downloadFile/...`
viewer -> documents:
- close external viewer/tab/window and return to originating patient documents tab
results -> result detail/viewer:
- clicking a result row opens `result_review`
- clicking `[ + ]` opens `result_detail_modal` only and should not be used
result detail/viewer -> results:
- `Back to Results` returns from `result_review` to `patient_results`
forms index -> form draft:
form draft -> forms index:
Any transition that is unreliable:
Any transition that changes patient context:
- calendar to patient chart establishes patient context
Any transition that hides patient identity:
- booking modal behavior still needs classification; it shows patient details but may not represent chart context

## Annotated Screenshot Index

Screenshot 1:
Surface: calendar
What proves the surface:
- active `CALENDAR` nav tab
- Day/Week/Month controls
- schedule grid
- left search/sidebar
Where patient identity is:
- only inside appointment tiles; not in persistent bound-patient header
What it could be confused with:
- other top-level system views if only the top bar is visible

Screenshot 2:
Surface: booking modal opened from calendar appointment tile
What proves the surface:
- modal/overlay title `Booking`
- opened from general appointment-tile click rather than patient-name click
Where patient identity is:
- visible in modal content
What it could be confused with:
- chart-bound patient surface unless classified separately
Notes:
- user does not expect the agent to need to interact with this view for current N2.0 goals; treat as deferred modal state for now

Screenshot 3:
Surface: calendar with collapsed left sidebar
What proves the surface:
- same `/html5/calendar` route and active calendar nav
- same schedule grid and day controls
- collapsed sidebar handle still visible
Where patient identity is:
- only inside appointment tiles
What it could be confused with:
- variant state of calendar rather than separate surface

Screenshot 4:
Surface: patient chart home or patient chart primary workspace
What proves the surface:
- route reported as `/html5/patients`
- persistent patient demographic/header region
- chart-specific panels and patient-scoped controls
Where patient identity is:
- persistent top patient header
What it could be confused with:
- other patient-bound chart tabs/surfaces; needs its own entry later

Screenshot 5:
Surface: chart_home
What proves the surface:
- route `/html5/patients`
- persistent patient banner container
- patient-specific tab controls
- medical-summary style content blocks and left note rail
Where patient identity is:
- patient banner header at top of chart
What it could be confused with:
- other patient-bound sub-surfaces sharing the same route

Screenshot 6:
Surface: medical_summary
What proves the surface:
- left note rail present
- summary cards such as `ACTIVE PROBLEMS`, `ACTIVE MEDICATION`, `SOCIAL HABITS`
- patient banner and chart-local right rail both present
Where patient identity is:
- patient banner header at top
What it could be confused with:
- generic chart shell unless summary-card anchors are checked

Screenshot 7:
Surface: medical_note
What proves the surface:
- note content dominates center pane
- note sections like `MEDICAL SUMMARY`, `PROGRESS NOTE`, `ASSESSMENT`, `PLAN`
- note actions such as `Modify`, `Approve`, and sometimes `Sign` / `Print` / `Fax`
Where patient identity is:
- patient banner header at top
What it could be confused with:
- medical_summary if only left rail and banner are checked

Screenshot 8:
Surface: patient_medication
What proves the surface:
- heading `Medications`
- medication table/grid dominates center pane
- patient banner persists
Where patient identity is:
- patient banner header at top
What it could be confused with:
- other patient list-style chart sub-surfaces if heading is ignored

Screenshot 9:
Surface: patient_problem_detail or patient_medical_summary_detail
What proves the surface:
- heading `Medical Summary : Problems and Diagnoses`
- left-side problem list
- detailed problem/diagnosis content in center pane
Where patient identity is:
- patient banner header at top
What it could be confused with:
- generic medical summary unless detail heading is checked

Screenshot 10:
Surface: patient_documents
What proves the surface:
- heading `All Documents`
- patient-bound documents table plus left category rail
- patient banner persists
Where patient identity is:
- patient banner header at top
What it could be confused with:
- system-wide documents if patient banner is not checked

Screenshot 11:
Surface: document_viewer_external
What proves the surface:
- separate browser PDF viewer
- route family `/html5/api/medicalDocuments/downloadFile/...`
- Chrome PDF toolbar and thumbnail rail
Where patient identity is:
- not visible as chart shell/banner; must be carried from provenance
What it could be confused with:
- in-chart viewer if origin tab is ignored

Screenshot 12:
Surface: patient_results
What proves the surface:
- heading `Results`
- results table/grid plus patient banner
Where patient identity is:
- patient banner header at top
What it could be confused with:
- system-wide results if patient banner is not checked

Screenshot 13:
Surface: result_review
What proves the surface:
- `Back to Results`
- invariant center result content region
- invariant right documentation panel
- invariant bottom action bar
Where patient identity is:
- patient banner header at top
What it could be confused with:
- generic result workflow page unless both the central review area and right documentation panel are checked

Screenshot 14:
Surface: result_detail_modal
What proves the surface:
- write/comment modal reached from results `[ + ]`
- not the full result-reading path
Where patient identity is:
- underlying patient banner remains in shell context
What it could be confused with:
- true result-reading surface if only the words `Result Details` are checked

## Open Questions / Unsure Areas

1. `profile` and `history` will be treated as deferred ancillary surfaces unless later needed for runtime guardrails.
2. If there are any additional chart-local sub-surfaces beyond the current in-scope set that must be marked `known but unsupported`, list them; otherwise the present scope is sufficient for N2.0 intake.
