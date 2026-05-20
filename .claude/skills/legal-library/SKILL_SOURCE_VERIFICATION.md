# SKILL_SOURCE_VERIFICATION

## Use when

- A `SOURCE_CANDIDATE_LIST` exists and each candidate must be accepted, rejected, or quarantined against the authority hierarchy.

## Do NOT use when

- No candidate list yet exists — use `SKILL_SOURCE_DISCOVERY`.
- Verification has already produced an `accept` decision — proceed to `SKILL_AUTHORITY_CAPTURE`.

## Inputs

- `SOURCE_CANDIDATE_LIST`
- `contract/v1/doctrine/LEGAL_SOURCE_HIERARCHY.md`

## Procedure

1. For each candidate, look up its `authority_type` and `jurisdiction` row in the hierarchy.
2. Compare the candidate's publisher class against the accepted publisher class for that row.
3. Verify citation completeness: jurisdiction, section number, version/effective date (or explicit `unknown`), accessed date.
4. Compute a provenance hash via `SKILL_PROVENANCE_HASHING` over the candidate's referenced text snapshot.
5. Decide: `accept`, `reject`, or `quarantine` per the doctrine in `contract/v1/doctrine/REJECTION_QUARANTINE_PROTOCOL.md`.

## Outputs

`SOURCE_VERIFICATION_REPORT` — per candidate: publisher class, hierarchy match status, citation completeness, provenance hash, decision, justification.

## Validation rules

- A `reject` or `quarantine` decision must carry a reason code from `REJECTION_QUARANTINE_PROTOCOL.md`.
- An `accept` decision requires complete citation and a provenance hash.
- No decision may rely on inference about authority class — only the documented hierarchy mapping.

## Failure modes

- Publisher class ambiguous → `quarantine` with `AMBIGUOUS_PUBLISHER` code; route to user for adjudication.
- Citation incomplete and missing data not recoverable from source → `quarantine` with `INCOMPLETE_CITATION`.
- Provenance hash cannot be computed (source unreachable) → `quarantine` with `SOURCE_UNREACHABLE`.

## Test fixture expectations

- Fixture: official primary URL must produce `accept`.
- Fixture: aggregator URL must produce `reject` with `UNOFFICIAL_PUBLISHER`.
- Fixture: official URL with missing effective date must produce `quarantine` with `INCOMPLETE_CITATION`.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be invoked for live verification, persistence, or downstream pipeline activation until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
