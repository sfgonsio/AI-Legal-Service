# CASECORE — CORE DATA WAVE TICKETS

## PURPOSE

Translate the approved core data implementation plan into execution-ready tickets by wave.

This ticket set is limited to the hardened path:

- Intake
- Message normalization
- Brain staged outputs
- Legal mapping / Build Case
- War Room
- Discovery entry handoff

These tickets are ordered to reduce schema drift, preserve truth/derived separation, and allow controlled implementation.

---

# WAVE 1 — CASE + INTAKE FOUNDATION

## W1-T1 — Create core case tables
### Objective
Create the base case persistence layer.

### Deliverables
- `cases`
- `case_status`
- `case_stage_state`

### Requirements
- stable case ID
- created_at / updated_at
- stage state queryable by case
- no stage-specific business logic embedded in base case row

### Acceptance
- case can be created
- case stage state can be read and updated
- stage state is independent from UI route structure

---

## W1-T2 — Create interview session persistence
### Objective
Persist interview sessions and progress.

### Deliverables
- `interview_sessions`
- `interview_responses`

### Requirements
- every session linked to case_id
- record start/end timestamps
- record interviewer/user identity
- response persistence across question navigation
- support audio and written interview modes

### Acceptance
- responses survive refresh/navigation
- multiple sessions supported
- no hardcoded question count in persistence layer

---

## W1-T3 — Create interview recording and transcript persistence
### Objective
Persist immutable audio metadata and editable transcript structures.

### Deliverables
- `interview_recordings`
- `interview_transcript_segments`

### Requirements
- raw audio is immutable
- transcript edits versioned or superseded, not destructive
- capture user/date/time for recording actions
- preserve linkage between recording and transcript segment

### Acceptance
- recording metadata persists per session
- transcript segment updates are attributable
- raw recording reference remains unchanged

---

## W1-T4 — Create uploaded file persistence
### Objective
Persist intake file uploads and versions.

### Deliverables
- `uploaded_files`
- `uploaded_file_versions`

### Requirements
- file linked to case
- type, source, hash, upload timestamp
- preserve immutable original reference
- support future external source imports

### Acceptance
- file metadata persists cleanly
- version relationship works
- file hash and source are queryable

---

## W1-T5 — Create intake actor persistence
### Objective
Persist actors and intake-provided relationship inputs.

### Deliverables
- `intake_actor_records`
- `intake_actor_relationship_inputs`

### Requirements
- support people and entities
- name-first display support
- role/context as separate fields
- no forced deduplication at intake stage

### Acceptance
- actors can be added by type-in or parsed input
- relationship inputs persist independently from later graph reasoning
- actors queryable by case

---

## W1-T6 — Create intake summary persistence
### Objective
Persist client and attorney summary outputs.

### Deliverables
- `intake_summaries_client`
- `intake_summaries_attorney`

### Requirements
- version or supersession support
- created_by / reviewed_by fields
- client summary separated from attorney legal framing summary

### Acceptance
- latest summary retrievable
- prior summary retained
- summary type clearly distinguished

---

## W1-T7 — Create intake timeline seed persistence
### Objective
Persist raw timeline seeds from intake.

### Deliverables
- `intake_timeline_seeds`

### Requirements
- store event-like fragments without overcommitting to final timeline
- link to source response/file/actor where possible
- preserve uncertainty

### Acceptance
- timeline seeds queryable by case
- seeds can feed later Brain timeline assembly

---

# WAVE 2 — MESSAGE NORMALIZATION PERSISTENCE

## W2-T1 — Create message source file tables
### Objective
Persist uploaded/exported communication source files.

### Deliverables
- `message_source_files`

### Requirements
- file hash
- file type
- source system
- case linkage
- parse status

### Acceptance
- source file tracked independently from extracted messages
- multiple source files supported per case

---

## W2-T2 — Create normalized message tables
### Objective
Persist normalized message-level objects.

### Deliverables
- `normalized_messages`

### Requirements
- sender candidate
- recipient candidates
- source linkage
- body_clean
- confidence fields
- ambiguity flags

### Acceptance
- one normalized message row per extracted message
- confidence and ambiguity queryable

---

## W2-T3 — Create quoted and forwarded block tables
### Objective
Persist quoted and forwarded content as separate structures.

### Deliverables
- `quoted_blocks`
- `forwarded_blocks`

### Requirements
- quoted/forwarded speaker separated from current sender
- nesting/chain depth supported
- confidence supported

### Acceptance
- quoted text not attributed to current sender
- forwarded source chain preserved

---

## W2-T4 — Create normalized statement persistence
### Objective
Persist statement-level segmentation outputs.

### Deliverables
- `normalized_statements`

### Requirements
- statement text
- speaker candidate
- message linkage
- pronoun flags
- signal flags
- attribution confidence

### Acceptance
- statements queryable by message and thread
- signal flags preserved

---

## W2-T5 — Create referenced actor candidate persistence
### Objective
Persist third-person and ambiguous actor references.

### Deliverables
- `referenced_actor_candidates`

### Requirements
- separate from sender/recipient
- resolution status
- candidate matches
- confidence

### Acceptance
- A?B about C structure can be represented without forced merge

---

## W2-T6 — Create message thread and corpus persistence
### Objective
Persist thread and corpus-level context.

### Deliverables
- `message_threads`
- `message_corpus`

### Requirements
- support multi-file thread reconstruction
- support corpus-wide conflict markers
- support participant lists

### Acceptance
- thread retrievable by case
- corpus state retrievable by case
- multi-file context preserved

---

## W2-T7 — Create normalization flags and failures persistence
### Objective
Persist normalization quality and failure states.

### Deliverables
- `normalization_quality_flags`
- `normalization_failure_events`

### Requirements
- explicit states:
  - ambiguous_sender
  - ambiguous_recipient
  - unresolved_third_person
  - broken_thread
  - insufficient_message_structure
- severity support

### Acceptance
- messages with failures are reviewable
- no silent failure

---

# WAVE 3 — BRAIN STAGED OUTPUT PERSISTENCE

## W3-T1 — Create classified statement persistence
### Objective
Persist Brain statement classification outputs.

### Deliverables
- `classified_statements`

### Requirements
- classify fact/allegation/opinion/hearsay/speculation/etc.
- link back to normalized_statement
- confidence per classification

### Acceptance
- classified statements queryable by case and message

---

## W3-T2 — Create fact candidate persistence
### Objective
Persist fact candidates derived from statements.

### Deliverables
- `fact_candidates`

### Requirements
- derived_from_statement_ids
- actor links
- event time candidate
- fact type
- confidence

### Acceptance
- facts queryable independently from statements
- facts traceable back to source statements

---

## W3-T3 — Create actor graph persistence
### Objective
Persist actor graph nodes and edges.

### Deliverables
- `actor_graph_nodes`
- `actor_graph_edges`

### Requirements
- node type: person/entity/unknown candidate
- edge types for relationship claims
- confidence and source linkage
- no auto-merge without evidence

### Acceptance
- graph queryable by case
- ambiguous relationships preserved

---

## W3-T4 — Create event candidate and timeline persistence
### Objective
Persist event structures and timeline assembly outputs.

### Deliverables
- `event_candidates`
- `event_timeline_events`
- `event_timeline_chains`

### Requirements
- source-linked events
- chronology support
- uncertainty support
- chain/grouping support

### Acceptance
- timeline can be read by case
- events can link to facts/statements/actors

---

## W3-T5 — Create contradiction and gap persistence
### Objective
Persist contradictions and unresolved evidentiary/structural gaps.

### Deliverables
- `contradiction_records`
- `gap_records`

### Requirements
- source-linked contradiction pairs/groups
- materiality/severity
- review state

### Acceptance
- contradictions and gaps are queryable for legal mapping and War Room

---

# WAVE 4 — LEGAL MAPPING / BUILD CASE PERSISTENCE

## W4-T1 — Create legal mapping record persistence
### Objective
Persist authority-backed legal mapping records.

### Deliverables
- `legal_mapping_records`
- `authority_application_records`

### Requirements
- every mapping tied to authority
- facts/events/actors linked
- confidence and unresolved gap fields

### Acceptance
- no legal mapping without authority reference

---

## W4-T2 — Create COA candidate persistence
### Objective
Persist cause-of-action candidates.

### Deliverables
- `coa_candidates`

### Requirements
- source facts/events
- authority linkage
- status/review support

### Acceptance
- COA candidates queryable by case
- attorney review state supported

---

## W4-T3 — Create burden and element support persistence
### Objective
Persist burden structures and element-level support.

### Deliverables
- `burden_candidates`
- `burden_element_support`

### Requirements
- element-level mapping
- supporting fact IDs
- missing element/gap support
- confidence per element

### Acceptance
- burden coverage queryable at element granularity

---

## W4-T4 — Create remedy candidate persistence
### Objective
Persist remedies linked to burdens/COA.

### Deliverables
- `remedy_candidates`

### Requirements
- source legal structure
- prerequisite linkage
- confidence and viability notes

### Acceptance
- remedies queryable by case and linked legal structure

---

## W4-T5 — Create complaint skeleton persistence
### Objective
Persist draft legal complaint structures.

### Deliverables
- `complaint_skeletons`

### Requirements
- versioning or supersession
- source linkage to COA/burdens/facts
- not treated as canonical truth

### Acceptance
- latest complaint skeleton retrievable
- previous versions preserved

---

## W4-T6 — Create coverage input persistence
### Objective
Persist structured inputs used by War Room coverage/simulation.

### Deliverables
- `coverage_input_sets`

### Requirements
- bundle burden/element/fact/remedy support
- snapshot-able
- queryable for War Room entry

### Acceptance
- War Room can consume without recomputing everything ad hoc

---

# WAVE 5 — WAR ROOM PERSISTENCE

## W5-T1 — Implement strategy scenario tables
### Objective
Implement append-only scenario persistence.

### Deliverables
- `strategy_scenarios`
- `strategy_selections`

### Requirements
- parent/root lineage
- version number
- append-only revisions

### Acceptance
- scenario fork/version works without destructive overwrite

---

## W5-T2 — Implement simulation snapshot tables
### Objective
Persist simulation outputs.

### Deliverables
- `coverage_snapshots`
- `assumption_sets`
- `outcome_projections`
- `question_sets`
- `strategy_gradients`

### Requirements
- scenario_id linkage
- calculation version / timestamp
- latest retrieval deterministic

### Acceptance
- simulation outputs preserved per scenario version

---

## W5-T3 — Implement strategy plan persistence
### Objective
Persist attorney-promoted plans.

### Deliverables
- `strategy_plans`

### Requirements
- linked source scenario
- approved questions snapshot
- outcome snapshot
- execution status metadata

### Acceptance
- plan promotion does not mutate source scenario history

---

## W5-T4 — Implement War Room artifact persistence
### Objective
Persist all generated/reviewable War Room artifacts.

### Deliverables
- `warroom_artifacts`

### Requirements
- artifact type/status
- exportability
- review metadata
- supersession support

### Acceptance
- strategic artifacts queryable and reviewable

---

## W5-T5 — Implement War Room read/query layer
### Objective
Support efficient reads for scenario and plan views.

### Deliverables
- scenario list query
- scenario full detail query
- scenario compare query
- best-scenario query
- plan list query

### Acceptance
- latest snapshot reads are deterministic
- no N+1 query pattern in core endpoints

---

# WAVE 6 — DISCOVERY ENTRY HANDOFF

## W6-T1 — Create discovery handoff packet persistence
### Objective
Persist the structured handoff from War Room to Discovery.

### Deliverables
- `discovery_handoff_packets`

### Requirements
- link to approved scenario/plan
- include COA/burdens/remedies/questions/targets
- packet versioning

### Acceptance
- handoff packet retrievable by case
- packet is source-linked and auditable

---

## W6-T2 — Create discovery readiness persistence
### Objective
Persist explicit readiness state for Discovery entry.

### Deliverables
- `discovery_readiness_assessments`

### Requirements
- readiness score/state
- missing prerequisites
- reviewed_by / approved_by
- timestamped

### Acceptance
- case can be marked not-ready with explicit reasons

---

## W6-T3 — Create approved question execution persistence
### Objective
Persist approved discovery questions for execution.

### Deliverables
- `approved_question_execution_sets`

### Requirements
- link back to question sets / strategy plan
- execution ordering
- review state

### Acceptance
- approved questions retrievable without ambiguity

---

## W6-T4 — Create discovery target persistence
### Objective
Persist prioritized discovery targets.

### Deliverables
- `discovery_target_sets`

### Requirements
- actor/evidence/burden linkage
- priority ordering
- rationale linkage

### Acceptance
- discovery team can read targets directly from packet/set

---

# CROSS-WAVE IMPLEMENTATION TICKETS

## X-T1 — Implement base audit fields and conventions
### Objective
Standardize created_at / updated_at / created_by / reviewed_by patterns.

### Acceptance
- applied consistently across all new tables

---

## X-T2 — Implement stable ID strategy
### Objective
Standardize UUID or case-scoped ID conventions.

### Acceptance
- IDs consistent across truth and derived strata

---

## X-T3 — Implement truth vs derived schema boundary review
### Objective
Review all new tables for proper stratum placement before migration merge.

### Acceptance
- no derived structure stored in canonical tables by mistake

---

## X-T4 — Build golden-path seed case
### Objective
Seed one coherent matter across all implemented waves.

### Acceptance
- end-to-end read/write sanity test possible

---

## X-T5 — Build messy-path seed case
### Objective
Seed one ambiguous/conflicting matter.

### Acceptance
- system fails safely and preserves ambiguity instead of guessing

---

# DELIVERY ORDER

Recommended execution sequence:

1. W1-T1 through W1-T7
2. W2-T1 through W2-T7
3. W3-T1 through W3-T5
4. W4-T1 through W4-T6
5. W5-T1 through W5-T5
6. W6-T1 through W6-T4
7. X-T1 through X-T5 interleaved as needed

---

# IMPLEMENTATION RULE

No later-wave ticket should be merged if it depends on earlier-wave data structures that are still undefined, mocked, or UI-only.

---

**Version:** 1.0  
**Status:** ACTIVE TICKET SET
