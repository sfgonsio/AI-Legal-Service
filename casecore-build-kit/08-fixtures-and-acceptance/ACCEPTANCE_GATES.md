# /casecore-spec/docs/governance/ACCEPTANCE_GATES.md

# ACCEPTANCE GATES

## Purpose
Define the milestone gates the system must pass.

## Gate 1 — Ingestion
- files registered
- canonical metadata captured
- audit records emitted

## Gate 2 — Fact Proposals
- fact proposal envelopes valid
- provenance present
- run metadata present

## Gate 3 — Review/Promotion
- review states visible
- promotion governed
- audit recorded

## Gate 4 — Events and COA
- event proposals generated
- mapping outputs exist
- unsupported/missing states are visible

## Gate 5 — Frontend Truth
- proposal/canonical distinction visible
- conflict/support states visible
- source drill-down available where required

## Gate 6 — Reproducibility
- rerun semantics documented
- no silent mutation of canonical state
