# CASECORE BUILD SPEC (Authoritative Execution Guide)

## 1. Purpose

This document defines the complete execution specification for building the CASECORE platform.

It is written for engineers to implement the system without interpretation, assumption, or invention.

All behavior must conform to:
- `/casecore-spec` (authoritative source)
- contracts, schemas, workflows, and governance files defined therein

---

## 2. Non-Negotiable Rules

### 2.1 Source of Truth
- `/casecore-spec` is the ONLY authoritative source
- `/casecore-build-kit` is derived and must not introduce new logic
- any ambiguity must be resolved in `/casecore-spec`, not locally

### 2.2 No Silent Behavior
- no implicit defaults
- no inferred state transitions
- no hidden transformations
- no undocumented fallback behavior

### 2.3 Deterministic Execution
- identical inputs must produce identical outputs
- all workflows must be replayable
- all state transitions must be explicit
- canonical IDs must be stable under identical inputs

### 2.4 AI Constraint
- AI outputs are ALWAYS proposals
- AI cannot write canonical data
- AI cannot approve promotion
- promotion requires governed workflow plus authorized review

---

## 3. System Architecture Model

CASECORE is a deterministic, contract-driven litigation system composed of:

### Core Layers
1. Data Layer (canonical artifacts)
2. Workflow Layer (state transitions)
3. Contract Layer (schemas, APIs, events, enums, audit rules)
4. Program Layer (deterministic transformations)
5. AI Proposal Layer (non-authoritative)
6. Review and Promotion Layer (human governance)
7. Frontend Layer (truth-labeled UI)

---

## 4. Canonical Processing Flow

The system SHALL process all case data through the following deterministic pipeline:

1. Input Sources
   - raw documents
   - structured intake
   - governed metadata

2. Fact Normalization
   Input:
   - source documents
   - source text/chunks
   Output:
   - fact proposal artifacts

   Constraints:
   - each fact must trace to source
   - no hidden inference
   - provenance required

3. Tagging
   Input:
   - facts
   Output:
   - tag assignments or tag proposals

   Constraints:
   - tags must come from governed taxonomy
   - no freeform canonical tags

4. Event / Composite Mapping
   Input:
   - facts
   - tag assignments
   Output:
   - event proposals
   - composite/event-support structures

   Constraints:
   - relationships must be explicit
   - conflict must not be silently collapsed

5. COA Mapping
   Input:
   - facts/events
   - COA library
   Output:
   - COA element coverage structures

   Constraints:
   - coverage is not legal sufficiency
   - gaps must remain visible

6. AI Proposal Generation (non-authoritative)
   Input:
   - canonical and governed support artifacts
   Output:
   - proposal artifacts only

   Constraints:
   - no canonical mutation
   - citations/source refs required where applicable

7. Review Workflow
   Input:
   - proposals
   Output:
   - review decisions
   - approval/rejection/override state

8. Promotion to Canonical State
   Input:
   - approved proposals
   Output:
   - canonical artifacts or canonical updates

   Constraints:
   - promotion must preserve full audit chain
   - promotion must follow governed state transitions

---

## 5. Artifact Model

The system SHALL operate on the following artifact classes.

### 5.1 Canonical Artifacts
Authoritative system-of-record artifacts, including:
- DOCUMENT
- FACT
- TAG_ASSIGNMENT
- EVENT
- COMPOSITE
- COA_ELEMENT_COVERAGE

Rules:
- canonical artifacts are versioned
- canonical artifacts must include provenance metadata where applicable
- canonical artifacts must be auditable

### 5.2 Proposal Artifacts
Non-authoritative artifacts, including:
- PROPOSAL_FACT
- PROPOSAL_TAG
- PROPOSAL_EVENT
- PROPOSAL_NARRATIVE
- PROPOSAL_DISCOVERY_GAP

Rules:
- proposal artifacts cannot overwrite canonical artifacts directly
- proposal artifacts must reference supporting inputs
- proposal artifacts must carry proposal metadata

### 5.3 Audit Artifacts
Governance and traceability artifacts, including:
- AUDIT_EVENT
- STATE_TRANSITION
- PROMOTION_RECORD
- OVERRIDE_RECORD

Rules:
- audit artifacts are append-only
- audit artifacts are immutable once recorded

---

## 6. Build Sequence (MANDATORY ORDER)

### Phase 1 — Data Foundation
Implement:
- DATABASE_SCHEMA.sql
- DATA_MODEL.md
- ENTITY_RELATIONSHIP_MODEL.md

Requirements:
- strict schema enforcement
- no nullable ambiguity unless defined
- indexing strategy implemented

### Phase 2 — Contract Layer
Implement:
- all JSON schemas
- all YAML enums
- all API contracts
- all event contracts
- audit contracts

Requirements:
- schema validation required at boundaries
- no payload accepted without validation

### Phase 3 — Workflow Engine
Implement:
- state_transitions.yaml
- STATE_TRANSITION_MATRIX.md

Requirements:
- no illegal transitions allowed
- every material state change must emit an event
- transitions must be auditable

### Phase 4 — Program Execution Layer
Implement:
- program_FACT_NORMALIZATION
- program_TAGGING
- program_COMPOSITE_ENGINE
- program_COA_ENGINE

Requirements:
- deterministic logic only
- no AI in deterministic program layer
- full traceability per output

### Phase 5 — Audit and Event System
Implement:
- audit schema
- audit events
- event bus handling

Requirements:
- every material mutation produces an audit record
- idempotent event handling
- retry-safe processing

### Phase 6 — AI Proposal Subsystem
Implement:
- agent_INTERVIEW_AGENT
- agent_MAPPING_AGENT
- agent_COA_REASONER

Requirements:
- all outputs wrapped in proposal envelope
- no direct DB writes
- prompt catalog enforced

### Phase 7 — Review and Promotion
Implement:
- artifact promotion APIs
- review status workflows

Requirements:
- promotion requires explicit approval
- audit chain must link proposal to decision to promotion

### Phase 8 — Frontend
Implement:
- view model policy
- truth labeling rules
- component system
- design system constraints

Requirements:
- canonical vs proposal must be visually distinct
- no UI state divergence from backend truth

### Phase 9 — Security and Ops
Implement:
- authorization matrix
- resiliency model
- retry model
- privileged content handling

Requirements:
- role-based access enforced
- failure recovery deterministic

### Phase 10 — Validation
Validate against:
- fixture inputs
- expected outputs
- traceability matrix
- integrated-system review requirements

Requirements:
- outputs must match expected fixtures
- traceability must be complete

---

## 7. Program Contract Rules

Each deterministic program MUST define:
- explicit input schema
- explicit output schema
- no side effects outside defined outputs
- run metadata
- provenance behavior

### 7.1 program_FACT_NORMALIZATION
Input:
- DOCUMENT
- source text/chunks

Output:
- FACT proposal artifacts

Rules:
- no hidden interpretation
- no uncontrolled deduplication
- provenance required

### 7.2 program_TAGGING
Input:
- FACT artifacts
- governed taxonomy

Output:
- TAG assignments or tag proposals

Rules:
- controlled taxonomy only
- deterministic mapping where designated

### 7.3 program_COMPOSITE_ENGINE
Input:
- FACT artifacts
- TAG assignments

Output:
- EVENT proposals
- COMPOSITE structures

Rules:
- relationship rules must be explicit
- conflict handling must remain visible

### 7.4 program_COA_ENGINE
Input:
- governed facts/events
- COA library

Output:
- COA_ELEMENT_COVERAGE

Rules:
- mapping must align to legal schema
- coverage must not be mislabeled as sufficiency

---

## 8. Proposal Envelope Specification

All AI-originated outputs MUST conform to a proposal envelope with the following minimum fields:

- proposal_id
- proposal_type
- matter_id
- run_id
- schema_version
- source_refs
- payload
- model_metadata
- created_at

Rules:
- no proposal may directly modify canonical data
- proposal type must be declared
- source refs must be present where applicable
- model metadata must identify provider, model, and prompt version

---

## 9. Promotion and State Transition Rules

### 9.1 Proposal States
- PROPOSED
- UNDER_REVIEW
- APPROVED
- REJECTED
- PROMOTED

### 9.2 Rules
- only approved proposals may be promoted
- promotion must create or update canonical state through governed services
- all transitions must be logged
- direct PROPOSED to PROMOTED is invalid unless explicitly governed and documented

### 9.3 Canonical Protection
- canonical artifacts may not be altered by direct AI output
- canonical changes must preserve lineage and audit history

---

## 10. Deterministic Identity Rules

All canonical entities must have stable identity rules.

Examples:
- FACT identity should be deterministically derivable from source and content rules
- EVENT identity should be deterministically derivable from component support structures
- TAG identity should use controlled vocabulary keys

Rules:
- no uncontrolled random canonical identity assignment
- identical governed inputs must produce identical canonical identity outcomes

---

## 11. Replay and Reproducibility Rules

The system MUST support replay using:
- same inputs
- same configuration
- same taxonomy
- same contract versions

Expected result:
- materially identical deterministic outputs
- auditable equivalence review where required

Rules:
- replay mismatches must be detectable
- silent replay drift is not allowed

---

## 12. Data Integrity Rules

- all canonical records must be versioned where applicable
- no destructive updates without audit
- relationships must remain consistent
- foreign keys and referential integrity must be enforced where applicable
- orphaned canonical references are not allowed

---

## 13. Eventing Rules

- every material state change emits an event
- events must be immutable once recorded
- consumers must be idempotent where repeated delivery is possible
- retry must not create duplicate canonical mutations

---

## 14. Error Handling Rules

- all material errors must be typed
- no silent failures
- retry must be safe and deterministic
- validation failures must reject writes, not coerce them silently
- authorization failures must deny and log where governed

---

## 15. Definition of Done

The system is complete when:

- all schemas validate
- all workflows enforce governed state transitions
- all deterministic programs produce deterministic outputs
- AI remains non-authoritative until governed promotion
- fixture inputs produce expected outputs
- traceability is complete
- audit logs are complete and queryable
- frontend reflects truth accurately
- security and authorization controls behave as specified

---

## 16. Final Instruction to Builders

Do not:
- invent behavior
- simplify contracts
- bypass validation
- merge canonical and proposal states
- hide conflict or unsupported states

If something is unclear:
- resolve it in `/casecore-spec` before implementation

---

## 17. Build Philosophy

This system is designed to:
- eliminate ambiguity
- enforce legal-grade traceability
- separate reasoning from truth
- ensure reproducibility
- preserve attorney control

The goal is not speed.

The goal is:
correctness, determinism, and defensibility
