# program_CASE_AUTHORITY_DECISION
(Authoritative Program Contract — v1 | Case-Scoped Authority Governance)

---

## 1. Purpose

Manage per-case, per-CACI attorney decisions about provisional CACI authority. A decision governs future use of that CACI for the balance of that case — and nothing outside that case.

## 2. Architectural Position

Downstream of: `program_CACI_PROVISIONAL_INGEST`.
Upstream of: Brain authority resolver, all downstream mappers (COA, burden, remedy, complaint).

## 3. States

- `PENDING_REVIEW` — default/implicit when no decision exists.
- `ACCEPTED` — CACI is grounded for this case, pinned to a specific provisional `record_id`.
- `REJECTED` — CACI is excluded for this case. Downstream must drop dependent rows.
- `REPLACED` — Original CACI is swapped for a replacement authority for this case.

## 4. Append-only history

- Decisions are never edited. A reversal or revision creates a new decision with `supersedes_decision_id` set.
- Historical decisions remain queryable; they must not be deleted.
- Resolver always uses the latest non-superseded decision.

## 5. Pinning

- `pinned_record_id` locks the decision to a specific provisional record version.
- Global supersession of that record does **not** move the decision to the new version. Reproducibility > recency.
- Attorney may issue a new decision pinned to the new active record.

## 6. Scope

- A decision applies **only** to its `case_id`. No global effect. No cross-case inference.

## 7. Transitions

Any state may transition to any state via a new decision record:
- PENDING_REVIEW → ACCEPTED | REJECTED | REPLACED
- ACCEPTED → REJECTED | REPLACED | (re-ACCEPTED at different pinned_record_id)
- REJECTED → ACCEPTED | REPLACED
- REPLACED → ACCEPTED | REJECTED | (re-REPLACED with different replacement)

## 8. Invariants

- ACCEPTED requires `pinned_record_id`.
- REPLACED requires `replacement` populated with `authority_type`, `authority_id`, `reason`.
- REJECTED requires `rationale`.
- No ACCEPTED decision may be written against a record whose status was BLOCKED_UNTRUSTED at decision time — the resolver will refuse it.
- Decisions for the same (case_id, caci_id) form a chain via `supersedes_decision_id`.

## 9. Outputs

- Database row in `case_authority_decisions` (append-only).
- Emission of `CASE_AUTHORITY_DECISION_UPDATED` event to trigger recompute (see `program_AUTHORITY_IMPACT_ANALYSIS`).

## 10. Human Interaction

- Attorneys issue decisions via the Legal Library / Case Authority surface.
- Paralegals may issue PENDING_REVIEW updates but not ACCEPTED/REJECTED/REPLACED without attorney role.
- SYSTEM may only issue PENDING_REVIEW synthesized defaults.

## 11. Audit

Every decision carries `audit.hash` = sha256 over canonicalized fields. `source_event` links to the UI action or agent event that produced it.

## 12. Non-Goals

- Not a place to rewrite provisional records.
- Not a place to certify authority globally.
- Not a substitute for provenance on the provisional record itself.
