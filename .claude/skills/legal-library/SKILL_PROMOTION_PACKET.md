# SKILL_PROMOTION_PACKET

## Use when

- An authority item has passed source verification, normalization, judge review, attorney review, and no-drift review — and a human-approval-ready promotion packet must be assembled.

## Do NOT use when

- Any prior gate has not passed.
- Used to perform the canonical promotion itself — this skill only produces the packet for human approval.

## Inputs

- `NORMALIZED_AUTHORITY_DRAFT`
- `SOURCE_VERIFICATION_REPORT` (accept)
- `JUDGE_REVIEW_REPORT` (pass)
- `ATTORNEY_REVIEW_REPORT` (pass)
- `NO_DRIFT_REVIEW_REPORT` (pass)
- `COMPLETENESS_SCORECARD` (acceptable)
- `BOUNDARY_CHECK_REPORT` (pass)

## Procedure

1. Verify each prerequisite is present and has a passing decision.
2. Aggregate all reports and the normalized draft into a single packet.
3. Compute a packet-level provenance hash.
4. Include a signature block reserved for the human approver.
5. Route the packet to the canonical-promotion approval queue (does not write to `/legal/canonical/`).

## Outputs

`PROMOTION_PACKET` — authority_id, normalized draft, all gate reports, packet hash, approval signature block (unsigned), routing record.

## Validation rules

- Any prerequisite missing or failing → halt and refuse to assemble the packet.
- Packet hash must cover all included artifacts so any future mutation is detectable.
- No part of the packet may be edited by the assembling skill — assembly is read-only against prior reports.

## Failure modes

- Prerequisite report missing → halt with `MISSING_PREREQUISITE`.
- Prerequisite report present but stale (input artifact has changed since report was produced) → halt with `STALE_REPORT`.

## Test fixture expectations

- Fixture: all prerequisites pass — packet assembles with all reports included.
- Fixture: judge report set to `fail` — assembly halts.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be used to assemble live promotion packets until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
