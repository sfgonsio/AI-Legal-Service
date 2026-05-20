# SKILL_COMPLETENESS_SCORING

## Use when

- Scoring how complete an authority pack is against the expected coverage for its target jurisdiction and authority family (e.g., full CACI series, full Evidence Code division).

## Do NOT use when

- The pack has no defined expected-coverage manifest.
- Used to drive promotion decisions on its own — completeness is one of many gates.

## Inputs

- An authority pack (collection of `NORMALIZED_AUTHORITY_DRAFT` records sharing a common scope)
- An expected-coverage manifest (e.g., "all CACI sections 1900–1907 required")

## Procedure

1. Enumerate target authority IDs from the expected-coverage manifest.
2. Enumerate present authority IDs in the pack.
3. Compute the diff: present, missing, extra-but-unexpected.
4. For each present item, check whether all required structural fields are populated.
5. Produce a numeric coverage score and a qualitative scorecard.

## Outputs

`COMPLETENESS_SCORECARD` — pack_id, target count, present count, missing list, extra list, per-item structural-fill ratio, aggregate coverage score (0.0–1.0), qualitative rating.

## Validation rules

- Score must be reproducible from the same pack + manifest.
- Missing items must be enumerated explicitly — no "approximately N missing."
- Extra items must be reported even if they are valid authority (to detect scope creep).

## Failure modes

- Expected-coverage manifest missing or ill-formed → halt with `MANIFEST_MISSING`.
- Pack contains duplicate authority IDs → halt with `DUPLICATE_AUTHORITY_ID`.

## Test fixture expectations

- Fixture: pack covering 5 of 8 expected IDs scores 0.625 with the 3 missing IDs enumerated.
- Fixture: pack with duplicates halts before scoring.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be used to authorize live promotion until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
