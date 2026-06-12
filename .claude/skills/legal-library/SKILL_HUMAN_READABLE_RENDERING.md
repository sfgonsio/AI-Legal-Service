# SKILL_HUMAN_READABLE_RENDERING

## Use when

- Canonical or approved-structured authority exists and a human-readable library page must be rendered from it per `contract/v1/doctrine/HUMAN_READABLE_LIBRARY_FORMAT.md`.

## Do NOT use when

- No canonical or approved structured authority exists.
- Rendering would require filling sections that have no canonical source.

## Inputs

- An approved canonical or structured authority record
- `contract/v1/doctrine/HUMAN_READABLE_LIBRARY_FORMAT.md`

## Procedure

1. For each required page section, locate the canonical source field that populates it.
2. Render the section using only canonical content, with citations to the canonical authority.
3. Mark any section without canonical content explicitly as `[missing-canonical]` — never fabricate, paraphrase, or fill from inference.
4. Include the canonical authority's provenance hash in the page footer.

## Outputs

`HUMAN_READABLE_LIBRARY_PAGE` — markdown page conforming to the format spec, every section either canonical-populated (with citation) or `[missing-canonical]`.

## Validation rules

- No section may contain content not traceable to the canonical authority.
- Citations must point to specific canonical records by ID.
- `[missing-canonical]` markers must be machine-detectable for later completeness audits.

## Failure modes

- Canonical authority record missing required fields → render with `[missing-canonical]` markers; do not halt the render itself but escalate.
- Format spec missing or ill-formed → halt with `FORMAT_SPEC_MISSING`.

## Test fixture expectations

- Fixture: complete canonical record renders all sections with citations.
- Fixture: canonical record missing remedy section renders with `[missing-canonical]` in that section.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be used to publish live human-readable pages until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
