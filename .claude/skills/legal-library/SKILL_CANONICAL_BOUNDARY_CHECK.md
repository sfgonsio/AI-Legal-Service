# SKILL_CANONICAL_BOUNDARY_CHECK

## Use when

- Before any review, before any proposed promotion, and before any proposed canonical write.
- Whenever an artifact crosses between layers (spine-index ↔ canonical ↔ human-readable, or proposal ↔ canonical).

## Do NOT use when

- The check has already been performed for this exact artifact and no input has changed since.
- The artifact is purely case-specific (non-canonical) and not crossing into the canonical layer.

## Inputs

- An artifact (verification report, normalization draft, review report, promotion recommendation, or candidate canonical file)
- `contract/v1/doctrine/LEGAL_SPINE_DOCTRINE.md`
- `contract/v1/doctrine/CANONICAL_PROMOTION_GATE.md`

## Procedure

1. Inspect the artifact for any non-canonical content (evidence, case facts, attorney strategy, AI-inferred text, timeline content, actor mapping, triangulation content).
2. Inspect the artifact for any reverse-flow attempt (non-canonical content trying to mutate canonical content).
3. Inspect provenance hashes; flag any missing or mismatched hash.
4. Inspect citation completeness against `AUTHORITY_INTAKE_MANIFEST_SCHEMA.md`.
5. Produce a verdict: `pass`, `fail`, or `quarantine`.

## Outputs

`BOUNDARY_CHECK_REPORT` — per artifact: artifact_id, layer crossing inspected, contamination findings, reverse-flow findings, provenance findings, verdict, justification, references to violated doctrine clauses.

## Validation rules

- A `pass` verdict requires zero contamination findings and zero reverse-flow findings.
- A `quarantine` verdict triggers routing to `SKILL_REJECTION_QUARANTINE`.
- The check must not modify the artifact under inspection.

## Failure modes

- Artifact format unparseable → return `INSPECTION_FAILED` and route to user.
- Doctrine documents missing or unparseable → halt with `DOCTRINE_REFERENCE_MISSING`.

## Test fixture expectations

- Fixture: clean canonical-only artifact passes.
- Fixture: artifact with embedded case-evidence string is flagged with contamination.
- Fixture: artifact with mismatched provenance hash is flagged.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be used to authorize live canonical writes until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
