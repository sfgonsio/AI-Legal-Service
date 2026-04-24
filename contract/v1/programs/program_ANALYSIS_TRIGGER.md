# program_ANALYSIS_TRIGGER
(Authoritative Program Contract — v1 | Explicit Analysis Gate)

---

## 1. Purpose

Require an explicit attorney/paralegal action to begin legal analysis. No upload, no save, no document edit may begin analysis.

## 2. Trigger

`POST /cases/{id}/submit-for-analysis` with `{actor_id, actor_type, role}`. Returns 202 Accepted with `{run_id}` and transitions case PROCESSING.

## 3. Preconditions

- Case save_state ∈ {SAVED, READY_FOR_ANALYSIS}.
- Case has ≥ 1 document and ≥ 1 COA row.
- No in-flight AnalysisRun in RUNNING state for the same case.

Violations return HTTP 409 with precondition detail.

## 4. Execution

Background task (FastAPI BackgroundTasks in v1; queue-worker-compatible API). Task calls `brain.analysis_runner.run_analysis(case_id, run_id)`. The route returns immediately.

## 5. Idempotency

Each invocation creates a new `run_id`. A completed AnalysisRun does not rerun on re-POST; a new POST creates a new run unless an active run is in RUNNING state.

## 6. Observability

`GET /cases/{id}/progress` exposes `current_analysis_run_id`, state, timestamps, review count.

## 7. Non-goals

- No implicit retry on failure (fail-fast into REVIEW_REQUIRED with error flag).
- No partial-reanalysis API (that is the recompute path tied to case authority decision changes).
