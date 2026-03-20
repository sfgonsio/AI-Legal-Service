# CASECORE BUILD SPEC (Authoritative Execution Guide)

## 1. Purpose

This document defines the **complete execution specification** for building the CASECORE platform.

It is written for engineers to implement the system **without interpretation, assumption, or invention**.

All behavior must conform to:
- `/casecore-spec` (authoritative source)
- contracts, schemas, and workflows defined therein

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

### 2.3 Deterministic Execution
- identical inputs must produce identical outputs
- all workflows must be replayable
- all state transitions must be explicit

### 2.4 AI Constraint
- AI outputs are ALWAYS proposals
- AI cannot write canonical data
- promotion requires governed workflow + human approval

---

## 3. System Architecture Model

CASECORE is a **deterministic, contract-driven litigation system** composed of:

### Core Layers
1. Data Layer (canonical artifacts)
2. Workflow Layer (state transitions)
3. Contract Layer (schemas + APIs)
4. Program Layer (deterministic transformations)
5. AI Proposal Layer (non-authoritative)
6. Review & Promotion Layer (human governance)
7. Frontend Layer (truth-labeled UI)

---

## 4. Canonical Processing Flow

1. Input
2. Fact Normalization
3. Tagging
4. Event / Composite Mapping
5. COA Mapping
6. AI Proposal Generation (non-authoritative)
7. Review Workflow
8. Promotion to Canonical State

---

## 5. Build Sequence (MANDATORY ORDER)

### Phase 1 — Data Foundation
Implement:
- DATABASE_SCHEMA.sql
- DATA_MODEL.md
- ENTITY_RELATIONSHIP_MODEL.md

Requirements:
- strict schema enforcement
- no nullable ambiguity unless defined
- indexing strategy implemented

---

### Phase 2 — Contract Layer
Implement:
- all JSON schemas
- all YAML enums
- all API contracts

Requirements:
- schema validation required at boundaries
- no payload accepted without validation

---

### Phase 3 — Workflow Engine
Implement:
- state_transitions.yaml
- STATE_TRANSITION_MATRIX.md

Requirements:
- no illegal transitions allowed
- every state change must emit an event
- transitions must be auditable

---

### Phase 4 — Program Execution Layer
Implement:
- program_FACT_NORMALIZATION
- program_TAGGING
- program_COMPOSITE_ENGINE
- program_COA_ENGINE

Requirements:
- deterministic logic only
- no AI in program layer
- full traceability per output

---

### Phase 5 — Audit + Event System
Implement:
- audit schema
- audit events
- event bus

Requirements:
- every mutation produces an audit record
- idempotent event handling
- retry-safe processing

---

### Phase 6 — AI Proposal Subsystem
Implement:
- agent_INTERVIEW_AGENT
- agent_MAPPING_AGENT
- agent_COA_REASONER

Requirements:
- all outputs wrapped in proposal envelope
- no direct DB writes
- prompt catalog enforced

---

### Phase 7 — Review & Promotion
Implement:
- artifact promotion APIs
- review status workflows

Requirements:
- promotion requires explicit approval
- audit chain must link proposal → decision → promotion

---

### Phase 8 — Frontend
Implement:
- view model policy
- truth labeling rules
- component system

Requirements:
- canonical vs proposal must be visually distinct
- no UI state divergence from backend truth

---

### Phase 9 — Security & Ops
Implement:
- authorization matrix
- resiliency model
- retry model

Requirements:
- role-based access enforced
- failure recovery deterministic

---

### Phase 10 — Validation
Validate against:
- fixture inputs
- expected outputs
- traceability matrix

Requirements:
- outputs must match expected fixtures exactly
- traceability must be complete

---

## 6. Data Integrity Rules

- all canonical records must be versioned
- no destructive updates without audit
- relationships must remain consistent
- foreign keys must be enforced

---

## 7. Eventing Rules

- every state change emits an event
- events must be immutable
- consumers must be idempotent

---

## 8. Error Handling Rules

- all errors must be typed
- no silent failures
- retry must be safe and deterministic

---

## 9. Definition of Done

The system is complete when:

- all schemas validate
- all workflows enforce state transitions
- all programs produce deterministic outputs
- AI remains non-authoritative
- fixtures pass exactly
- traceability is complete
- audit logs are complete and queryable
- frontend reflects truth accurately

---

## 10. Final Instruction to Builders

Do not:
- invent behavior
- simplify contracts
- bypass validation
- merge canonical and proposal states

If something is unclear:
→ resolve in `/casecore-spec` before implementation

---

## 11. Build Philosophy

This system is designed to:
- eliminate ambiguity
- enforce legal-grade traceability
- separate reasoning from truth
- ensure reproducibility

The goal is not speed.

The goal is:
**correctness, determinism, and defensibility**
