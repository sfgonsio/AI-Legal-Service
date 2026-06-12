# SKILL_JUDGE_REVIEW

## Use when

- A `NORMALIZED_AUTHORITY_DRAFT` exists and must be reviewed for legal correctness, neutrality, completeness, and faithful preservation of official meaning.

## Do NOT use when

- The draft has not been produced yet.
- The review would substitute interpretation or strategy for the official text.

## Inputs

- `NORMALIZED_AUTHORITY_DRAFT`
- Linked `RAW_AUTHORITY_CAPTURE_PACKET` (for comparison against official source)
- `contract/v1/doctrine/LEGAL_SPINE_DOCTRINE.md`
- `contract/v1/doctrine/AUTHORITY_PACK_FORMAT.md`

## Procedure

1. Compare `official_text` in the draft against the captured source byte-for-byte (after documented whitespace rules).
2. Compare structural fields (elements, burdens, remedies, etc.) against the official source structure.
3. Assess neutrality: no slanting, no editorial gloss, no advocacy framing.
4. Assess completeness: all elements/burdens/remedies present in the source must be present in the draft.
5. Produce a decision: `pass`, `fail`, or `needs_revision` with itemized findings.

## Outputs

`JUDGE_REVIEW_REPORT` — authority_id, faithfulness findings, neutrality findings, completeness findings, structural correctness findings, decision, justification, references to specific source spans.

## Validation rules

- `pass` requires byte-for-byte text fidelity (per documented normalization rules), zero neutrality findings, zero completeness gaps.
- Every finding must reference a specific source span; no generic findings.
- Review must be reproducible: re-running on the same inputs must yield the same decision.

## Failure modes

- Source span referenced cannot be located → halt with `SOURCE_SPAN_NOT_FOUND`; route to capture review.
- Draft references a structure not in the format spec → halt with `STRUCTURE_OUT_OF_SCHEMA`.

## Test fixture expectations

- Fixture: faithful draft passes.
- Fixture: draft with a paraphrased element fails with a faithfulness finding pointing to the changed span.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be used to record live judge reviews until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
