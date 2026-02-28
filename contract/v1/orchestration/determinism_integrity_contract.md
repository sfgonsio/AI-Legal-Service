# determinism_integrity_contract
(Authoritative Determinism & Run Integrity Contract â€” v1)

---

## 1. Purpose

This contract defines deterministic run integrity requirements for Contract v1.

It governs:
- inputs_fingerprint semantics (stable input set identity)
- run_fingerprint semantics (run configuration identity)
- canonical artifact metadata requirements
- replay determinism expectations
- mixed-run query prohibition enforcement

This contract is **authoritative** for orchestration, Write Broker metadata, and query safety.

---

## 2. Definitions

**inputs_fingerprint**  
A SHA-256 fingerprint computed from the *set of uploads* (stable under ordering), including each uploadâ€™s raw_sha256 and identifying metadata.

**run_fingerprint**  
A SHA-256 fingerprint computed from:
- case_id
- contract_version
- inputs_fingerprint
- ruleset versions
- policy_version
- rerun_level

**Canonical artifact**  
Any persisted artifact used for active retrieval (facts, tags, composites, mappings, COA outputs, reasoner outputs).

---

## 3. Canonical Requirements

All canonical artifacts MUST include:
- case_id
- run_id
- inputs_fingerprint
- run_fingerprint
- contract_version
- produced_timestamp_utc
- ruleset version bundle (parser/normalization/tagging/composite/coa/policy)
- supersedes_run_id (if applicable)

No canonical artifact may be stored without these fields.

---

## 4. Replay Determinism Rule

Given:
- identical uploads (same inputs_fingerprint)
- identical contract_version
- identical ruleset versions
- identical policy_version
- identical rerun_level

Then:
- run_fingerprint MUST match
- canonical artifacts MUST be identical (content-addressable equivalence or byte-for-byte where applicable)

No silent nondeterminism is allowed.

---

## 5. Mixed-Run Prohibition

Active query responses MUST NOT mix:
- artifacts with different run_id OR
- artifacts with different run_fingerprint

Unless:
- user explicitly selects a historical run_id AND
- the system switches context fully to that historical run

---

## 6. Governance & Enforcement

Blocking validation failures include:
- missing run_identity_fingerprints SSOT
- missing required fingerprint fields in SSOT
- missing manifest wiring of the SSOT file
- any system behavior that produces mixed-run responses

This contract is enforced by:
- validator rules
- harness replay checks
- audit ledger controls

---
