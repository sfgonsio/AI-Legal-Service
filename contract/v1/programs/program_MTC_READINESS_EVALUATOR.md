# Program Contract: MTC_READINESS_EVALUATOR
**Version:** v1  
**Layer:** Brain (Post-Spine Baseline v1.0-spine-stable)  
**Type:** Deterministic Program (Non-Agent)  
**Status:** Brain v1  

---

# 1. Purpose
MTC_READINESS_EVALUATOR deterministically evaluates whether a Motion to Compel is:
- blocked (missing prerequisites)
- ready (record complete)
- recommended (materiality threshold met)

It outputs a court-ready readiness packet for attorney review.

---

# 2. Inputs
Required:
- discovery_request records
- discovery_response records (or proof of non-response)
- deficiency_items (matrix)
- meet_and_confer_events + artifacts
- case COA mapping (optional but recommended for materiality scoring)

Config:
- jurisdiction
- materiality thresholds
- required meet & confer minimums (e.g., at least 1 attempt + follow-up)

---

# 3. Outputs
Canonical:
- artifacts/mtc/mtc_readiness.json
- artifacts/mtc/deficiency_matrix.json
- artifacts/mtc/exhibit_list.json
- artifacts/mtc/declaration_facts.md (draft factual chronology for attorney editing)

Each artifact includes:
- run_id
- timestamps
- deterministic ordering keys
- citations to stored artifacts (requests/responses/emails)

---

# 4. Deterministic Evaluation Rules
## 4.1 Prerequisite Checks (Blockers)
Mark BLOCKED if any are missing:
- request not recorded with served_date
- response not recorded and no proof of non-response
- deficiency matrix absent
- meet & confer absent or lacks artifact proof
- commitments/deadlines unclear

## 4.2 Materiality Scoring
Compute score per deficiency_item:
- critical element gap → high weight
- credibility/damages → medium weight
- procedural defect only → lower weight

Recommend MTC if:
- unresolved materiality score ≥ threshold
AND
- prerequisites satisfied

## 4.3 Output Assembly
Generate:
- deficiency matrix (stable sorted by materiality desc, date asc)
- exhibit list (requests, responses, M&C letters/emails, call memos)
- declaration facts chronology (events sorted by date)

---

# 5. Traceability & Citation Requirements
Every readiness assertion must cite:
- request artifact
- response artifact (or non-response proof)
- meet & confer artifact
- deficiency mapping

No citations → readiness item invalid.

---

# 6. Governance
This program:
- does not file motions
- does not provide final legal arguments
- produces packets for attorney review only

Attorney approval gate required for filing.

---

# 7. Audit Events
- mtc_readiness_run_started
- mtc_prerequisites_checked
- mtc_readiness_emitted
- mtc_blocked_emitted (if blocked)
- mtc_recommended_emitted (if recommended)

---

# 8. Acceptance Tests (Brain v1)
Minimum acceptance:
- With fixture discovery record, outputs:
  - blocked when meet & confer artifacts missing
  - ready when artifacts present
  - recommended when materiality exceeds threshold
- 100% readiness items include citations