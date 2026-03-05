# Case Signal Model — Contract v1

**Status:** SSOT (authoritative)  
**Purpose:** Define the canonical case-layer structure used across interview, document ingestion, burden mapping, and coverage.

---

## 1. Philosophy

The platform does not “understand the case” by intuition. It builds a case model by collecting and normalizing **signals**.

Signals are:
- structured observations derived from client statements or documents
- attached to citations
- tagged with confidence and provenance

Signals are not:
- legal conclusions
- attorney advocacy
- speculative narrative

---

## 2. Universal Core Signal Families (All Civil Cases)

These families are general enough to represent any case type:

- **parties**: persons/orgs, roles, relationships
- **events**: actions/occurrences; who/what/when/where
- **damages**: harm type, amount, causation links, timeline
- **documents**: referenced or uploaded documents with metadata
- **communications**: messages, notice, admissions, demands
- **statute_mentions**: explicit legal hooks mentioned by client or documents (optional early)

These are often present but may be empty depending on case type:
- **agreements**: contracts, terms, assent, performance
- **ownership_claims**: assets, brand, IP, chain of title, control/possession

---

## 3. Archetype Hypotheses (Case Type Without Overclaiming)

Clients often do not know their legal case type. The system uses a hypothesis model:

- `archetype_hypotheses[]`:
  - `archetype_id`
  - `confidence` (0–1)
  - `why_signals[]` (citations)
  - `disambiguation_questions[]` (to confirm/refute)

**Rule:** the system speaks in “may involve” / “working hypothesis” language.

---

## 4. Signal Record Requirements (Per Signal)

Each signal record must include:
- `signal_id` (stable ID)
- `signal_type` (taxonomy)
- `attributes` (structured fields)
- `source` (interview | document | system)
- `confidence` (unverified | corroborated | verified)
- `citations[]` (doc_uid / chunk_uid / interview_turn refs)
- `created_at` timestamp

---

## 5. How Signals Evolve (Living Case Model)

Signals change over time:
- interview creates initial unverified signals
- documents corroborate or refute
- discovery and deposition add precision

**Rule:** new evidence updates confidence, never silently overwrites.

---

## 6. Outputs Built from the Case Signal Model

- burden map coverage report
- interview next-question suggestions (gap-driven)
- evidence requests and hygiene checks
- discovery themes and readiness evaluation (no drafting)

---

## 7. Acceptance Criteria

The model is correct when:
- it supports multiple archetypes without schema changes
- it is auditable (citations on every critical signal)
- it avoids legal conclusions while still guiding structured intake