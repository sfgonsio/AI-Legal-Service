# SKILL_REJECTION_QUARANTINE

## Use when

- Any candidate source, capture, draft, review, or packet fails a verification, review, or boundary check and must be removed from the active pipeline.

## Do NOT use when

- The item is still under review (decision not yet made).
- The item should be discarded silently (quarantine is the audit trail; no silent discards).

## Inputs

- The failing artifact
- A reason code from `contract/v1/doctrine/REJECTION_QUARANTINE_PROTOCOL.md`
- The originating agent and skill names

## Procedure

1. Create a quarantine record with artifact pointer, reason code, originator, timestamp, and a description.
2. Move the artifact (or a copy) to `/quarantine/legal_authority/`.
3. Flag any downstream artifacts that depended on this item.
4. Notify `AGENT_LEGAL_LIBRARY_PROGRAM_CONTROLLER` so the work queue can be updated.

## Outputs

`QUARANTINE_RECORD` — quarantine_id, artifact pointer, reason code, originator agent and skill, timestamp, dependency list, follow-up action.

## Validation rules

- Reason code must be a known value from the quarantine protocol; no free-form reasons.
- Quarantine record must be append-only — never edited after creation.
- Dependency list must be enumerated; no aggregated counts.

## Failure modes

- Reason code not in the protocol → halt with `UNKNOWN_REASON_CODE`; require the originator to pick a valid code.
- Quarantine location unwritable → halt with `QUARANTINE_LOCATION_UNREACHABLE`; escalate to user.

## Test fixture expectations

- Fixture: artifact with `INCOMPLETE_CITATION` quarantines and produces a record with that reason code.
- Fixture: artifact with invented reason code halts before writing.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be used to quarantine live artifacts until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
