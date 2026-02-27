# deterministic_program_spine
(Authoritative Implementation Rollup — Contract v1)

---

## 1. Purpose

This document defines the deterministic execution backbone of Contract v1.

It connects the individual program contracts into a single, coherent execution spine and clarifies:

- Execution order and dependencies
- Authoritative vs proposal artifacts
- Deterministic vs agent reasoning boundaries
- What each program is allowed and forbidden to do
- The structural guarantees required to support reliable, citation-backed attorney queries

If any conflict exists, individual program contracts govern.

---

## 2. Architectural Alignment

This spine is consistent with:

- Section 7 layered architecture
- Agents vs Programs separation
- Tool Gateway mediation
- Write Broker enforcement
- Case isolation
- Audit ledger requirements
- Manifest hash-lock validation

Programs are deterministic-only.
Agents may reason but may not write canonical artifacts outside governance lanes.

---

## 3. Canonical Deterministic Flow

### 3.1 Backbone Order

1) PROCESSING (Documents + Chunks)
2) program_FACT_NORMALIZATION
3) program_TAGGING
4) program_COMPOSITE_ENGINE
5) MAPPING_AGENT
6) program_COA_ENGINE
7) Retrieval / Query Answering

### 3.2 Core Design Principle

Programs produce structured artifacts.
Agents produce proposals and relationships.

No program invents meaning.
No agent mutates canonical artifacts directly.

---

## 4. Canonical Artifact Classes

### 4.1 Authoritative Artifacts

- Documents / Chunks indexes
- EvidenceFacts
- TagAssignments
- EventCandidates (as candidate structures, not “truth events”)
- COA Element Coverage Matrix

These artifacts are deterministic, versioned, and hash-locked.

### 4.2 Proposal / Advisory Artifacts

- Narrative summaries
- Strategy explanations
- Candidate tag suggestions (if ever implemented)
- Argumentation layers (e.g., COA_REASONER)

Proposal artifacts must never overwrite authoritative artifacts.

---

## 5. Program Responsibilities (Spine Summary)

### 5.1 PROCESSING
Decomposes uploads into stable indexed artifacts.

Guarantee:
- Immutable chunk ids
- Stable document hashes
- Reproducible parsing

---

### 5.2 program_FACT_NORMALIZATION
Converts extracted signals into atomic, citation-backed EvidenceFacts.

Guarantee:
- ≥1 evidence citation per fact
- No synthesis
- No legal meaning

---

### 5.3 program_TAGGING
Applies controlled vocabulary tags deterministically.

Guarantee:
- Tags are indexing only
- Only vocabulary-approved tags allowed
- All assignments include rule provenance

---

### 5.4 program_COMPOSITE_ENGINE
Clusters related facts into EventCandidates.

Guarantee:
- Must reference supporting_fact_ids
- Must surface confidence and conflicts
- Must not invent facts
- Produces candidates, not authoritative truth

---

### 5.5 MAPPING_AGENT
Aligns story claims to evidence and candidate events.

Guarantee:
- May propose edges
- Must cite canonical artifacts
- Cannot mutate EvidenceFacts, EventCandidates, or TagAssignments

---

### 5.6 program_COA_ENGINE
Evaluates COA element coverage deterministically.

Guarantee:
- Structural evaluation only
- No narrative persuasion
- No element marked supported without explicit evidence links
- Tags are filters only, not proof

---

## 6. Attorney Query Reliability Model

The system answers reliably because:

- Evidence is decomposed into stable chunks
- Facts are atomic and citation-backed
- Tags narrow retrieval scope
- Composite clustering manages scale
- Mapping connects story claims to artifacts
- COA coverage measures legal sufficiency structurally

All query outputs must be traceable to:
- doc_id
- chunk_id
- fact_id
- event_candidate_id (if used)

No citation → no claim.

---

## 7. Non-Negotiable Guardrails

1. Tagging never becomes synthesis.
2. Composite never becomes authoritative truth.
3. COA_ENGINE never becomes narrative.
4. Agents cannot write canonical state directly.
5. All canonical writes go through Write Broker.
6. All artifacts are case-scoped.
7. Manifest hash-lock enforcement prevents drift.

These guardrails prevent architectural spaghetti.

---

## 8. Determinism Contract

The deterministic spine requires:

- Versioned rulesets for normalization, tagging, composite, and COA evaluation
- Identical inputs + identical ruleset versions = identical outputs
- Reruns required when upstream artifacts change
- Full provenance logging for every program execution

---

## 9. Optional Extension Points (Non-Authoritative)

The following may be added without altering the deterministic spine:

- program_TAG_CANDIDATE_SUGGESTER (non-authoritative suggestions)
- agent_COA_REASONER (narrative explanation layer)
- Attorney promotion workflows for EventCandidates

These extensions must not modify canonical artifacts automatically.

---

## 10. Version Control Discipline

This file is SSOT.

Any modification requires:
- Manifest inventory update
- SHA256 hash update
- Successful validate_contract.ps1 execution
- Clear commit messaging referencing contract impact