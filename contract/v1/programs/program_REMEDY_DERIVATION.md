# program_REMEDY_DERIVATION
(Authoritative Program Contract — v1 | Downstream Surface)

---

## 1. Purpose

Derive remedies for each COA from GROUNDED or GROUNDED_VIA_REPLACEMENT authority only. Remedies may NOT be computed from bare provisional candidates.

## 2. Inputs

- COA rows for the case
- Resolved authority block per COA (from Brain resolver)

## 3. Rules

- For each COA, read `authority.effective_grounding`:
  - `GROUNDED` or `GROUNDED_VIA_REPLACEMENT` → emit remedy rows.
  - `PROPOSED` → emit a **preview** remedy row, watermarked `preview: true`. Preview rows are not eligible for complaint export.
  - `NONE` → emit no remedy.
- Every remedy row carries `(decision_id, pinned_record_id)` from the COA's authority block.
- When a REPLACED decision redirects, remedies derive from the replacement authority, not the original CACI.

## 4. Recomputation

On `CASE_AUTHORITY_DECISION_UPDATED` event, re-derive remedies for all COAs whose `caci_ref` matches the updated `caci_id`. Prior remedy rows are superseded, not overwritten. See `program_AUTHORITY_IMPACT_ANALYSIS`.

## 5. Non-Goals

- No direct reads of provisional records.
- No inference of replacements — REPLACED decisions carry the replacement.
