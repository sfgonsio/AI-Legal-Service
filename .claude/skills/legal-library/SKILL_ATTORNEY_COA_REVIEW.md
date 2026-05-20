# SKILL_ATTORNEY_COA_REVIEW

## Use when

- A `NORMALIZED_AUTHORITY_DRAFT` and `JUDGE_REVIEW_REPORT` exist and the authority must be reviewed for practical legal applicability across causes of action, burdens, remedies, pleading, and admissibility.

## Do NOT use when

- The draft has not passed judge review yet.
- The review would introduce case-specific facts or strategy into the authority itself.

## Inputs

- `NORMALIZED_AUTHORITY_DRAFT`
- `JUDGE_REVIEW_REPORT` (pass)
- `contract/v1/doctrine/LEGAL_SPINE_DOCTRINE.md`
- `contract/v1/doctrine/AUTHORITY_PACK_FORMAT.md`

## Procedure

1. Identify the COA(s) this authority supports per the authority's `legal_domain` and `structure.elements`.
2. Assess whether the elements are fully usable for pleading (each element has a clear factual predicate path).
3. Assess burden mapping: every element has a burden of proof, persuasion, or production identified.
4. Assess remedy coverage: remedies referenced by the authority are enumerated.
5. Assess admissibility implications where applicable.
6. Produce a decision: `pass`, `fail`, or `needs_revision`.

## Outputs

`ATTORNEY_COA_REVIEW_REPORT` — authority_id, COA coverage findings, element pleading-readiness, burden mapping completeness, remedy coverage, admissibility findings, decision, justification.

## Validation rules

- Findings may not import case-specific facts, evidence, or strategy.
- `pass` requires every element to be pleading-ready and every burden to be mapped.
- Review must be reproducible from the same inputs.

## Failure modes

- Authority structure cannot be mapped to any COA → halt with `COA_MAPPING_NOT_FOUND`; route to spine governor.
- Burden cannot be identified for an element → mark `needs_revision`; return to normalizer.

## Test fixture expectations

- Fixture: CACI fraud instruction reviews to `pass` with all five elements mapped to burdens.
- Fixture: instruction with missing remedy reviews to `needs_revision`.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be used to record live attorney reviews until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
