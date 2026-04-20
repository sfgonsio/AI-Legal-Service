# SCREEN: Dashboard
VERSION: 0001

---

## PURPOSE

The Dashboard is the primary operational surface for managing a legal case.

It reflects:
- current case state
- actionable gaps
- forward direction

It is not a static report.

---

## CORE PRINCIPLE — LIVING SYSTEM

The dashboard behaves like an income statement:

- it represents current truth
- it evolves as the case progresses
- it does not preserve prior dashboard layouts as separate screens

Each stage changes the composition of visible objects, not the identity of the dashboard.

---

## SECONDARY VIEW — HISTORICAL CONTEXT

A secondary, unobtrusive tabbed view exists to provide:

- predecessor stage summaries
- progression history
- chain-of-evidence visibility
- chain-of-progress visibility

This functions like a balance sheet:
- historical
- structured
- traceable

The primary UI remains forward-looking.

---

## DASHBOARD PHILOSOPHY

The dashboard is primarily interested in:

- what is true right now
- what is missing right now
- what action should be taken next

The dashboard is not intended to preserve old dashboard presentations once the case has progressed beyond a prior stage.

History belongs in:
- traceability
- audit
- stage summaries
- evidence lineage
- activity records

Not in frozen copies of past dashboard layouts.

---

## PERSISTENT SHELL

The dashboard always contains a stable shell, while internal objects evolve by stage.

### Top Level Buttons

These are interactive and drill down:

- Cases #
- Active #
- New #
- Trial #

### Notes
- Keep Cases
- Keep Active
- Add New
- Change "At Trial" to "Trial"
- Remove Cannon Weapons
- Remove Deployed
- Remove Patterns

---

## CASE TILE

Each case is represented as a tile.

The attorney may arrange tiles spatially.

### Core Fields

- Case Name
- Status
- Case Number
- Jurisdiction

Example:
- Case Name: Mills vs. Polley
- Status: Active
- Jurisdiction: Sacramento County Superior Court

---

## PROGRESS STACK

Displayed vertically and cleanly aligned.

Objects:

- Progress %
- Liability Elements Met %
- Evidentiary Support %
- Remedies Viability %
- Case Strength %

### Interaction Rule
Each is interactive.
When clicked, display:
- description
- algorithm
- supporting rationale

### Placeholder Rule
Until algorithms are tightly controlled:
- display `TBD`
- do not fabricate values
- do not use mock percentages

---

## STAGE GATES

Interactive objects:

- Intake
- Build Case
- Discovery
- Trial
- Resolution
- Closed

### Behavior
- Current stage is visually highlighted
- Completed stages remain accessible
- Future stages are visible but may be restricted
- End of each stage gate is concluded with the legal team and client joining the War Room

### Notes
- Replace "Pleadings" with "Build Case"
- Keep Discovery
- Keep Trial
- Add interactive object labeled "War Room"

---

## CORE OBJECT COUNTS

Displayed in the case tile:

- COAs ## with Coverage = Strong / Moderate / Weak
- Burdens ## with Coverage = Strong / Moderate / Weak
- Remedies ## with Coverage = Strong / Moderate / Weak
- Actors ##
- Evidence Files ##

### Placeholder Rule
Until real calculations are finalized:
- counts may display `TBD`
- coverage may display `TBD`
- no fabricated numbers

### Notes
- Remove weapons count
- Remove critical button
- Remove "2 in War Room"

---

## STAGE-DRIVEN COMPOSITION

The dashboard changes as the case progresses.

### Intake Stage
Primary visible objects include:
- interview
- file upload
- intake completion
- evidence upload status

### Build Case Stage
Primary visible objects include:
- causes of action
- burdens
- remedies
- complaint
- legal authority application to intake content

### Discovery Stage
Primary visible objects include:
- interrogatories
- pleadings
- admissions
- deposition
- evidence mapping to complaint, burdens, and remedies

### Trial Stage
Primary visible objects include:
- trial readiness
- evidentiary posture
- witness / actor readiness
- unresolved burden gaps

### Resolution / Closed
Primary visible objects include:
- outcome summary
- contract satisfaction
- payment / closure state
- archive readiness

---

## DRILL-DOWN MODEL

All interactive dashboard objects follow this progression where applicable:

- LEVEL I
- LEVEL II
- LEVEL III
- RAW DATA

### Rule
The lowest level must preserve traceability to raw evidence, source material, and rationale.

---

## TILE DETAIL — STATUS

### Object
Status

### Purpose
Visual reference that informs the status of the case.

### When clicked
User should see:
- definition of the status
- close control

### Data shown
- New
- Build Case
- Discovery
- Trial
- Resolution
- Closed

### Definitions

#### New
A contract exists, intake interview is incomplete. When contract is complete, the case moves to Build Case.

#### Build Case
Interview is complete. File upload is incomplete, causes of action, burdens, remedies are incomplete, complaint is incomplete.
When file upload, COA, burdens, and remedies are complete, the status moves to Discovery.
Output is a complaint that is filed.

#### Discovery
Build Case is complete and complaint is filed. Interrogatories and deposition are incomplete.
Discovery is complete when discovery videos are mapped to complaint, burdens, and remedies, and Evidence ID# is assigned.
When Discovery is complete, the status moves to Trial.

#### Trial
Discovery is complete. Status persists until a verdict is input into the platform.
Status changes from Trial to Closed upon verdict entry.

#### Resolution
A verdict is entered. Status remains until full contract is satisfied and payment for services is received, at which time the status changes to Resolution.

#### Closed
Account balance = $0 owed. The account is flagged for Archive.

---

## TILE DETAIL — PROGRESS METERS

### Purpose
Visual reference that informs current condition of case relative to the full case and is clickable to drill down into details.

Labels:
- Case Coverage
- Evidence
- Actors

### Interaction
Each label is interactive and exposes:
- description
- algorithm
- supporting details

### Drill-Down Principle
The user goes from highest to lowest level of detail.
The lowest level is raw data to maintain a clear chain of evidence.

### Placeholder Rule
Where calculations are not finalized:
- show `TBD`
- show intended algorithm narrative
- do not fabricate confidence values

---

## CASE COVERAGE

### Level I Description
How comprehensively the case has covered its essential scope—issues, planned tasks, discovery items, and compliance checks—minus penalties for any open critical gaps.

### Inputs
- issuesAddressed / issuesIdentified
- tasksCompleted / tasksPlanned
- discoveryItemsCollected / discoveryItemsRequired
- complianceChecksPassed / complianceChecksRequired
- openCriticalGaps
- gapPenaltyRate

### Level II
For each calculation provide:
- narrative of supporting evidence
- files used in calculation
- file strength indicators:
  - admissibility
  - credibility
  - relevance

---

## EVIDENCE

### Level I Description
Confidence from the raw number of evidence items vs. a target, with modest benefit beyond the target.

### Level I Display
- Files ###
- File type counts by extension

### Level II
List files by selected type with:
- file name
- date
- size
- COA
- burden
- remedy
- relevance score
- admissibility score
- credibility score
- evidentiary value

### Level III
Open raw file and display:
- file name
- file ID
- date
- file size
- full text / raw file
- mappings and rationale
- scoring rationale

---

## ACTORS

### Level I Description
Confidence based on the number of key actors identified vs. a minimum and practical maximum.

### Display
- First Name
- Last Name
- Entity Name
- Alias
- Nickname
- Actor role(s)
- Entity type
- Relationship to other actors

### Factual Involvement
- key events participated in
- timeline relevance
- decision making authority
- knowledge scope
- consistency issues
- produced vs withheld materials
- inconsistencies or admissions
- impeachment material
- incentives
- conflicts
- prior litigation
- public records

---

## STAGE GATE DETAIL — INTAKE

### Purpose
Visual reference that informs completeness and strength of Intake, including interview completion and evidential file upload, with traceability to file-level detail.

### When clicked
User should see:
- Intake definition
- Completion conditions
- Completion % with calculation logic
- drill-down to interview and evidence

### Display
- Intake Status
- Intake Completion %
- Interview completion status
- Evidence upload status

### Placeholder Rule
If calculations are not finalized:
- display `TBD`
- show intended logic only

---

## TRACEABILITY RULE

Every displayed value must be traceable to:
- underlying data
- evidence
- mapped rationale
- raw source where applicable

No black-box metrics are allowed.

---

## ACTIVITY LEDGER / DIKW NOTE

The platform should support a stage-aware, date-stamped, append-only activity history that helps:
- preserve chain of evidence
- show progression
- support continuous improvement
- support DIKW learning from usage

This is a first-class future capability and should align with dashboard history / progression visibility.

---

## DESIGN PRIORITY

1. Clarity
2. Actionability
3. Traceability
4. Minimal clutter
5. Forward momentum

---

## NON-GOALS

- Historical preservation of dashboard layouts as separate screens
- Mock or fabricated data
- Static per-stage dashboards as independent UI artifacts

---

## SUMMARY

The dashboard is:
- one living screen
- stage-aware
- action-oriented
- traceable
- current-state focused
- historically supported through unobtrusive progression tabs

END