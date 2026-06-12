# Authority Safety Rules
(v1 | Enforcement contract for case-scoped provisional CACI)

---

These rules are non-negotiable. Any code path or program that violates one of these rules is non-compliant and must be rejected at review.

## SR-1 — No silent promotion of provisional CACI

No code path may change a provisional CACI from `PROVISIONAL` or `BLOCKED_UNTRUSTED` to canonical certified authority. Promotion only occurs via a superseding record with `trust.canonical: true` and `provenance.certified: true`, produced by a certified-source pipeline — which does not yet exist in this contract version.

## SR-2 — No downstream final grounding from bare provisional candidate

A downstream mapper (COA / burden / remedy / complaint) may not emit a GROUNDED artifact on the basis of a provisional record alone. Grounding requires one of:

- `case_decision.state == ACCEPTED` (grounding = GROUNDED) OR
- `case_decision.state == REPLACED` (grounding = GROUNDED_VIA_REPLACEMENT) OR
- `certified.present == true` independent of CACI

`PROPOSED` artifacts may be produced as preview, watermarked `preview: true`, and excluded from export, pleading, and finalization gates.

## SR-3 — No direct provisional reads outside resolver

Only two modules may read `authority_packs/ca_caci_provisional/`:

1. `backend/brain/provisional_store.py` (the read accessor)
2. `backend/brain/authority_resolver.py` (consumes via provisional_store)

The `case_authority` routes are part of the Brain surface (Library, map, decision writes) and consume via provisional_store.

Any other module — COA route, burden mapper, remedy derivation, complaint parse, weapons, frontend — must route through `resolve_authority()` and consume the tri-signal block.

## SR-4 — Blocked / untrusted records cannot become grounded

- A record with `status: BLOCKED_UNTRUSTED` cannot be the target of an ACCEPTED decision. The decision-write route and the resolver both enforce this.
- A PENDING_REVIEW against a BLOCKED_UNTRUSTED record resolves to `effective_grounding: NONE`, not PROPOSED.

## SR-5 — Append-only decisions

Decisions are never edited. Reversals create a new row with `supersedes_decision_id` set. Resolver always uses the latest non-superseded decision.

## SR-6 — Pinning is stable

A case's ACCEPTED decision stays pinned to its `pinned_record_id` even if that record is globally superseded. Attorneys must issue a new decision to migrate to the new active record. Reproducibility over recency.

## SR-7 — Case scope isolation

A case decision applies only to its `case_id`. No cross-case inference, no global toggles from a case decision.

## SR-8 — Supersession, not overwrite

All state changes (provisional record updates, decision revisions) are supersession events. Prior records remain reachable (read-only) for audit.

## SR-9 — Every downstream artifact carries decision_id and pinned_record_id

Any downstream artifact (COA row, burden row, remedy row, pleading citation) that depended on a CACI must record `(decision_id, pinned_record_id)` at emission time. Artifacts produced without those fields are non-compliant.

## SR-10 — Complaint citation gate

Complaint/pleading output may cite a CACI only when:

- the resolved authority has `certified.present == true`, OR
- `case_decision.state == ACCEPTED` (with provisional footnote), OR
- `case_decision.state == REPLACED` (cite the replacement authority).

No bare provisional citation in any pleading.

## SR-11 — No authority resolution outside analysis or decision flow

`resolve_authority()` may be invoked only from:

1. `brain.analysis_runner.run_analysis(...)` during a PROCESSING run, OR
2. `POST /case-authority/decisions` when the case state is REVIEW_REQUIRED.

Save paths, ingest paths, document uploads, Dashboard reads, and any other surface MUST NOT invoke the resolver. Downstream read endpoints (`/coas/case/{id}`, `/case-authority/case/{id}/map`) serve from the snapshot columns on COA rows and the snapshotted tri-signal block persisted by the last analysis run. When a case is not yet in a post-analysis state, these endpoints return HTTP 409 with `{save_state, message}` rather than invoking the resolver.

## SR-12 — Ingest pipeline has no authority dependencies

The ingest pipeline (`brain.ingest_pipeline`, `brain.content_extractors`, `brain.actor_extractor`, `routes/documents.py`, `routes/actors.py`) MUST NOT import or call:

- `brain.authority_resolver`
- `brain.recompute`
- `routes/case_authority.py` (decision-write helpers)
- any COA / burden / remedy / complaint module

Save/upload triggers ingest only. Legal analysis triggers only on
`POST /cases/{id}/submit-for-analysis`, per SR-11 and
`program_CASE_SAVE_LIFECYCLE`.

Enforcement: `dev_sr12_audit.py` greps the ingest surface and fails if any of the
forbidden imports appear.

## Enforcement checkpoints

1. **Schema validation** — provisional record and case decision schemas reject missing fields.
2. **Decision-write route** — refuses ACCEPT over BLOCKED; requires rationale for REJECT; requires replacement for REPLACE.
3. **Resolver** — enforces transition rules; refuses to return GROUNDED against a BLOCKED record.
4. **Downstream routes** — never import from `brain.provisional_store`; only `brain.authority_resolver`.

## Review checklist (pre-merge)

- [ ] New downstream mapper does not import `brain.provisional_store`.
- [ ] New artifact shape carries `decision_id` and `pinned_record_id`.
- [ ] Preview rows on PROPOSED authority are watermarked.
- [ ] Complaint paths gate on ACCEPTED/REPLACED/certified.
- [ ] Decision transitions tested: PENDING→ACCEPTED, ACCEPTED→REJECTED, REJECTED→REPLACED.
