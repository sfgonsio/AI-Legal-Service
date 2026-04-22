# CASECORE — CORE DATA IMPLEMENTATION PLAN

## 1. PURPOSE

This document translates the approved platform design artifacts into an implementation-ready data plan for the hardened core path of the platform.

This plan exists to bridge:

- product/design intent
- governance contracts
- data persistence
- service ownership
- migration order
- validation gates

It defines what data structures should be implemented now so the platform can reliably support:

- Intake
- Message Normalization
- Brain staged outputs
- Build Case / legal mapping
- War Room
- Discovery entry handoff

This plan is intentionally limited to the current hardened slice and does not attempt to fully model all downstream stage gates.

---

## 2. SCOPE

This implementation plan covers the following operational path:

1. Intake
2. Message normalization
3. Brain staged processing
4. Legal mapping / Build Case
5. War Room
6. Discovery entry handoff

This plan does **not** yet fully implement:

- full Discovery execution
- deposition execution
- trial execution
- closure / post-matter analytics

---

## 3. GOVERNING PRINCIPLES

### 3.1 Two-Strata Rule
The platform must distinguish between:

- **Truth / Canonical Stratum**
- **Derived / Reasoning Stratum**

Truth objects are source-grounded and preserved.  
Derived objects are proposal, interpretation, structure, strategy, or simulation outputs.

### 3.2 No Raw-to-Legal Leap
No legal mapping should occur directly from raw messages or unnormalized uploads.

Required staged path:

- raw input
- normalized object
- statement / fact extraction
- actor / event / timeline structure
- legal mapping
- strategy

### 3.3 Append-Only and Replayable
Scenario-like and derived reasoning artifacts must be append-only, versioned, and replayable.

### 3.4 Explicit Uncertainty
Ambiguity, insufficiency, contradiction, and unresolved identity must be preserved as explicit system states.

### 3.5 Traceability
Every derived conclusion must be traceable to:

- source artifact
- source statement or extract
- actor/entity object
- event/timeline object
- authority object
- transformation stage

### 3.6 Attorney Governance
The system may propose and structure, but attorney review governs promotion of high-impact legal conclusions and strategy outputs.

---

## 4. IMPLEMENTATION SOURCES OF TRUTH

This plan is aligned to the following approved design artifacts:

- `contract/v1/data/INTAKE_DB_SPEC.md`
- `contract/v1/data/WAR_ROOM_DB_SPEC.md`
- `contract/v1/brain/BRAIN_CONTRACT_SPEC.md`
- `contract/v1/brain/MESSAGE_NORMALIZATION_SPEC.md`

If implementation conflicts with these documents, the conflict must be surfaced and resolved before schema drift is introduced.

---

## 5. DATA STRATA

## 5.1 Truth / Canonical Stratum

These objects preserve source-grounded inputs and normalized evidence structures.

### Core case objects
- cases
- case_status
- case_stage_state

### Intake truth objects
- interview_sessions
- interview_responses
- interview_recordings
- interview_transcript_segments
- uploaded_files
- uploaded_file_versions
- intake_actor_records
- intake_actor_relationship_inputs
- intake_summaries_client
- intake_summaries_attorney
- intake_timeline_seeds

### Message normalization truth objects
- message_source_files
- normalized_messages
- normalized_statements
- quoted_blocks
- forwarded_blocks
- referenced_actor_candidates
- message_threads
- message_corpus
- normalization_quality_flags
- normalization_failure_events

### Evidence truth objects
- evidence_items
- evidence_file_links
- evidence_extracts
- evidence_source_links
- evidence_inventory_status

### Authority truth references
- authority_family_registry
- authority_unit_registry
- authority_link_references

These authority records may be loaded from `authority_store` and referenced by ID/path in the runtime DB.

---

## 5.2 Derived / Reasoning Stratum

These objects are downstream structured reasoning and strategic outputs.

### Brain-stage derived objects
- classified_statements
- fact_candidates
- actor_graph_nodes
- actor_graph_edges
- event_candidates
- event_timeline_events
- event_timeline_chains
- contradiction_records
- gap_records

### Legal mapping / Build Case objects
- legal_mapping_records
- coa_candidates
- burden_candidates
- burden_element_support
- remedy_candidates
- complaint_skeletons
- coverage_input_sets
- authority_application_records

### War Room derived objects
- strategy_scenarios
- strategy_selections
- coverage_snapshots
- assumption_sets
- outcome_projections
- question_sets
- strategy_gradients
- strategy_plans
- warroom_artifacts

### Discovery entry derived objects
- discovery_handoff_packets
- discovery_readiness_assessments
- approved_question_execution_sets
- discovery_target_sets

---

## 6. IMPLEMENTATION WAVES

## Wave 1 — Case + Intake Foundation

### Objective
Stand up the persistence layer for case creation and intake operations.

### Must implement
- case record
- case stage state
- interview session
- interview response persistence
- audio recording metadata
- transcript segment persistence
- uploaded files
- intake actors
- actor relationship input records
- client and attorney intake summaries

### Why first
Everything else depends on reliable case-scoped intake persistence.

### Exit criteria
- A case can be created
- Interview responses persist across sessions
- Audio/session metadata is immutable and traceable
- Uploaded files are attached to case
- Actors are persisted with stable IDs
- Intake summaries can be saved and revised via versioning or supersession rules

---

## Wave 2 — Message Normalization Persistence

### Objective
Persist normalized communication data before Brain reasoning begins.

### Must implement
- message_source_files
- normalized_messages
- normalized_statements
- quoted_blocks
- forwarded_blocks
- referenced_actor_candidates
- message_threads
- message_corpus
- normalization flags / failures

### Why second
This is the key protection against bad message reasoning and actor confusion.

### Exit criteria
- A message file can be ingested
- Individual messages can be normalized
- Statements can be segmented
- Quoted and forwarded content is preserved separately
- Third-person references are preserved
- Threads and corpus records are created
- Ambiguity states persist explicitly

---

## Wave 3 — Brain Staged Output Persistence

### Objective
Persist Brain stage outputs after normalization and before legal mapping.

### Must implement
- classified_statements
- fact_candidates
- actor_graph_nodes
- actor_graph_edges
- event_candidates
- timeline_events
- contradiction records
- gap records

### Why third
This is the structural reasoning layer needed before legal application.

### Exit criteria
- Statements can be classified
- Facts can be derived from statements
- Actor graph can be persisted
- Events and timeline chains can be persisted
- Contradictions and gaps are queryable

---

## Wave 4 — Legal Mapping / Build Case Persistence

### Objective
Persist the platform’s legal structuring outputs.

### Must implement
- legal_mapping_records
- coa_candidates
- burden_candidates
- burden_element_support
- remedy_candidates
- complaint_skeletons
- authority_application_records
- coverage_input_sets

### Why fourth
This is the layer that turns structured facts into legal structure.

### Exit criteria
- Facts/events can map to authority-backed COA/burden/remedy structures
- Legal conclusions carry source + authority traceability
- Complaint skeleton outputs can be saved
- Coverage inputs exist for War Room

---

## Wave 5 — War Room Persistence

### Objective
Implement the War Room persistence layer already defined in the War Room DB spec.

### Must implement
- strategy_scenarios
- strategy_selections
- coverage_snapshots
- assumption_sets
- outcome_projections
- question_sets
- strategy_gradients
- strategy_plans
- warroom_artifacts

### Why fifth
War Room depends on the upstream truth and legal mapping layers being real.

### Exit criteria
- Scenario versioning works append-only
- Simulations persist correctly
- Plans can be promoted without mutating source scenario history
- Query layer reads current/latest snapshots correctly

---

## Wave 6 — Discovery Entry Handoff

### Objective
Persist the package that hands the case from War Room into Discovery.

### Must implement
- discovery_handoff_packets
- discovery_readiness_assessments
- approved_questions
- prioritized discovery targets
- linked scenario/plan references

### Why sixth
Discovery should begin only after the case has enough structured truth and strategy.

### Exit criteria
- Discovery handoff packet can be generated
- Packet is source-linked and auditable
- Discovery readiness state is explicit
- Questions and targets are approved and prioritized

---

## 7. MIGRATION ORDER

Recommended migration order:

1. cases
2. case_stage_state
3. uploaded_files
4. interview_sessions
5. interview_responses
6. interview_recordings
7. interview_transcript_segments
8. intake_actor_records
9. intake_actor_relationship_inputs
10. intake_summaries_client
11. intake_summaries_attorney
12. intake_timeline_seeds

13. message_source_files
14. normalized_messages
15. normalized_statements
16. quoted_blocks
17. forwarded_blocks
18. referenced_actor_candidates
19. message_threads
20. message_corpus
21. normalization_quality_flags
22. normalization_failure_events

23. evidence_items
24. evidence_extracts
25. evidence_source_links

26. classified_statements
27. fact_candidates
28. actor_graph_nodes
29. actor_graph_edges
30. event_candidates
31. event_timeline_events
32. event_timeline_chains
33. contradiction_records
34. gap_records

35. legal_mapping_records
36. coa_candidates
37. burden_candidates
38. burden_element_support
39. remedy_candidates
40. complaint_skeletons
41. authority_application_records
42. coverage_input_sets

43. strategy_scenarios
44. strategy_selections
45. coverage_snapshots
46. assumption_sets
47. outcome_projections
48. question_sets
49. strategy_gradients
50. strategy_plans
51. warroom_artifacts

52. discovery_handoff_packets
53. discovery_readiness_assessments
54. approved_question_execution_sets
55. discovery_target_sets

---

## 8. SERVICE OWNERSHIP

## 8.1 Intake Service Ownership
Writes:
- cases
- interview_sessions
- interview_responses
- interview_recordings
- transcript segments
- uploaded_files
- intake actors
- intake summaries

Reads:
- case state
- uploaded files
- actor list
- summaries

## 8.2 Message Normalization Service Ownership
Writes:
- message_source_files
- normalized_messages
- normalized_statements
- quoted_blocks
- forwarded_blocks
- referenced_actor_candidates
- threads
- corpus
- quality flags / failures

Reads:
- uploaded communication files
- actor registry
- case context

## 8.3 Brain Service Ownership
Writes:
- classified_statements
- fact_candidates
- actor graph
- events / timeline
- contradictions
- gaps

Reads:
- normalized message objects
- interview normalized inputs
- document extracts
- actor registry
- evidence inventory
- authority references

## 8.4 Legal Mapping / Build Case Service Ownership
Writes:
- legal mapping records
- COA candidates
- burden structures
- remedies
- complaint skeletons
- authority applications
- coverage inputs

Reads:
- fact candidates
- timeline
- actor graph
- authority registry

## 8.5 War Room Service Ownership
Writes:
- all War Room persistence objects

Reads:
- coverage inputs
- burden structures
- remedy structures
- actor profiles
- contradictions
- public intelligence inputs where available

## 8.6 Discovery Handoff Service Ownership
Writes:
- discovery handoff packet
- readiness assessment
- approved execution sets

Reads:
- strategy plans
- question sets
- priorities
- target sets

---

## 9. TABLE DESIGN RULES

### 9.1 Stable IDs
Every row should use stable case-scoped IDs or UUIDs as appropriate.

### 9.2 Timestamps
Every persisted object should include:
- created_at
- updated_at where mutable
- captured_at where source-derived
- approved_at / reviewed_at where applicable

### 9.3 Attribution
Every object should include:
- created_by
- normalized_by / generated_by when applicable
- reviewed_by / approved_by when applicable

### 9.4 JSON vs normalized children
Use normalized tables for high-value entities and relationships.  
Use JSON only when:
- snapshotting derived state
- preserving flexible selection bundles
- storing structured outputs that are likely to evolve before full normalization

### 9.5 Do not over-normalize too early
Canonical source objects and critical graph objects should be normalized.  
Strategy snapshots and scenario selections may remain partially JSON for v1.

---

## 10. IMMUTABILITY RULES

## Immutable after save
- raw file records
- recording metadata
- normalized_message rows
- normalized_statement rows
- fact_candidate rows
- event candidate rows
- legal mapping rows
- War Room snapshots
- discovery handoff packet snapshots

## Mutable only by status / review metadata
- review state
- approval state
- execution state
- readiness state

## Versioned by new row
- intake summaries
- complaint skeleton revisions
- scenario revisions
- strategy plan revisions
- discovery handoff revisions

---

## 11. MINIMUM QUERY REQUIREMENTS

The implementation must support the following reads efficiently:

### Intake
- get case intake state
- get interview progress
- get uploaded files
- get actors

### Message normalization
- get normalized messages by case
- get all statements for a thread
- get unresolved references
- get broken threads

### Brain
- get facts by case
- get actor graph by case
- get event timeline by case
- get contradictions / gaps

### Build Case
- get COA candidates
- get burden support by element
- get remedy candidates
- get complaint skeleton

### War Room
- get scenarios by case
- get latest snapshots by scenario
- compare scenarios
- get best scenario
- get plans by case

### Discovery entry
- get latest approved handoff packet
- get discovery readiness state
- get approved question execution set

---

## 12. VALIDATION GATES

## Gate A — Intake data integrity
Before moving past Wave 1:
- verify interview persistence
- verify actor persistence
- verify uploaded file linkage
- verify summary version behavior

## Gate B — Message normalization integrity
Before moving past Wave 2:
- verify sender/recipient correctness
- verify quote/forward separation
- verify third-person references
- verify thread reconstruction
- verify ambiguity preservation

## Gate C — Brain structural integrity
Before moving past Wave 3:
- verify facts derive from statements
- verify actor graph outputs
- verify timeline and contradiction persistence

## Gate D — Legal mapping integrity
Before moving past Wave 4:
- verify no legal mapping without authority linkage
- verify COA/burden/remedy traceability
- verify complaint skeleton persistence

## Gate E — War Room integrity
Before moving past Wave 5:
- verify append-only scenario versioning
- verify snapshots and plans persist cleanly
- verify query layer returns latest snapshots deterministically

## Gate F — Discovery entry integrity
Before moving past Wave 6:
- verify handoff packet completeness
- verify questions/targets approved and linked
- verify strategy-to-discovery traceability

---

## 13. TEST DATA STRATEGY

Implementation should be tested with:

### Golden-path matter
A clean, coherent case with:
- structured intake
- clear actors
- coherent messages
- reasonable evidence
- obvious candidate claims

### Messy-path matter
A realistic hard case with:
- conflicting communications
- ambiguous third-party references
- weak timelines
- incomplete uploads
- uncertain remedies

The system must succeed on the first and fail safely on the second.

---

## 14. DISCOVERY ENTRY DEFINITION

A case is ready for Discovery entry only when the persisted system can produce:

- candidate COA set
- burden structure
- remedy structure
- complaint skeleton
- fact/timeline foundation
- actor structure
- approved or reviewable question targets
- prioritized discovery targets
- explicit gap and assumption list
- strategy plan or equivalent structured handoff

If these do not exist, the case should not be marked Discovery-ready.

---

## 15. DEFERRED DECISIONS

The following are intentionally deferred:

- full deposition execution schema
- trial-specific evidence presentation schema
- final settlement modeling schema
- full public intelligence subsystem normalization
- full expert witness subsystem
- post-resolution analytics

These should not block implementation of the hardened core path.

---

## 16. IMPLEMENTATION DELIVERABLES

The outcome of this plan should be:

1. migration files
2. ORM / model definitions
3. persistence services
4. read/query services
5. write/read tests
6. one golden-path seeded case
7. one messy-path seeded case
8. readiness validation checklist

---

## 17. NEXT IMPLEMENTATION STEP

The immediate next step after approving this plan is to create:

- schema implementation tasks by wave
- migration order tickets
- service ownership tickets
- validation checklist for each wave

This plan should be used as the implementation backbone while the authority library build-out proceeds in parallel.

---

**Version:** 1.0  
**Status:** ACTIVE IMPLEMENTATION PLAN
