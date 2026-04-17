\# program\_FACT\_NORMALIZATION.md



\## 1. Document Purpose



This document defines the authoritative execution contract for `program\_FACT\_NORMALIZATION` in the AI Legal Service Platform.



`program\_FACT\_NORMALIZATION` is the deterministic program responsible for converting governed Source Material into structured, provenance-linked Facts suitable for storage in the Evidence Graph and consumption by downstream programs and agents.



This contract exists so that fact creation is bounded, replayable, auditable, case-isolated, and implementation-ready. It establishes what this Program may read, what it may write, how it must behave under reruns, and how its outputs become authoritative.



If this Program contract conflicts with platform-level system contracts, the platform-level system contracts govern unless revised through approved change control.



---



\## 2. Program Identity



\*\*Program Name:\*\*  

`program\_FACT\_NORMALIZATION`



\*\*Program Class:\*\*  

Deterministic execution module



\*\*Layer:\*\*  

Programs



\*\*Primary Pipeline Role:\*\*  

Source Material → Facts



\*\*Owning Domain:\*\*  

Evidence ingestion and factual normalization



\*\*Execution Mode:\*\*  

Bounded programmatic computation, not freeform agent reasoning



---



\## 3. Purpose



`program\_FACT\_NORMALIZATION` transforms governed Source Material into bounded factual units that are normalized, provenance-linked, and suitable for downstream legal reasoning.



This Program creates the first authoritative layer above raw intake material. It does not decide legal merit, strategy, claim sufficiency, or attorney judgment. Its role is to form defensible Fact objects from supported source material.



This Program exists because the platform must not jump directly from raw interviews, files, transcripts, emails, contracts, or exhibits into legal reasoning. Facts are the required intermediate structure that makes downstream event construction, pattern detection, cause-of-action analysis, damages logic, and attorney review explainable and defensible.



---



\## 4. Scope



\### In Scope



This Program may:



\- read governed Source Material registered to a single case

\- read linked Documents and Fragments associated to that case

\- extract bounded factual assertions materially supported by the source

\- normalize names, dates, times, amounts, units, addresses, identifiers, and references when support exists

\- preserve ambiguity where support is incomplete or contested

\- assign governed fact types

\- score extraction confidence using governed logic

\- flag outputs for human review when thresholds or ambiguity require it

\- write Fact objects and provenance links through governed persistence paths

\- emit deterministic execution records and audit events

\- produce execution summaries and replay-comparison artifacts



\### Out of Scope



This Program must not:



\- make legal conclusions

\- decide liability, causation, damages entitlement, or claim sufficiency

\- infer Causes of Action

\- create Events, Patterns, Signals, Coverage findings, or Strategy outputs as authoritative objects

\- silently resolve contradiction as truth

\- perform broad cross-document legal synthesis beyond bounded fact formation

\- mutate unrelated case records

\- read or write across cases

\- use unregistered tools or uncontrolled network access

\- store unsupported narrative summaries as authoritative Facts



---



\## 5. Trigger Conditions



`program\_FACT\_NORMALIZATION` may run only when all of the following are true:



\- a valid `case\_id` exists

\- a valid `run\_id` exists

\- governed Source Material is registered to that case

\- required ingestion metadata is present

\- the workflow state permits fact normalization

\- the invocation is authorized by lane, role, and tool constraints

\- the input set is case-consistent



\### Allowed Invocation Modes



\- system-triggered after source registration or source capture completion

\- UI-triggered through a governed intake or evidence workflow

\- agent-triggered through an authorized orchestration path

\- rerun-triggered through governed replay, supersession, or correction flows



\### Disallowed Invocation Modes



\- invocation against unregistered raw files

\- invocation without a case boundary

\- invocation against mixed-case source sets

\- invocation in closed, locked, or forbidden workflow states

\- invocation that bypasses audit, provenance, or tool gateway requirements



---



\## 6. Inputs



\### Required Inputs



\#### `case\_id`

\- Type: string

\- Required: yes

\- Description: authoritative case identifier

\- Source of truth: Evidence Graph Case object



\#### `run\_id`

\- Type: string

\- Required: yes

\- Description: governed execution identifier for this run

\- Source of truth: orchestration spine / execution context



\#### `source\_ids`

\- Type: array\[string]

\- Required: yes

\- Description: Source Material objects to normalize

\- Source of truth: Evidence Graph Source Material layer



\#### `workflow\_state`

\- Type: enum

\- Required: yes

\- Description: current state used for entry validation and transition control

\- Source of truth: governed state model



\#### `contract\_version`

\- Type: string

\- Required: yes

\- Description: contract version active at execution

\- Source of truth: governed contract metadata



\### Optional Inputs



\#### `document\_ids`

\- Type: array\[string]

\- Required: no

\- Description: specific document objects within the source scope



\#### `fragment\_ids`

\- Type: array\[string]

\- Required: no

\- Description: specific fragments within the source scope



\#### `normalization\_profile`

\- Type: string

\- Required: no

\- Description: governed configuration profile for extraction and normalization behavior



\#### `replay\_context`

\- Type: object

\- Required: no

\- Description: replay, rerun, or comparison context



\#### `idempotency\_key`

\- Type: string

\- Required: no

\- Description: caller-provided idempotency token where orchestration uses idempotent run protection



\### Input Validation Requirements



Inputs must be validated for:



\- existence

\- case consistency

\- non-empty source scope

\- allowed workflow entry state

\- authorization by lane and role

\- source registration completeness

\- replay compatibility where applicable

\- contract version compatibility

\- profile availability if a profile is provided



If any required validation fails, authoritative execution must not begin.



---



\## 7. Outputs



\### Primary Outputs



\#### Fact objects



Structured, provenance-linked Facts written to the Evidence Graph.



Each authoritative Fact must include at minimum:



\- `fact\_id`

\- `case\_id`

\- `source\_id`

\- `fact\_type`

\- `fact\_text\_normalized`

\- `fact\_status`

\- `confidence\_score`

\- `provenance\_ref`

\- `produced\_by\_program`

\- `run\_id`

\- `contract\_version`

\- `created\_at`



Where available and applicable, each Fact should also include:



\- `document\_id`

\- `fragment\_id`

\- `subject\_entity\_ref`

\- `object\_entity\_ref`

\- `fact\_date\_start`

\- `fact\_date\_end`

\- `fact\_amount`

\- `fact\_unit`

\- `ambiguity\_flag`

\- `review\_required\_flag`



\#### Provenance links



Each Fact must be linked to the source support from which it was formed, including:



\- source linkage

\- document linkage where applicable

\- fragment linkage where applicable

\- producing run linkage

\- program identity linkage



\#### Execution record



A governed execution record must link the output set to the current run and preserve replayability.



\### Secondary Outputs



\#### Normalization summary



The Program must produce a structured execution summary including at minimum:



\- number of sources processed

\- number of documents processed

\- number of fragments processed

\- number of facts created

\- number of facts updated or superseded

\- number of facts flagged for review

\- number of source units skipped

\- number of failures

\- output fingerprint or comparison artifact if implemented



\### Output Authority Rule



Outputs become authoritative only when successfully persisted through governed write paths with required provenance and audit references intact.



No in-memory or temporary output is authoritative.



---



\## 8. Minimal Fact Formation Rules



A Fact created by this Program must satisfy all of the following:



\- it is materially supported by Source Material

\- it is bounded enough to be traceable and reviewable

\- it does not overstate certainty

\- it preserves ambiguity where ambiguity exists

\- it is linked to provenance

\- it is scoped to one case

\- it is representable within the governed Fact schema



\### Examples of valid Fact styles



\- “On or about March 4, 2024, Polley emailed Mills regarding invoice approval.”

\- “Document states that Preferred Gardens paid $18,000 on Invoice 1108.”

\- “Interview source reports that shipment was delayed by approximately two weeks.”



\### Examples of invalid Fact styles



\- “Defendant committed fraud.”

\- “The case clearly proves bad faith.”

\- “Mills was obviously deceived intentionally.”

\- “This establishes liability.”



Those belong to downstream reasoning or attorney judgment, not this Program.



---



\## 9. Read / Write Boundaries



\### Allowed Reads



This Program may read:



\- Case objects needed for scope and permission validation

\- Source Material objects in the active case

\- linked Document objects in the active case

\- linked Fragment objects in the active case

\- governed normalization configuration

\- tool registry references for authorized utilities

\- current workflow state

\- existing Facts for idempotency, deduplication, replay comparison, or supersession checks within the same case



\### Allowed Writes



This Program may write:



\- Fact objects

\- Fact-to-source links

\- Fact-to-document links

\- Fact-to-fragment links

\- provenance records

\- execution records

\- replay-comparison artifacts if modeled

\- audit-linked summary records

\- state transitions explicitly allowed by this contract



\### Prohibited Writes



This Program must not write:



\- canonical entity resolutions as final truth

\- relationship objects as authoritative graph edges, except approved bounded support references if architecture later allows

\- Event objects

\- Signal objects

\- Pattern objects

\- Cause-of-Action objects

\- Coverage objects

\- strategy objects

\- attorney disposition state

\- cross-case references



---



\## 10. Reasoning Model Mapping



\### Upstream Stage Consumed



\- Source Material



\### Downstream Stage Produced



\- Facts



\### Required Intermediates



\- provenance links

\- extraction metadata

\- normalization metadata

\- review flags where applicable



\### Reasoning Rule



This Program must convert source-supported material into bounded Facts without promoting those Facts into Events, Patterns, Causes of Action, Coverage findings, or Strategy.



\### Uncertainty Handling Rule



If ambiguity exists, the Program must do one or more of the following:



\- preserve ambiguity explicitly in the Fact

\- lower confidence appropriately

\- set `review\_required\_flag = true`

\- decline to create the Fact when support is inadequate



The Program must not silently invent certainty.



---



\## 11. Workflow State Mapping



\### Allowed Entry States



\- `source\_capture\_complete`

\- `fact\_normalization\_pending`

\- `fact\_normalization\_in\_progress` for governed resume behavior

\- `fact\_normalization\_requires\_review` for approved rerun/correction behavior



\### In-Progress State



\- `fact\_normalization\_in\_progress`



\### Success State



\- `fact\_normalization\_complete`



\### Failure States



\- `fact\_normalization\_failed`

\- `fact\_normalization\_requires\_review`



\### Allowed Transition Examples



\- `source\_capture\_complete` → `fact\_normalization\_pending`

\- `fact\_normalization\_pending` → `fact\_normalization\_in\_progress`

\- `fact\_normalization\_in\_progress` → `fact\_normalization\_complete`

\- `fact\_normalization\_in\_progress` → `fact\_normalization\_failed`

\- `fact\_normalization\_in\_progress` → `fact\_normalization\_requires\_review`



\### Transition Constraint



This Program must not advance workflow directly to mapping approval, pattern analysis, COA analysis, attorney disposition, or any later-stage review state unless such transition is explicitly defined in the platform state model.



---



\## 12. Determinism Requirements



`program\_FACT\_NORMALIZATION` must be deterministic or deterministically constrained.



\### Determinism Requirements



\- identical governed inputs must produce equivalent outputs or replay-explainable deltas

\- output schema and output ordering rules must be stable

\- fact identity logic must be reproducible or replay-comparable

\- extraction and normalization behavior must depend only on governed inputs and governed configuration

\- contract version and config version must be recorded

\- uncontrolled randomness must not affect authoritative output

\- authoritative persistence must not depend on nondeterministic side effects



\### Deterministically Constrained Rule



If any probabilistic component is used internally, the Program must still ensure:



\- stable output structure

\- explicit recording of execution context

\- replay comparison support

\- no silent drift in authoritative data

\- explainable supersession where outputs differ materially



---



\## 13. Idempotency and Deduplication Rules



This Program must support safe repeated execution against the same governed input set.



\### Idempotency Expectations



For the same case, same source scope, same contract version, same normalization profile, and equivalent source content:



\- duplicate authoritative Facts must not be created

\- existing equivalent Facts may be recognized and reused

\- rerun behavior must be auditable

\- any material output change must be explicitly recorded



\### Deduplication Rule



Equivalent Facts derived from the same support should not multiply across runs unless architecture explicitly models distinct superseded versions.



---



\## 14. Provenance Requirements



Every authoritative Fact must be provenance-linkable.



Minimum provenance fields:



\- `case\_id`

\- `run\_id`

\- `program\_name`

\- `contract\_version`

\- `source\_id`

\- `created\_at`

\- `workflow\_state\_at\_write`



Where applicable:



\- `document\_id`

\- `fragment\_id`

\- extraction span or equivalent locator

\- normalization profile identifier

\- parser or utility version if governed



\### Provenance Rule



No authoritative Fact may exist without traceability back to Source Material.



---



\## 15. Confidence and Review Threshold Rules



Each Fact must have a confidence assessment produced under governed logic.



\### Confidence Expectations



Confidence must reflect support quality, not legal weight.



Confidence may consider:



\- source clarity

\- extraction fidelity

\- ambiguity level

\- contradiction presence

\- source type reliability

\- fragment completeness



\### Review Threshold Behavior



A Fact must be flagged for human review when one or more of the following apply:



\- conflicting source language is material

\- the source is incomplete or unreadable in a material way

\- entity reference is unstable

\- date, amount, or actor attribution is materially uncertain

\- support exists but confidence is below the configured auto-authority threshold

\- the extraction may affect downstream reasoning materially if wrong



\### Approval Boundary Rule



This Program may persist Facts and review flags. It may not convert review-needed uncertainty into attorney judgment.



---



\## 16. Audit Event Requirements



This Program must emit auditable records for at minimum:



\- normalization requested

\- normalization started

\- normalization completed

\- normalization failed

\- normalization requires review

\- normalization rerun started

\- normalization rerun completed

\- normalization outputs superseded

\- normalization outputs reused under idempotent replay, if modeled



Each audit event must include at minimum:



\- case\_id

\- run\_id

\- program\_name

\- timestamp

\- outcome status

\- source count

\- fact count where applicable

\- contract\_version



---



\## 17. Failure Handling



\### Failure Types



\#### Input validation failure

Examples:

\- missing `case\_id`

\- missing `source\_ids`

\- invalid `workflow\_state`

\- case mismatch across sources



Behavior:

\- halt execution before authoritative writes

\- emit failure audit event

\- set failure state if state model requires it



\#### Workflow state failure

Examples:

\- forbidden entry state

\- locked case

\- unresolved review gate



Behavior:

\- halt execution

\- emit failure audit event

\- preserve prior authoritative data



\#### Source parsing failure

Examples:

\- unreadable file

\- unsupported format

\- corrupted fragment

\- extraction utility failure



Behavior:

\- fail the affected unit or the full run according to governed policy

\- emit audit event

\- preserve traceability of skipped/failed units

\- require review if partial outputs remain defensible



\#### Persistence failure

Examples:

\- Fact write failure

\- provenance write failure

\- execution record failure



Behavior:

\- authoritative promotion must fail

\- no silent partial state mutation

\- emit failure audit event

\- preserve rollback or non-authoritative status per architecture



\### Failure Rule



No failure may result in silent promotion of non-traceable or partially written Facts.



---



\## 18. Rerun / Replay / Supersession Behavior



\### Rerun Allowed When



\- governed source content changed

\- normalization rules changed under approved versioning

\- replay validation is being performed

\- corrective rerun is requested through governed workflow

\- partial prior failure requires controlled resumption



\### Replay Expectations



Replay must allow comparison using:



\- case\_id

\- run\_id

\- source set

\- source content identity or fingerprint

\- normalization profile

\- contract version

\- output fingerprint or equivalent comparison structure



\### Supersession Rule



If rerun outputs materially replace prior outputs:



\- the replacement must be explicit

\- prior outputs must be superseded, not silently overwritten

\- audit and execution lineage must preserve what changed and why



\### Preservation Rule



If rerun fails, prior authoritative outputs must remain intact unless architecture explicitly supports staged replacement under transactional control.



---



\## 19. Tool Access



This Program may use only registry-approved tools necessary for bounded normalization.



\### Typical Allowed Tool Classes



\- text extraction utilities

\- OCR or document parsing utilities if formally approved

\- schema validators

\- normalization utilities

\- provenance builders

\- deterministic comparison helpers



\### Tool Access Constraints



\- all tools must be registry-defined

\- all tool access must pass through the governed gateway

\- no uncontrolled network calls

\- no tool may bypass provenance requirements

\- no tool may persist outside governed write paths

\- no tool may access another case without explicit platform authorization



---



\## 20. Security and Isolation Constraints



This Program must enforce:



\- strict case isolation

\- no cross-case reads

\- no cross-case writes

\- least-necessary data access

\- no external uncontrolled data sharing

\- no hidden side-channel persistence

\- no temporary store treated as authoritative state

\- bounded execution within approved platform controls



All execution must remain within the active governed case boundary.



---



\## 21. Human Review / Approval Boundaries



This Program may automatically create bounded Facts when support and confidence thresholds are sufficient under governed rules.



Human review is required when ambiguity, contradiction, instability, or low-confidence conditions make automatic authority unsafe.



\### Human Review Examples



\- conflicting witness and document accounts

\- unclear actor attribution

\- uncertain date or amount

\- fragment support too incomplete for stable phrasing

\- duplicate-looking Facts that may not actually be equivalent



\### Approval Boundary



This Program may create Facts. It may not finalize legal conclusions, strategic interpretations, or attorney-only determinations.



---



\## 22. Acceptance Criteria



This Program contract is implementable when all of the following are true:



\- Source Material → Facts transformation is explicit

\- entry conditions are defined

\- input schema expectations are defined

\- output schema expectations are defined

\- read and write boundaries are explicit

\- idempotency behavior is explicit

\- confidence and review rules are explicit

\- workflow states are explicit

\- provenance requirements are explicit

\- audit requirements are explicit

\- rerun and supersession behavior are explicit

\- failure handling is explicit

\- tool access is bounded and registry-controlled



---



\## 23. Human Presentation Lens



\### What this Program does in plain English



`program\_FACT\_NORMALIZATION` is the platform’s “evidence-to-facts engine.”



It takes source material such as interviews, emails, contracts, invoices, text messages, PDFs, and other intake materials, then converts them into structured factual statements the rest of the platform can safely reason over.



\### Why it matters to attorneys



Without this layer, the system would jump too quickly from messy evidence into legal conclusions.



This Program creates disciplined factual building blocks so that later stages can answer questions like:



\- what happened

\- who did what

\- when it happened

\- what document supports it

\- where uncertainty still exists



\### Why it matters technically



This Program is the first step that turns unstructured evidence into governed platform memory.



It establishes:



\- traceable facts

\- provenance links

\- deterministic replay

\- review flags

\- downstream readiness for mapping, patterning, and COA analysis



\### Attorney-facing message



This is where the platform stops being “document storage” and starts becoming “litigation intelligence.”



It does not decide the case. It creates the factual record the case reasoning can trust.



---



\## 24. Authoring Notes



`program\_FACT\_NORMALIZATION` is the foundational deterministic program in the litigation reasoning pipeline.



All downstream reasoning depends on the quality, traceability, and discipline of the Fact layer it creates.



Typical downstream programs include:



\- `program\_COMPOSITE\_ENGINE`

\- `program\_PATTERN\_ENGINE`

\- `program\_COA\_ENGINE`

\- `program\_COVERAGE\_ENGINE`



This Program must remain aligned with:



\- `system\_STACK\_ARCHITECTURE.md`

\- `system\_REASONING\_MODEL.md`

\- `system\_EVIDENCE\_GRAPH.md`

\- `system\_STATE\_MODEL.md`

\- `system\_TOOL\_GATEWAY.md`

\- `contract\_manifest.yaml`



No implementation may treat this Program as a conversational agent, an autonomous legal analyst, or a shortcut to attorney judgment.

