# INTAKE DATA CONTRACT & DB SPEC

## Stage Gate Alignment

**Primary Stage Gate:** INTAKE

This spec defines the truth-layer persistence for the INTAKE stage gate. It corresponds to **Wave 1 (W1-T1 … W1-T7)** of `CORE_DATA_WAVE_TICKETS.md` and is implemented by alembic migration `0001_wave1_core_intake` (13 tables) under `casecore-runtime/production/backend/`. This document is generated from, and must stay in sync with, that migration and `core_models.py`.

## Conventions

- **IDs:** UUID stored as `CHAR(36)` (portable across SQLite and PostgreSQL).
- **Timestamps:** plain `DATETIME`; ORM applies Python-side defaults. Audit fields `created_at` / `updated_at` / `created_by` / `reviewed_by` are applied per X-T1/X-T2.
- **JSON:** `sa.JSON` (TEXT in SQLite, JSON in PG; JSONB deferred).
- **Stratum:** these are **truth-layer** tables (`core_cases.stratum` defaults `"truth"`). No derived/Brain output is stored here (X-T3 boundary).
- **Cascade:** all child tables FK to `core_cases.id` with `ON DELETE CASCADE`.
- The legacy `cases` table in `models.py` is **untouched**; Wave 1 introduces `core_cases` as the new root.

## Table catalog (13)

### 1. `core_cases` — root of the Wave 1 FK tree (W1-T1)
`id` (PK), `display_name`, `stratum` (default `truth`), `created_by`, `created_at`, `updated_at`. Stable case identity; no stage-specific business logic embedded.

### 2. `case_stage_state` — stage-gate state per case (W1-T1)
`id` (PK), `core_case_id` (FK), `stage_key`, `state_value`, `state_details` (JSON), `entered_at`, `updated_at`. Unique on (`core_case_id`, `stage_key`). Stage state is queryable and independent of UI route structure.

### 3. `uploaded_files` — intake file uploads (W1-T4)
`id` (PK), `core_case_id` (FK), `file_name`, `mime_type`, `file_size_bytes`, `sha256_hash` (indexed), `source_type`, `source_reference`, `storage_uri`, `storage_backend`, `captured_at`, `uploaded_by`, `created_at`. Immutable original reference; hash and source queryable.

### 4. `interview_sessions` — interview sessions (W1-T2)
`id` (PK), `core_case_id` (FK), `interview_mode` (audio/written), `interviewer_user_id`, `started_at`, `ended_at`, `status` (default `in_progress`), `created_at`, `updated_at`. Multiple sessions per case.

### 5. `interview_responses` — per-question responses (W1-T2)
`id` (PK), `interview_session_id` (FK), `core_case_id` (FK), `question_key`, `response_text`, `response_payload` (JSON), `answered_by`, `captured_at`, `created_at`, `updated_at`. Indexed on (`session`, `question_key`); responses survive navigation/refresh (upsert by session+question). No hardcoded question count.

### 6. `interview_recordings` — immutable audio metadata (W1-T3)
`id` (PK), `interview_session_id` (FK), `core_case_id` (FK), `storage_uri`, `storage_backend`, `file_hash`, `duration_seconds`, `mime_type`, `captured_at`, `recorded_by`, `created_at`. Raw recording reference is immutable.

### 7. `interview_transcript_segments` — editable transcript, versioned (W1-T3)
`id` (PK), `interview_recording_id` (FK), `interview_session_id` (FK), `core_case_id` (FK), `segment_index`, `start_ms`, `end_ms`, `text_content`, `speaker_label`, `version` (default 1), `supersedes_segment_id` (self-FK), `is_current` (default true, indexed), `edited_by`, `created_at`. Edits are superseding (non-destructive), attributable to user.

### 8. `uploaded_file_versions` — file version chain (W1-T4)
`id` (PK), `uploaded_file_id` (FK), `core_case_id` (FK), `version_number`, `sha256_hash`, `storage_uri`, `storage_backend`, `file_size_bytes`, `change_note`, `created_by`, `created_at`. Unique on (`uploaded_file_id`, `version_number`).

### 9. `intake_actor_records` — actors/entities at intake (W1-T5)
`id` (PK), `core_case_id` (FK), `actor_type` (person/entity), `display_name` (name-first), `role_context`, `raw_input_text`, `source_reference`, `confidence`, `captured_at`, `created_by`, `created_at`, `updated_at`. No forced deduplication at intake.

### 10. `intake_actor_relationship_inputs` — intake-provided relationships (W1-T5)
`id` (PK), `core_case_id` (FK), `actor_a_id` (FK), `actor_b_id` (FK, nullable), `relationship_claim`, `direction`, `source_reference`, `captured_at`, `created_by`, `created_at`. Persisted independently from later graph reasoning.

### 11. `intake_summaries_client` — client-facing summary, versioned (W1-T6)
`id` (PK), `core_case_id` (FK), `summary_text`, `summary_payload` (JSON), `version_number` (default 1), `supersedes_summary_id` (self-FK), `is_current` (indexed), `created_by`, `reviewed_by`, `reviewed_at`, `created_at`. Latest retrievable; priors retained.

### 12. `intake_summaries_attorney` — attorney legal-framing summary, versioned (W1-T6)
Same shape as #11, separate table so client summary and attorney legal framing are distinct.

### 13. `intake_timeline_seeds` — raw timeline seeds (W1-T7)
`id` (PK), `core_case_id` (FK), `seed_text`, `event_time_candidate`, `event_time_iso`, `time_precision`, `source_response_id` (FK → interview_responses), `source_file_id` (FK → uploaded_files), `related_actor_id` (FK → intake_actor_records), `uncertainty_notes`, `captured_at`, `created_by`, `created_at`. Event-like fragments with preserved uncertainty and source linkage; feed later Brain timeline assembly.

## Gate completion criteria (INTAKE)

INTAKE is complete on the canonical line (`main`) when:
- migration `0001_wave1_core_intake` applies cleanly (13 tables),
- `tests/test_wave1_intake.py` passes (8 tests, one per W1 ticket),
- `scripts/wave_proof.py` reports SUCCESS,
- golden-path (X-T4) and messy-path (X-T5) seed cases exist.

## Status

**Version:** 1.0 — generated from `0001_wave1_core_intake`. Implementation landed via PR (Wave 1 + Wave 2 consolidation).
