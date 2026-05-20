# AUTHORITY_PACK_FORMAT

## Scope

Defines the machine-readable structured format for canonical authority. Every promoted authority item must conform to this schema.

## Required JSON shape

```json
{
  "authority_id": "EVID_500",
  "authority_type": "statute",
  "jurisdiction": {
    "country": "US",
    "state": "CA",
    "county": null,
    "city": null
  },
  "legal_domain": ["evidence", "burden_of_proof"],
  "citation": {
    "official_citation": "Cal. Evid. Code § 500",
    "short_citation": "EVID 500",
    "source_url": "...",
    "source_name": "California Legislative Information"
  },
  "versioning": {
    "effective_date": "YYYY-MM-DD|null",
    "accessed_at": "YYYY-MM-DDTHH:MM:SSZ",
    "version_label": "...|null",
    "provenance_hash": "sha256:..."
  },
  "text": {
    "official_text": "...",
    "normalized_text": "...",
    "section_title": "...|null"
  },
  "structure": {
    "elements": [],
    "burdens": [],
    "remedies": [],
    "definitions": [],
    "exceptions": [],
    "procedural_requirements": [],
    "admissibility_requirements": []
  },
  "relationships": {
    "supersedes": [],
    "superseded_by": [],
    "references": [],
    "related_authorities": []
  },
  "review": {
    "source_verified": false,
    "normalized": false,
    "judge_reviewed": false,
    "attorney_reviewed": false,
    "no_drift_passed": false,
    "canonical_promoted": false
  }
}
```

## Field rules

- `official_text`: byte-for-byte source text (after documented whitespace rules). May not be paraphrased.
- `normalized_text`: reformatted for machine readability but legally equivalent. Differences from `official_text` must be limited to whitespace and formatting.
- `structure.*`: populated only from content explicitly present in the source. Inferred elements/burdens/remedies are not permitted.
- `relationships.*`: populated from explicit cross-references in the source or from approved cross-mapping records.
- `review.*`: advanced only by the responsible reviewer agent.

## Cross-reference with the spine index

The `authority_id` in this pack format must match the spine-index key in `contract/v1/knowledge/authority_catalog.yaml` for items also present in the catalog. The catalog references this pack by ID; the pack holds the authoritative text.

## References

- `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` Section 8
- `contract/v1/doctrine/AUTHORITY_INTAKE_MANIFEST_SCHEMA.md`

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

No live canonical authority pack may be produced or persisted until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved.
