# REJECTION_QUARANTINE_PROTOCOL

## Scope

Defines the conditions under which an authority candidate, capture, draft, review, or packet must be quarantined, and the reason codes used to record those decisions.

## Quarantine triggers

An item is quarantined if any of the following are true:

- Source is unofficial and unsupported.
- Source is outdated and cannot be versioned.
- Citation is incomplete.
- Source text cannot be verified against the official publisher.
- Normalization would change legal meaning.
- AI filled gaps from model knowledge.
- Evidence or case facts influenced authority content.
- Jurisdiction is wrong or ambiguous.
- Review agents disagree without resolution.
- Provenance hash is missing, mismatched, or unverifiable.
- Boundary check detected reverse flow or contamination.

## Reason codes

```text
UNOFFICIAL_PUBLISHER
OUTDATED_NO_VERSION
INCOMPLETE_CITATION
TEXT_UNVERIFIABLE
NORMALIZATION_CHANGES_MEANING
AI_GAPFILL
EVIDENCE_INFLUENCE
JURISDICTION_AMBIGUOUS
REVIEWER_DISAGREEMENT
PROVENANCE_HASH_MISSING
PROVENANCE_HASH_MISMATCH
REVERSE_FLOW
CONTAMINATION
AMBIGUOUS_PUBLISHER
RESTRICTED_ACCESS
SOURCE_UNREACHABLE
CAPTURE_FAILED_UNREACHABLE
EXTRACTION_INCOMPLETE
STRUCTURE_INFERENCE_REQUIRED
NORMALIZATION_AMBIGUOUS
QUARANTINE_LOCATION_UNREACHABLE
UNKNOWN_REASON_CODE
```

## Quarantine record rules

- Records are append-only — never edited after creation.
- Records must include: artifact pointer, reason code, originator agent and skill, timestamp (ISO 8601 UTC), description, dependency list, follow-up action.
- Quarantined items may not be used by the canonical spine.
- Quarantined items remain in `/quarantine/legal_authority/` until adjudicated or expunged by user.

## Re-entry

A quarantined item may re-enter the pipeline only after the originating defect is corrected and a fresh source verification is performed. Re-entry creates a new manifest record; the prior quarantine record persists for audit.

## References

- `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` Section 15
- `contract/v1/doctrine/CANONICAL_PROMOTION_GATE.md`
- `contract/v1/doctrine/AUTHORITY_INTAKE_MANIFEST_SCHEMA.md`

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

No live quarantine action may be taken on production authority items until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved.
