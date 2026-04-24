# program_CASE_SAVE_LIFECYCLE
(Authoritative Program Contract — v1 | Case Lifecycle & Pipeline Separation)

---

## 1. Purpose

Govern the seven-state case save machine and hard-separate the ingest pipeline (on save) from the analysis pipeline (on explicit Submit for Legal Analysis).

## 2. States

DRAFT, SAVED, READY_FOR_ANALYSIS, PROCESSING, REVIEW_REQUIRED, APPROVED, RETURNED_TO_INTAKE.

## 3. Allowed transitions

See `contract/v1/schemas/case/case_save_state.schema.json` x-allowed-transitions. Any other transition is rejected with HTTP 409 and an audit record is NOT written.

## 4. Ingest pipeline (on save)

Bounded to exactly these operations:
1. Persist case metadata + document rows.
2. Compute sha256 for new document bytes.
3. Extract text (document.text_content).
4. Normalize (whitespace, encoding).
5. Index (char_count + basic term index).

The ingest pipeline MUST NOT call `brain.authority_resolver`, `brain.recompute`, COA engine, burden builder, remedy derivation, complaint parse, or any program/agent that performs legal reasoning.

## 5. Analysis pipeline (on Submit for Legal Analysis only)

Executed by `brain.analysis_runner.run_analysis(case_id, run_id)`:
1. Create AnalysisRun row (PENDING → RUNNING).
2. Transition case PROCESSING.
3. For each COA in case: call `resolve_authority`; snapshot `(authority_decision_id, authority_pinned_record_id, authority_effective_grounding)` onto COA row.
4. Run burden builder, remedy derivation, complaint parse-validation (program-level; consume snapshotted authority only).
5. Tally `review_required_count` = COAs with `effective_grounding ∈ {PROPOSED, NONE}`.
6. Transition case REVIEW_REQUIRED; AnalysisRun COMPLETED.
7. On failure: transition case REVIEW_REQUIRED with error flag; AnalysisRun FAILED.

## 6. State audit

Every transition writes a row to `case_state_events` (append-only): `{case_id, from_state, to_state, actor, at, reason}`.

## 7. API gating

- `POST /cases/{id}/save-draft` — any non-terminal state → DRAFT or SAVED.
- `POST /cases/{id}/submit-for-analysis` — from SAVED or READY_FOR_ANALYSIS only.
- `POST /cases/{id}/return-to-intake` — from any state → RETURNED_TO_INTAKE then auto → DRAFT.
- `GET /coas/case/{id}`, `GET /case-authority/case/{id}/map`, `POST /case-authority/resolve` — return HTTP 409 with `{save_state, message}` when state ∈ {DRAFT, SAVED, READY_FOR_ANALYSIS, RETURNED_TO_INTAKE}.
- `POST /case-authority/decisions` — allowed only when state is REVIEW_REQUIRED.

## 8. Non-negotiables

- No authority resolution occurs outside analysis runner or decision writes.
- Ingest never triggers analysis.
- Analysis never happens on upload or save.
- Attorney decisions are never silently written; state machine must permit them.
