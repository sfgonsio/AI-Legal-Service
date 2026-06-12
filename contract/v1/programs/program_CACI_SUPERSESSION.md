# program_CACI_SUPERSESSION
(Authoritative Program Contract — v1 | Provisional Authority Layer)

---

## 1. Purpose

Replace a prior provisional CACI record with a new one **without overwriting** the prior. Preserves full history for audit and case-scoped reproducibility.

## 2. Inputs

- `new_record` (validated against `caci_provisional_record.schema.json`)
- `prior_record_id` — the record being superseded

## 3. Pipeline

1. Load prior record from `records/<caci_id>.yaml`.
2. Verify `prior_record_id` matches.
3. On prior:
   - set `superseded_by = new_record.record_id`
   - set `status = SUPERSEDED`
   - move file from `records/<caci_id>.yaml` to `superseded/<caci_id>__<prior_record_id>.yaml` (read-only).
4. On new record:
   - set `supersedes = prior_record_id`
5. Write new record to `records/<caci_id>.yaml`.
6. Update `manifest.yaml` active entry.
7. Append manifest `superseded` entry: `{caci_id, prior_record_id, superseded_by, at}`.

## 4. Invariants

- Superseded records are **read-only** from then on.
- Case authority decisions pinned to a superseded `record_id` remain valid — the pinned record is still reachable under `superseded/`.
- Supersession never retroactively changes a prior case's grounded artifacts.

## 5. Case-Decision Impact

Supersession **does not** alter case decisions. A case that ACCEPTED record_id X continues to use X (now in `superseded/`), not the new active record. Re-review is the attorney's choice, via a new case decision.

## 6. Certification Pathway

When a future certified source for the same CACI is produced, it is also written as a superseding record — but with `trust.canonical: true` and `provenance.certified: true`. That is the **only** path from provisional to canonical. No silent promotion.

## 7. Failure Modes

- `prior_record_id` mismatch → abort, no changes.
- New record fails schema validation → abort.
- New record has `status: BLOCKED_UNTRUSTED` → still written (for audit), but the manifest flags it; attorneys see a blocked state, not a silent demotion of the prior active record.
