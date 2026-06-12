# SKILL_AUTHORITY_NORMALIZATION

## Use when

- A `RAW_AUTHORITY_CAPTURE_PACKET` exists and must be transformed into the structured form defined by `contract/v1/doctrine/AUTHORITY_PACK_FORMAT.md`.

## Do NOT use when

- No verified capture exists.
- The transformation would require inventing missing structural elements not present in the source.

## Inputs

- `RAW_AUTHORITY_CAPTURE_PACKET`
- `contract/v1/doctrine/AUTHORITY_PACK_FORMAT.md`

## Procedure

1. Parse extracted text into the structural fields: elements, burdens, remedies, definitions, exceptions, procedural_requirements, admissibility_requirements.
2. Preserve `official_text` byte-for-byte in the `text.official_text` field.
3. Produce `normalized_text` that may reformat whitespace/structure but never changes legal meaning.
4. Populate `citation`, `jurisdiction`, `versioning` from capture metadata.
5. Compute provenance hashes over the normalized JSON.

## Outputs

`NORMALIZED_AUTHORITY_DRAFT` — JSON conforming to `AUTHORITY_PACK_FORMAT.md`, with `review.*` flags all set `false`.

## Validation rules

- `official_text` must match the captured source byte-for-byte (after whitespace normalization with documented rules).
- Any structural field that is not explicitly present in the source must be left empty (not inferred).
- Normalized text may not introduce numbered elements, conditions, or exceptions absent from the source.

## Failure modes

- Source lacks structure that the format requires → leave fields empty and mark `STRUCTURE_INFERENCE_REQUIRED`; route to `AGENT_EXPERT_JUDGE_AUTHORITY_REVIEWER`.
- Whitespace-normalization rules ambiguous for the source → halt with `NORMALIZATION_AMBIGUOUS`.

## Test fixture expectations

- Fixture: known CACI instruction normalizes into a `NORMALIZED_AUTHORITY_DRAFT` with elements matching the official element list.
- Fixture: Evidence Code section normalizes with burdens preserved.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be invoked for live normalization or persistence until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
