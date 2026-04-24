# program_CASE_TO_AUTHORITY_MAPPING
(Authoritative Program Contract — v1 | Downstream Surface)

---

## 1. Purpose

Produce the per-case view of every CACI touched by that case and its current resolved authority state. This is the attorney's decision surface.

## 2. Output shape

A list of rows, one per CACI in scope:

```
{
  caci_id,
  authority: {
    certified,
    provisional_candidate,
    case_decision,
    effective_grounding,
    display_badge,
    decision_id,
    pinned_record_id
  }
}
```

## 3. Source of truth

Rows are produced by calling Brain resolver for each `(case_id, caci_id)`. No direct reads of provisional store or case decision table.

## 4. Consumers

- Legal Library UI
- Attorney review queue (filter `requires_attorney_review == true`)
- Complaint mapping pre-flight gate
- Case-readiness dashboard

## 5. Invariants

- CACIs not in the provisional manifest are not surfaced.
- Decisions pinned to superseded record_ids remain active and are surfaced with their original pinned record.
