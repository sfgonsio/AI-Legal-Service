# Case Authority Resolution (Brain)

## Purpose

Single entry point by which downstream surfaces obtain CACI authority. Downstream code MUST NOT read provisional records directly. All reads go through this resolver.

## Signature

```
resolve_authority(case_id, caci_id) -> ResolvedAuthority
```

## Resolution order (non-negotiable)

1. **Case-level decision** — the latest non-superseded decision for `(case_id, caci_id)`. If none, synthesize `PENDING_REVIEW` against the currently active provisional record.
2. **Active provisional record status** — consulted only after the case decision is known. BLOCKED_UNTRUSTED records block PENDING_REVIEW from proposing.
3. **Confidence threshold** — enforced at record-ingest time (≥0.90). Not re-checked here; the record's status already reflects it.

## Branch semantics

| Decision state | Pinned record status @ pin time | Result |
|---|---|---|
| ACCEPTED | was PROVISIONAL | grounding = GROUNDED, source = record, badge = "attorney-accepted (provisional)" |
| ACCEPTED | was BLOCKED_UNTRUSTED | ERROR: refused; operator must re-decide |
| REJECTED | any | grounding = NONE, source = null, badge = "attorney-rejected" |
| REPLACED | any | grounding = GROUNDED_VIA_REPLACEMENT, source = resolved replacement, badge = "replaced-by:<authority_id>" |
| PENDING_REVIEW | PROVISIONAL | grounding = PROPOSED, source = record, badge = "provisional-candidate", requires_attorney_review = true |
| PENDING_REVIEW | BLOCKED_UNTRUSTED | grounding = NONE, badge = "blocked-untrusted" |

## Invariants

- Case decision always wins over record status.
- A superseded pinned record stays reachable — the resolver loads from `records/` first, then `superseded/` by record_id.
- ACCEPTED is never silently granted over BLOCKED.
- No downstream surface may bypass the resolver.

## Consumers

- COA mapping
- Burden mapping
- Remedy derivation
- Complaint mapping
- Case-to-authority view
- Legal Library display

Each consumer receives the full tri-signal block (certified / provisional_candidate / case_decision) plus effective_grounding and display_badge, and records `(decision_id, pinned_record_id)` on any artifact it emits.
