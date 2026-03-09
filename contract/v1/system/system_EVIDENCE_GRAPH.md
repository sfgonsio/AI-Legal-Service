# system_EVIDENCE_GRAPH.md

## 1. Document Purpose

This document defines the authoritative Evidence Graph model for the AI Legal Service Platform.

The Evidence Graph is the platform’s structured, persistent, case-bounded memory system. It stores the governed objects required for litigation reasoning, including source material, facts, entities, relationships, events, signals, patterns, causes of action, coverage structures, and provenance.

This document exists to ensure that all reasoning stages have a clean, auditable, queryable, and replay-compatible storage model.

If any downstream schema, program contract, agent contract, UI behavior, or workflow specification conflicts with this document, this document governs unless formally revised through approved change control.

---

## 2. Scope

This document governs the persistent data model for:

- cases and matters
- source material registration
- provenance
- facts
- entities
- aliases
- relationships
- events
- signals
- patterns
- causes of action
- coverage structures
- review status
- confidence metadata
- governed linkage between all reasoning stages

This document applies to:

- database design
- storage contracts
- program read/write behavior
- agent persistence boundaries
- query design
- replay compatibility
- audit linkage
- UI display surfaces that reflect authoritative state

---

## 3. Architectural Principle

The Evidence Graph is the platform’s authoritative case memory.

It must store litigation intelligence as connected, provenance-linked structures rather than as isolated files, opaque blobs, or agent-only memory.

Core rule:

**If information materially affects legal reasoning, workflow progression, evidence traceability, or attorney review, it must exist in the Evidence Graph or in an explicitly governed authoritative store linked to it.**

---

## 4. Graph Role in the Platform Stack

Within the platform stack:

- the **Spine** governs rules and execution constraints
- the **Evidence Graph** stores authoritative case memory
- **Programs** transform and write governed graph objects
- **Agents** read from and propose structures into governed graph flows
- the **UI** presents and routes interaction with graph-backed state

The Evidence Graph does not replace the Spine, and the Spine does not replace the Evidence Graph.

---

## 5. Core Design Requirements

The Evidence Graph must be:

- authoritative
- case-bounded
- provenance-linked
- queryable
- structured
- version-aware where required
- replay-compatible
- auditable
- explainable
- compatible with deterministic program execution

The Evidence Graph must not depend on hidden, informal, or purely conversational memory to preserve litigation state.

---

## 6. Canonical Object Families

The Evidence Graph must support at minimum the following object families:

1. Cases and Matters
2. Source Material
3. Documents and Fragments
4. Facts
5. Entities
6. Aliases
7. Relationships
8. Events
9. Signals
10. Patterns
11. Causes of Action
12. Coverage
13. Review and Approval State
14. Provenance
15. Audit-Linked Execution References

These families define the authoritative graph surface for MVP.

---

## 7. Canonical Object Definitions

---

## 7.1 Case

### Purpose

Represents the top-level litigation domain boundary.

### Required Characteristics

A Case must:

- uniquely identify the matter domain
- bound all graph objects beneath it
- prevent cross-case leakage
- support role-aware access control
- support case-level metadata

### Example Fields

- `case_id`
- `case_key`
- `case_name`
- `jurisdiction`
- `matter_type`
- `status`
- `created_at`
- `updated_at`

### Rule

Every authoritative graph object must belong to exactly one active case unless future approved architecture explicitly supports cross-case constructs.

---

## 7.2 Matter / Submatter

### Purpose

Represents a governed subdivision within a case where needed.

### Example Use

- separate disputes inside one lawsuit
- claim clusters
- related transactional threads
- party-specific issue domains

### Example Fields

- `matter_id`
- `case_id`
- `matter_name`
- `matter_type`
- `status`

### Rule

Submatter use is optional for MVP, but the schema should not preclude it.

---

## 7.3 Source Material

### Purpose

Represents raw litigation inputs before or alongside downstream normalization.

### Includes

- interview responses
- uploaded files
- emails
- transcripts
- spreadsheets
- contracts
- images
- manually entered notes where permitted
- structured imports

### Example Fields

- `source_id`
- `case_id`
- `source_type`
- `source_label`
- `ingest_channel`
- `originator`
- `capture_timestamp`
- `trust_level`
- `raw_location_ref`
- `hash_ref`

### Rule

Source Material is governed raw input, not yet legal intelligence.

---

## 7.4 Document

### Purpose

Represents a registered file or formal source asset inside the case.

### Example Fields

- `document_id`
- `case_id`
- `source_id`
- `doc_uid`
- `filename`
- `mime_type`
- `file_hash`
- `ingested_at`
- `document_date`
- `author_ref`
- `custodian_ref`

### Rule

Every Document must be provenance-linkable to the source path or capture path from which it entered the platform.

---

## 7.5 Document Fragment / Chunk

### Purpose

Represents a bounded sub-document unit used for traceable extraction and reasoning.

### Example Fields

- `fragment_id`
- `document_id`
- `chunk_uid`
- `page_ref`
- `char_start`
- `char_end`
- `text_excerpt_ref`
- `hash_ref`

### Rule

Where a fact, event, signal, or pattern is derived from a sub-document region, the region must be linkable through a fragment or equivalent traceable structure.

---

## 7.6 Fact

### Purpose

Represents a bounded, provenance-linked statement derived from source material.

### Example Fact Types

- communication occurred
- payment made
- contract signed
- product shipped
- notice sent
- access revoked
- meeting occurred
- assignment referenced

### Example Fields

- `fact_id`
- `case_id`
- `fact_type`
- `fact_text_normalized`
- `subject_ref`
- `predicate`
- `object_ref_or_value`
- `date_ref_or_value`
- `amount_ref_or_value`
- `confidence_score`
- `dispute_status`
- `derived_from_source_id`
- `derived_from_document_id`
- `derived_from_fragment_id`

### Rule

A Fact must describe supported content, not freeform legal conclusions.

---

## 7.7 Entity

### Purpose

Represents a person, organization, product, instrument, account, location, or other case-relevant actor/object.

### Entity Classes May Include

- person
- company
- partnership
- trust
- brand
- product
- contract
- invoice
- account
- communication artifact
- location
- shipment
- filing

### Example Fields

- `entity_id`
- `case_id`
- `entity_type`
- `canonical_name`
- `status`
- `confidence_score`
- `notes_ref`
- `first_seen_source_id`

### Rule

Entities must be case-bounded and should support canonical identity plus alias resolution.

---

## 7.8 Alias

### Purpose

Represents alternate names, spellings, abbreviations, or references that point to a canonical entity.

### Example Fields

- `alias_id`
- `case_id`
- `entity_id`
- `alias_text`
- `alias_type`
- `confidence_score`
- `source_ref`

### Rule

Alias resolution must not destroy the original observed text. Canonicalization must preserve traceability.

---

## 7.9 Relationship

### Purpose

Represents a governed connection between entities, documents, facts, or events.

### Example Relationship Types

- owns
- controls
- signed
- sent
- received
- paid
- delivered
- managed
- represented
- transferred_to
- guaranteed
- interfered_with
- performed_for

### Example Fields

- `relationship_id`
- `case_id`
- `relationship_type`
- `left_object_type`
- `left_object_id`
- `right_object_type`
- `right_object_id`
- `confidence_score`
- `effective_date`
- `end_date`
- `source_support_ref`

### Rule

Relationships must be provenance-aware and must not be stored as unsupported inference blobs.

---

## 7.10 Event

### Purpose

Represents a time-bound or sequence-bound occurrence constructed from facts and relationships.

### Example Event Types

- contract execution
- payment request
- shipment refusal
- notice delivery
- trademark use
- demand letter sent
- account lockout
- termination declaration

### Example Fields

- `event_id`
- `case_id`
- `event_type`
- `event_label`
- `start_time`
- `end_time`
- `event_status`
- `confidence_score`
- `sequence_index`
- `dispute_status`

### Supporting Link Structures

Events should also support:

- event participants
- linked facts
- linked documents
- linked fragments
- linked entities

### Rule

Every Event must be explainable through supporting lower-layer objects.

---

## 7.11 Signal

### Purpose

Represents a localized indicator of legal or strategic significance.

### Example Signal Types

- repeated late payment
- inconsistent ownership reference
- possible agency language
- notice repetition
- suspicious timing cluster
- missing support indicator

### Example Fields

- `signal_id`
- `case_id`
- `signal_type`
- `signal_label`
- `signal_description`
- `confidence_score`
- `severity_score`
- `status`

### Rule

Signals suggest significance but do not by themselves establish legal sufficiency.

---

## 7.12 Pattern

### Purpose

Represents a structured aggregation of signals, facts, events, and relationships that together form a meaningful theme.

### Example Pattern Types

- breach and notice pattern
- ownership confusion pattern
- interference pattern
- fraud-indicating conduct pattern
- unjust enrichment pattern
- recurring nonperformance pattern

### Example Fields

- `pattern_id`
- `case_id`
- `pattern_type`
- `pattern_label`
- `pattern_summary`
- `confidence_score`
- `status`
- `priority_score`

### Rule

Patterns must remain evidence-linked, explainable, and suitable for legal mapping.

---

## 7.13 Cause of Action

### Purpose

Represents a structured legal claim candidate or governed claim analysis object.

### Example Fields

- `coa_id`
- `case_id`
- `claim_type`
- `claim_label`
- `jurisdiction_ref`
- `support_status`
- `strength_score`
- `review_status`
- `attorney_disposition`

### Required Support Structures

A Cause of Action should support:

- linked legal elements
- supporting facts
- supporting events
- supporting patterns
- missing support records
- contradictory evidence records
- key witness references
- key document references

### Rule

No Cause of Action may exist as an unsupported conclusion.

---

## 7.14 Cause-of-Action Element Support

### Purpose

Represents support mapping between claim elements and graph evidence.

### Example Fields

- `coa_element_support_id`
- `coa_id`
- `element_key`
- `element_label`
- `support_status`
- `support_score`
- `missing_support_flag`
- `notes_ref`

### Rule

Element-level support must be structurally representable, not hidden in narrative text only.

---

## 7.15 Coverage

### Purpose

Represents measured support sufficiency and identified gaps for claims, issues, or event chains.

### Example Fields

- `coverage_id`
- `case_id`
- `coverage_scope_type`
- `coverage_scope_id`
- `coverage_status`
- `coverage_score`
- `gap_summary`
- `readiness_status`
- `generated_at`

### Rule

Coverage must be tied to explicit support structures rather than intuition alone.

---

## 7.16 Review / Approval State

### Purpose

Represents governed human review status for material objects.

### Example Fields

- `review_id`
- `case_id`
- `object_type`
- `object_id`
- `review_status`
- `reviewer_role`
- `reviewer_id_or_ref`
- `reviewed_at`
- `review_notes_ref`

### Rule

Review state should be modeled explicitly for material objects that require human governance.

---

## 7.17 Provenance

### Purpose

Represents the traceability chain from graph objects back to originating material and execution context.

### Provenance Must Support

- source references
- document references
- fragment references
- run references
- program references
- agent references where applicable
- timestamps
- derivation chains

### Example Fields

- `provenance_id`
- `case_id`
- `object_type`
- `object_id`
- `source_id`
- `document_id`
- `fragment_id`
- `run_id`
- `producer_type`
- `producer_name`
- `created_at`

### Rule

Every material graph object must be provenance-linkable.

---

## 7.18 Execution Reference

### Purpose

Represents the governed execution context under which a graph object was created or modified.

### Example Fields

- `execution_ref_id`
- `case_id`
- `run_id`
- `program_name`
- `agent_name`
- `lane_name`
- `contract_version`
- `created_at`

### Rule

Material mutations must be attributable to a governed execution context.

---

## 8. Canonical Link Structures

The graph should support many-to-many link tables or equivalent graph edges for at minimum:

- fact ↔ entity
- fact ↔ document
- fact ↔ fragment
- event ↔ fact
- event ↔ entity
- event ↔ document
- signal ↔ fact
- signal ↔ event
- pattern ↔ signal
- pattern ↔ event
- pattern ↔ fact
- coa ↔ pattern
- coa ↔ fact
- coa ↔ event
- coverage ↔ coa
- review ↔ object
- provenance ↔ object

These link structures are necessary for explainability and queryability.

---

## 9. Case Boundary Rules

### 9.1 Isolation Rule

Every graph object must belong to a single case boundary.

### 9.2 Cross-Case Prohibition

No graph object may link across cases unless future approved architecture explicitly introduces governed cross-case intelligence.

### 9.3 Query Rule

All graph reads and writes must be case-scoped by default.

---

## 10. Persistence Rules

### 10.1 Authoritative Persistence Rule

If a reasoning object affects legal interpretation, workflow, review, or downstream computation, it must be persistable in the Evidence Graph.

### 10.2 No Opaque Blob Rule

Material reasoning state must not exist only as opaque narrative text or agent scratchpad memory.

### 10.3 Structured Storage Rule

Narrative notes may exist, but core reasoning state must be represented with structured objects and links.

---

## 11. Determinism and Replay Implications

### 11.1 Write Determinism Rule

Writes into the Evidence Graph by Programs must be governed, auditable, and replay-compatible according to contract.

### 11.2 No Silent Mutation Rule

No material graph object may be created, changed, merged, or reclassified without governed execution and traceable provenance.

### 11.3 Replay Compatibility Rule

The graph model must support comparison of materially generated outputs across reruns where required.

---

## 12. UI Implications

The UI must treat the Evidence Graph as the authoritative source for:

- timeline views
- entity views
- document support views
- pattern review views
- cause-of-action support matrices
- coverage dashboards
- attorney review surfaces

The UI must not invent or retain separate authoritative copies of graph state.

---

## 13. Program Implications

The program layer maps into the Evidence Graph as follows:

- `program_FACT_NORMALIZATION` writes Facts and supporting provenance structures
- `program_COMPOSITE_ENGINE` writes Events and event-support links
- `program_PATTERN_ENGINE` writes Signals and Patterns
- `program_COA_ENGINE` writes Causes of Action and element support structures
- `program_COVERAGE_ENGINE` writes Coverage objects and identified gaps

Each program contract must define exact read/write boundaries against the graph.

---

## 14. Agent Implications

Agents may:

- read graph-backed context
- propose graph-bound structures through governed flows
- assist in refinement and review

Agents must not:

- silently mutate graph truth
- bypass provenance requirements
- create unsupported authoritative claim state

---

## 15. MVP Graph Minimum

The MVP Evidence Graph must support at minimum:

- Case
- Source Material
- Document
- Fragment
- Fact
- Entity
- Alias
- Relationship
- Event
- Signal
- Pattern
- Cause of Action
- Cause-of-Action Element Support
- Coverage
- Review State
- Provenance
- Execution Reference

---

## 16. Anti-Spaghetti Interpretation Rules

Interpret this document using the following maxims:

- **Documents are not the graph.**
- **Facts are not enough without links.**
- **Events require support.**
- **Patterns require traceability.**
- **Claims require element support.**
- **Coverage must reveal gaps.**
- **Everything material must be provenance-linked.**
- **Nothing important may live only in agent memory.**

---

## 17. Deferred Questions

The following are intentionally deferred to schema implementation and companion contracts:

- exact physical table names
- exact indexing strategy
- exact JSON vs relational field choices
- exact event taxonomy
- exact relationship ontology
- exact confidence scale
- exact merge and dedupe strategy
- exact versioning scheme for revised graph objects

These must not contradict the object model in this document.

---

## 18. Acceptance Criteria

This document is accepted when:

- all required reasoning objects have a persistent home
- provenance can link all material objects back to source support
- graph objects are case-bounded
- program read/write responsibilities can be defined without ambiguity
- UI surfaces can query authoritative structures directly
- no material reasoning depends on hidden memory alone

---

## 19. Final Directive

The Evidence Graph must be implemented as the platform’s authoritative, structured, provenance-linked case memory.

It is not a document folder, not a chatbot transcript store, and not a loose collection of notes.

It is the governed memory layer required for defensible litigation reasoning.

---

## 20. Summary Statement

The Evidence Graph stores the connected case objects that allow the platform to reason defensibly.

It preserves:

- source material,
- facts,
- entities,
- relationships,
- events,
- signals,
- patterns,
- causes of action,
- coverage,
- review state,
- and provenance

as one governed, queryable, case-bounded memory system.

That is the authoritative Evidence Graph model.