# AUTHORITY_INTAKE_MANIFEST_SCHEMA

## Scope

Defines the manifest schema that must accompany every authority item before it enters review or promotion.

## Required JSON shape

```json
{
  "authority_id": "CACI_1900",
  "jurisdiction": "California",
  "authority_level": "state",
  "authority_type": "jury_instruction",
  "source_name": "Judicial Council of California Civil Jury Instructions",
  "source_url": "...",
  "source_accessed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "effective_date": "YYYY-MM-DD|null",
  "version": "...|null",
  "citation": "...",
  "official_status": "official|authorized|secondary|rejected",
  "source_format": "html|pdf|xml|json|txt|other",
  "capture_method": "manual|api|download|other",
  "provenance_hash": "sha256:...",
  "normalization_status": "not_started|draft|validated|rejected",
  "judge_review_status": "pending|pass|fail|needs_revision",
  "attorney_review_status": "pending|pass|fail|needs_revision",
  "no_drift_review_status": "pending|pass|fail|quarantine",
  "canonical_promotion_decision": "pending|approved|rejected",
  "canonical_promotion_approved_by": null,
  "canonical_promoted_at": null,
  "notes": []
}
```

## Field rules

- `authority_id`: unique within its jurisdiction + authority_type namespace; references the spine index entry where applicable.
- `official_status`: must be one of the four enumerated values; no free-form values.
- `provenance_hash`: SHA-256 of the captured source bytes (see `SKILL_PROVENANCE_HASHING`).
- All review-status fields default to `pending` and may only be advanced by the responsible reviewer agent.
- `canonical_promotion_decision` is `approved` only when all gates per `CANONICAL_PROMOTION_GATE.md` are satisfied AND a human approver is recorded.

## References

- `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` Section 7
- `contract/v1/doctrine/CANONICAL_PROMOTION_GATE.md`
- `contract/v1/doctrine/AUTHORITY_PACK_FORMAT.md`

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

No agent may produce or persist live manifest records until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture manifests only.
