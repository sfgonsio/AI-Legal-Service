# RENDER_DB_AUTHORITY_MODEL

## Scope

Defines the **proposed target** Render database schema for canonical authority storage. This document is a target model for later approval, not an authorization to write.

## Proposed tables

```text
legal_authority_sources
legal_authority_manifests
legal_authority_items
legal_authority_versions
legal_authority_relationships
legal_authority_reviews
legal_authority_promotion_packets
legal_authority_human_pages
legal_authority_quarantine
```

## Minimum field set (per table where applicable)

```text
id
authority_id
jurisdiction
authority_level
authority_type
citation
source_url
source_name
source_accessed_at
effective_date
version_label
provenance_hash
canonical_status
review_status
created_at
updated_at
```

## Table responsibilities

- `legal_authority_sources` — distinct publisher/source records.
- `legal_authority_manifests` — per-item intake manifests per `AUTHORITY_INTAKE_MANIFEST_SCHEMA.md`.
- `legal_authority_items` — current canonical authority pack records per `AUTHORITY_PACK_FORMAT.md`.
- `legal_authority_versions` — historical versions of each authority item; canonical promotion creates a new version row.
- `legal_authority_relationships` — supersedes / superseded_by / references / related_authorities edges.
- `legal_authority_reviews` — judge / attorney / no-drift review rows.
- `legal_authority_promotion_packets` — assembled packets with signature blocks.
- `legal_authority_human_pages` — rendered human-readable pages with canonical-pack provenance.
- `legal_authority_quarantine` — append-only quarantine records.

## Migration discipline

Render DB writes require, in order:

1. Schema proposal (this document plus migration design).
2. Schema approval by Steve / authorized reviewer.
3. Migration file authored and reviewed.
4. Staging migration applied and validated.
5. Deployment migration applied with rollback plan.
6. Production validation evidence captured.

No table in this document may be created via ad-hoc DB operations.

## References

- `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` Section 10
- `contract/v1/doctrine/AUTHORITY_INTAKE_MANIFEST_SCHEMA.md`
- `contract/v1/doctrine/AUTHORITY_PACK_FORMAT.md`

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

No live Render DB writes against any table in this model may occur until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved AND the schema-migration discipline above is independently approved.
