# Knowledge Contract v1
**Scope:** Brain Layer (Post-Spine Baseline v1.0-spine-stable)  
**Status:** Draft – Brain v1  
**Type:** Deterministic Knowledge Governance Specification  

---

# 1. Purpose

This document defines how the platform:

- Ingests external legal authority
- Stores structured legal knowledge
- Governs knowledge promotion
- Preserves determinism and replay integrity
- Enables adversarial reasoning (e.g., OPPOSITION_AGENT)

This contract does NOT modify the Spine.  
It extends capability through governed knowledge accumulation.

---

# 2. Design Principles

1. Spine remains immutable.
2. Knowledge grows through deterministic ingestion.
3. No auto-promotion to trusted authority.
4. Every knowledge object must have provenance.
5. Replay must remain deterministic.
6. Agents may consume trusted knowledge only by default.

---

# 3. Knowledge Object Types

The system recognizes the following knowledge object classes:

## 3.1 authority_text
Structured statutory or rule-based law.

Examples:
- CA Evidence Code sections
- CA Jury Instructions (data)
- Procedural rules

Required Fields:
- authority_id
- citation
- jurisdiction
- effective_date
- source_hash
- ingest_run_id
- trust_level

---

## 3.2 case_summary
Attorney-reviewed case analysis.

Required Fields:
- case_id
- court
- holding_summary
- cited_authority
- ingest_run_id
- review_status
- trust_level

---

## 3.3 burden_map
Mapping between:
- Cause of Action
- Elements
- Required proof
- Jury instruction linkage

Required Fields:
- coa_id
- element_id
- burden_description
- linked_authority_ids
- trust_level

---

## 3.4 heuristic_rule
Pattern recognition guidance.

Examples:
- “Conversion claims require demonstrable possession interference.”
- “Meet & Confer failures weaken Motion to Compel posture.”

Required Fields:
- heuristic_id
- description
- supporting_authority_ids
- risk_rating
- trust_level

---

## 3.5 practice_guide
Attorney-approved structured guidance.

Examples:
- Discovery strategy checklist
- MTC drafting checklist
- Opposition preparation flow

Required Fields:
- guide_id
- version
- author
- review_status
- trust_level

---

# 4. Trust Lifecycle

Every knowledge object must exist in one of the following states:

| State       | Description |
|------------|------------|
| candidate  | Ingested automatically; not authoritative |
| reviewed   | Human-reviewed; not yet system-trusted |
| trusted    | Approved for system-wide reasoning use |
| deprecated | No longer authoritative |

Only `trusted` knowledge is eligible for:
- OPPOSITION_AGENT reasoning
- Tactical strategy generation
- Automated burden evaluation

---

# 5. Deterministic Ingestion

All external research sources must be ingested via:

**program_KNOWLEDGE_INGESTION**

Characteristics:
- Deterministic
- Versioned
- Run-scoped (ingest_run_id)
- Hash-fingerprinted
- Produces structured knowledge objects only

No dynamic scraping during reasoning.

---

# 6. Provenance Requirements

Every knowledge object must include:

- source_identifier
- original_citation
- ingest_timestamp
- ingest_run_id
- content_hash
- jurisdiction
- effective_date
- trust_level

Failure to include provenance invalidates the object.

---

# 7. Promotion Gate

Promotion from `candidate` → `reviewed` → `trusted` requires:

1. Human approval event
2. Logged audit_ledger entry
3. Promotion metadata:
   - reviewer_id
   - approval_timestamp
   - justification_note

Promotion events must be replay-safe.

---

# 8. Agent Consumption Rules

By default:

- Agents may consume only `trusted` knowledge.
- Optional override must:
  - Be explicitly declared
  - Log audit event
  - Be scoped to run_id

OPPOSITION_AGENT must default to trusted-only mode.

---

# 9. Interaction With Replay

Knowledge objects used during reasoning must be:

- Version-pinned
- Query-filtered by trust_level
- Deterministically selectable

Replay equivalence requires:

- Same ingest_run_id
- Same trust snapshot
- Same knowledge query parameters

---

# 10. Data Layer Extension (Non-Spine Modification)

This Brain contract assumes the existence (or future addition) of:

- knowledge_objects table
- knowledge_promotions table
- knowledge_audit table

These are additive extensions and do not modify existing spine tables.

---

# 11. Governance Boundary

This contract:

- Does not modify contract_manifest.yaml enforcement rules.
- Does not alter validator core behavior.
- Does not modify overlay or config binding logic.

This is an additive intelligence layer.

---

# 12. Relationship to OPPOSITION_AGENT

OPPOSITION_AGENT shall:

- Query burden_map objects
- Identify missing element coverage
- Cross-reference authority_text
- Detect heuristic weaknesses
- Produce structured adversarial output

OPPOSITION_AGENT shall not:
- Modify knowledge objects
- Promote knowledge
- Override trust states

---

# 13. Future Expansion (Out of Scope for v1)

- Cross-jurisdiction intelligence
- Dynamic legal update monitoring
- Predictive outcome modeling
- ML-derived heuristic scoring

---

# 14. Status

Knowledge Contract v1 defines the Brain Layer governance model.

Future versions must:
- Preserve deterministic ingestion
- Preserve promotion gate enforcement
- Maintain replay integrity