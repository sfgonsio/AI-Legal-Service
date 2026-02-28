# rerun_governance_contract
(Authoritative Orchestration Contract — v1 | State Machine & Rerun Governance)

---

## 1. Purpose

This contract defines:

- The authoritative state machine for case processing runs
- Rerun levels (R0–R7)
- Artifact invalidation rules
- Attorney approval gates
- Audit ledger requirements
- Deterministic run_id semantics

It ensures that late uploads, rule changes, and attorney decisions do not create architectural drift, silent corruption, or inconsistent outputs.

This document governs orchestration behavior for Contract v1.

---

## 2. Architectural Alignment

This contract operates within:

- Section 7 layered architecture
- Deterministic program spine
- Write Broker mediation
- Tool Gateway enforcement
- Case isolation
- Audit ledger append-only guarantees
- Manifest hash-lock discipline

This contract governs orchestration logic only.
It does not redefine program behavior.

---

## 3. Core Principles

1. Every processing cycle is a versioned run.
2. Canonical artifacts are never mutated in place.
3. Reruns create superseding artifact versions.
4. Downstream artifacts are explicitly invalidated when upstream changes.
5. Attorney approval is required when reruns impact legal sufficiency or strategy outputs.
6. No silent recomputation is allowed.

---

## 4. Run Identity Model

Each execution cycle SHALL generate:

- run_id (UUID)
- case_id
- contract_version
- parser_ruleset_version
- normalization_ruleset_version
- tagging_ruleset_version
- composite_ruleset_version
- coa_ruleset_version
- timestamp_utc

Artifacts MUST include:
- run_id
- supersedes_run_id (if applicable)

---

## 5. State Machine Overview

Case processing exists in one of the following states:

- STATE_IDLE
- STATE_PROCESSING
- STATE_FACTS_READY
- STATE_TAGGED
- STATE_COMPOSITE_READY
- STATE_MAPPED
- STATE_COA_EVALUATED
- STATE_REASONED
- STATE_SUPERSEDED
- STATE_BLOCKED (error)

Transitions occur only through governed events.

---

## 6. Rerun Levels (Authoritative)

### R0 — Store Only (No Processing)

Used when:
- Client uploads new evidence
- Attorney has not approved processing

Effects:
- Raw uploads stored
- No canonical artifacts generated
- No invalidation occurs

Approval required:
- No

Audit event:
- UPLOAD_STORED_PENDING_REVIEW

---

### R1 — PROCESSING Only

Executes:
- program_PROCESSING

Invalidates:
- Nothing upstream (raw uploads immutable)
- Marks previous DOCUMENTS + CHUNKS as superseded

Approval required:
- No (unless case policy requires review)

Audit event:
- RERUN_R1_PROCESSING_COMPLETE

---

### R2 — PROCESSING + FACT_NORMALIZATION

Executes:
- program_PROCESSING
- program_FACT_NORMALIZATION

Invalidates:
- EvidenceFacts from prior run
- Any downstream artifacts referencing prior fact_ids

Approval required:
- Optional (policy-driven)

Audit event:
- RERUN_R2_FACTS_COMPLETE

---

### R3 — + TAGGING

Executes:
- PROCESSING
- FACT_NORMALIZATION
- TAGGING

Invalidates:
- TagAssignments
- Any composite that relied on tag filters

Approval required:
- Optional

Audit event:
- RERUN_R3_TAGGING_COMPLETE

---

### R4 — + COMPOSITE

Executes:
- PROCESSING
- FACT_NORMALIZATION
- TAGGING
- COMPOSITE_ENGINE

Invalidates:
- EventCandidates
- Any mapping referencing old event_candidate_ids

Approval required:
- Recommended if composites impact legal theory

Audit event:
- RERUN_R4_COMPOSITE_COMPLETE

---

### R5 — + MAPPING Refresh

Executes:
- All prior levels
- MAPPING_AGENT re-run

Invalidates:
- Story-to-evidence edge mappings
- Any coverage interpretations dependent on mappings

Approval required:
- Yes (legal narrative impact)

Audit event:
- RERUN_R5_MAPPING_COMPLETE

---

### R6 — + COA_ENGINE Refresh

Executes:
- All prior levels
- program_COA_ENGINE

Invalidates:
- COA element coverage matrix
- Structural sufficiency conclusions

Approval required:
- Yes (legal sufficiency impact)

Audit event:
- RERUN_R6_COA_COMPLETE

---

### R7 — Downstream Proposal Regeneration

Executes:
- COA_REASONER
- Any drafting/proposal layers

Invalidates:
- Advisory memos
- Discovery plans
- Deposition topic proposals

Approval required:
- Yes (attorney-driven)

Audit event:
- RERUN_R7_REASONER_COMPLETE

---

## 7. Invalidation Matrix (Summary)

If a level is executed, all downstream artifacts must be:

- marked superseded
- retained for audit
- excluded from active query responses

No artifact may silently remain active after its dependency changes.

---

## 8. Attorney Approval Gates

Approval REQUIRED for:

- R5 (Mapping)
- R6 (COA evaluation)
- R7 (Reasoning outputs)

Approval OPTIONAL (policy-driven):

- R2
- R3
- R4

Approval NOT required:

- R0
- R1

All approvals must generate audit events:
- ATTORNEY_APPROVED_RERUN
- ATTORNEY_DECLINED_RERUN

---

## 9. Partial Rerun Rules

The system SHALL NOT allow skipping intermediate layers.

Example:
- Cannot execute R6 without re-executing R4 if composites are invalidated.
- Cannot execute R3 without R2.

Rerun levels are cumulative.

---

## 10. Late Upload Scenario Handling

When new uploads occur after COA evaluation:

Default system behavior:
- Enter STATE_IDLE_PENDING_DECISION
- Suggest recommended rerun level based on dependency analysis
- Await attorney selection

System must display:
- What artifacts will be invalidated
- Estimated scope impact
- Downstream consequences

---

## 11. Audit Ledger Requirements

Each rerun SHALL log:

- rerun_level
- triggering_event
- initiating_user_id (if manual)
- run_id
- superseded_run_id
- artifact_counts
- timestamp_utc

Audit logs must be append-only.

---

## 12. Determinism Guarantees

Given:
- identical uploads
- identical ruleset versions
- identical policies

The same rerun level MUST produce identical canonical artifacts.

---

## 13. Failure Modes

Blocking failures:
- Missing upstream artifacts
- Ruleset mismatch
- Write Broker rejection
- Hash verification failure

Non-blocking:
- Optional advisory layer errors

Failures transition state to STATE_BLOCKED.

---

## 14. Supersession Policy

Superseded artifacts:
- remain stored
- remain queryable for audit
- are excluded from active retrieval unless explicitly requested

---

## 15. Query Safety Rule

Active query responses must reference:
- only artifacts tied to the latest active run_id
- unless user explicitly selects historical run

No mixed-run answers allowed.

---

## 16. Governance Escalation

If a rerun impacts:
- Filed pleadings
- Discovery responses
- Produced reports

The system SHALL:
- flag “Legal Artifact Impact”
- require attorney acknowledgement before activation

---

## 17. SIPOC

Supplier:
- Client uploads
- Attorney actions
- Policy updates

Input:
- Raw files
- Rulesets
- Prior run artifacts

Process:
- Determine rerun level
- Execute cumulative pipeline
- Supersede downstream artifacts
- Log audit events

Output:
- New run_id
- Versioned artifacts
- Updated active state

Customer:
- Attorneys
- Litigation support
- Audit/compliance

---

## 18. Acceptance Criteria

Compliant when:

- All reruns generate new run_id
- Downstream artifacts are explicitly invalidated
- Approval gates enforced
- Audit logs complete
- No mixed-run queries allowed
- Determinism preserved

---

## 19. Human Presentation Lens

Rerun governance protects legal integrity.

It ensures that when new evidence enters the system, nothing silently shifts.

The system never hides impact.
It forces visibility.
It preserves history.
It requires intentional decisions.

The architecture remains stable even when the case evolves.