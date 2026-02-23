-- contract/v1/data/postgres_ddl.sql
-- Contract v1: Minimal physical schema aligned to:
-- - run_record.schema.yaml
-- - audit_event.schema.yaml
-- - artifact_ref.schema.yaml (referenced via *_artifacts_json JSONB fields)
-- - export_bundle.schema.yaml
-- - run_lifecycle.md
--
-- Notes:
-- 1) This DDL is intentionally "strict where it matters" (audit append-only, case isolation ready).
-- 2) Artifact payloads (PDF/audio/transcripts) live in object storage; DB stores references + hashes + metadata.
-- 3) IDs are TEXT to support UUID/ULID without forcing an extension.

BEGIN;

-- Optional (only if you want convenience UUID generation):
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- --------------------------------------------------------------------
-- 0) Helper: bounded text is enforced at app layer; DB uses TEXT.
-- --------------------------------------------------------------------

-- --------------------------------------------------------------------
-- 1) RUNS (Run Record)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS runs (
  run_id                    TEXT PRIMARY KEY,
  parent_run_id             TEXT NULL,
  root_run_id               TEXT NULL,
  correlation_id            TEXT NULL,

  run_kind                  TEXT NOT NULL,
  status                    TEXT NOT NULL,

  contract_version          TEXT NOT NULL,

  policy_versions_lanes     TEXT NOT NULL,
  policy_versions_roles     TEXT NOT NULL,

  taxonomy_versions_coa     TEXT NULL,
  taxonomy_versions_tags    TEXT NULL,
  taxonomy_versions_entities TEXT NULL,

  case_id                   TEXT NULL,
  lane_id                   TEXT NULL,

  actor_type                TEXT NULL,
  actor_id                  TEXT NULL,
  role_id                   TEXT NULL,

  created_at_utc            TIMESTAMPTZ NOT NULL,
  started_at_utc            TIMESTAMPTZ NULL,
  completed_at_utc          TIMESTAMPTZ NULL,

  error_code                TEXT NULL,
  error_message_bounded     TEXT NULL,
  retryable                 BOOLEAN NULL,

  metadata_json             JSONB NOT NULL DEFAULT '{}'::jsonb,

  inputs_artifacts_json     JSONB NOT NULL DEFAULT '[]'::jsonb,  -- array of artifact_ref
  outputs_artifacts_json    JSONB NOT NULL DEFAULT '[]'::jsonb   -- array of artifact_ref
);

-- Self-referential relationships (optional but useful)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'runs_parent_fk'
  ) THEN
    ALTER TABLE runs
      ADD CONSTRAINT runs_parent_fk
      FOREIGN KEY (parent_run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'runs_root_fk'
  ) THEN
    ALTER TABLE runs
      ADD CONSTRAINT runs_root_fk
      FOREIGN KEY (root_run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

-- Canonical indexes
CREATE INDEX IF NOT EXISTS idx_runs_case_created     ON runs (case_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_runs_root             ON runs (root_run_id);
CREATE INDEX IF NOT EXISTS idx_runs_parent           ON runs (parent_run_id);
CREATE INDEX IF NOT EXISTS idx_runs_kind_status      ON runs (run_kind, status);
CREATE INDEX IF NOT EXISTS idx_runs_policy_versions  ON runs (policy_versions_lanes, policy_versions_roles);

-- --------------------------------------------------------------------
-- 2) AUDIT LEDGER (Append-only)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_ledger (
  event_id                  TEXT PRIMARY KEY,
  timestamp_utc             TIMESTAMPTZ NOT NULL,

  action_type               TEXT NOT NULL,
  outcome                   TEXT NOT NULL,
  outcome_reason_bounded    TEXT NULL,

  contract_version          TEXT NOT NULL,
  policy_versions_lanes     TEXT NOT NULL,
  policy_versions_roles     TEXT NOT NULL,

  case_id                   TEXT NULL,
  lane_id                   TEXT NULL,

  run_id                    TEXT NOT NULL,
  parent_run_id             TEXT NULL,
  root_run_id               TEXT NULL,

  actor_type                TEXT NULL,
  actor_id                  TEXT NULL,
  role_id                   TEXT NULL,

  target_json               JSONB NOT NULL DEFAULT '{}'::jsonb,

  request_hash_sha256       TEXT NULL,
  response_hash_sha256      TEXT NULL,

  input_artifacts_json      JSONB NOT NULL DEFAULT '[]'::jsonb,  -- array of artifact_ref
  output_artifacts_json     JSONB NOT NULL DEFAULT '[]'::jsonb,  -- array of artifact_ref

  error_code                TEXT NULL,
  error_message_bounded     TEXT NULL,
  retryable                 BOOLEAN NULL
);

-- Correlate audit events to runs (non-blocking; allow audit even if run record missing in dev)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'audit_run_fk'
  ) THEN
    ALTER TABLE audit_ledger
      ADD CONSTRAINT audit_run_fk
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_audit_run_time        ON audit_ledger (run_id, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_audit_case_time       ON audit_ledger (case_id, timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action_outcome  ON audit_ledger (action_type, outcome, timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_lane_time       ON audit_ledger (lane_id, timestamp_utc DESC);

-- Enforce append-only semantics (no UPDATE/DELETE) in production
CREATE OR REPLACE FUNCTION audit_ledger_block_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'audit_ledger is append-only; mutation is not allowed';
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_audit_ledger_no_update'
  ) THEN
    CREATE TRIGGER trg_audit_ledger_no_update
      BEFORE UPDATE ON audit_ledger
      FOR EACH ROW
      EXECUTE FUNCTION audit_ledger_block_mutation();
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_audit_ledger_no_delete'
  ) THEN
    CREATE TRIGGER trg_audit_ledger_no_delete
      BEFORE DELETE ON audit_ledger
      FOR EACH ROW
      EXECUTE FUNCTION audit_ledger_block_mutation();
  END IF;
END $$;

-- --------------------------------------------------------------------
-- 3) ARTIFACTS (Canonical Registry)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id               TEXT PRIMARY KEY,
  artifact_kind             TEXT NOT NULL,

  case_id                   TEXT NULL,
  plane                     TEXT NOT NULL CHECK (plane IN ('case','shared','system')),

  storage_uri               TEXT NOT NULL,
  content_hash_sha256       TEXT NOT NULL,

  size_bytes                BIGINT NULL,
  mime_type                 TEXT NULL,

  created_at_utc            TIMESTAMPTZ NOT NULL,
  created_by_run_id         TEXT NULL,
  created_by_actor_id       TEXT NULL,

  tags_json                 JSONB NOT NULL DEFAULT '[]'::jsonb,
  metadata_json             JSONB NOT NULL DEFAULT '{}'::jsonb
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'artifacts_created_by_run_fk'
  ) THEN
    ALTER TABLE artifacts
      ADD CONSTRAINT artifacts_created_by_run_fk
      FOREIGN KEY (created_by_run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

-- Integrity index for fast hash lookups / dedupe checks
CREATE UNIQUE INDEX IF NOT EXISTS uq_artifacts_content_hash ON artifacts (content_hash_sha256);
CREATE INDEX IF NOT EXISTS idx_artifacts_case_created       ON artifacts (case_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_artifacts_kind               ON artifacts (artifact_kind);

-- --------------------------------------------------------------------
-- 4) EXPORT BUNDLES (Manifest + Integrity)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS export_bundles (
  bundle_id                 TEXT PRIMARY KEY,

  bundle_kind               TEXT NOT NULL,
  bundle_name               TEXT NULL,
  bundle_description_bounded TEXT NULL,

  scope                     TEXT NOT NULL CHECK (scope IN ('case','shared','system')),
  case_id                   TEXT NULL,

  contract_version          TEXT NOT NULL,
  policy_versions_lanes     TEXT NOT NULL,
  policy_versions_roles     TEXT NOT NULL,

  taxonomy_versions_coa     TEXT NULL,
  taxonomy_versions_tags    TEXT NULL,
  taxonomy_versions_entities TEXT NULL,

  status                    TEXT NOT NULL,

  created_at_utc            TIMESTAMPTZ NOT NULL,
  completed_at_utc          TIMESTAMPTZ NULL,

  created_by_actor_type     TEXT NULL,
  created_by_actor_id       TEXT NULL,
  created_by_role_id        TEXT NULL,

  approvals_json            JSONB NOT NULL DEFAULT '[]'::jsonb,
  contents_json             JSONB NOT NULL DEFAULT '{}'::jsonb,  -- artifacts[], included_tables[], filters
  integrity_json            JSONB NOT NULL DEFAULT '{}'::jsonb,  -- manifest_hash_sha256, package_hash_sha256, package_locator
  signatures_json           JSONB NOT NULL DEFAULT '[]'::jsonb,
  audit_json                JSONB NOT NULL DEFAULT '{}'::jsonb,  -- audit_event_ids[], run_ids[]
  redaction_json            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_export_bundles_case_created  ON export_bundles (case_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_export_bundles_status        ON export_bundles (status, created_at_utc DESC);

-- --------------------------------------------------------------------
-- 5) DOMAIN / CAPABILITY TABLES (Case Plane)
-- These align to your lanes (WRITE_INTAKE_ARTIFACTS, WRITE_MAPPING_OUTPUTS).
-- Antigravity may rename, but MUST preserve case partitioning + governed writes.
-- --------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transcripts (
  transcript_id             TEXT PRIMARY KEY,
  case_id                   TEXT NOT NULL,
  run_id                    TEXT NOT NULL,
  session_id                TEXT NULL,
  artifact_id               TEXT NOT NULL,
  created_at_utc            TIMESTAMPTZ NOT NULL
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'transcripts_run_fk') THEN
    ALTER TABLE transcripts
      ADD CONSTRAINT transcripts_run_fk
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'transcripts_artifact_fk') THEN
    ALTER TABLE transcripts
      ADD CONSTRAINT transcripts_artifact_fk
      FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_transcripts_case_created ON transcripts (case_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_transcripts_run          ON transcripts (run_id);

-- --------------------------------------------------------------------
-- Interview Notes (Case Plane)
-- Aligns to WRITE_INTAKE_ARTIFACTS lane: interview_notes append
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS interview_notes (
  note_id                  TEXT PRIMARY KEY,
  case_id                  TEXT NOT NULL,
  run_id                   TEXT NOT NULL,
  session_id               TEXT NULL,

  note_kind                TEXT NULL,          -- e.g., "summary", "key_facts", "followups"
  note_text_bounded        TEXT NULL,          -- short bounded note for quick viewing
  note_artifact_id         TEXT NULL,          -- optional: store full note text as an artifact

  created_at_utc           TIMESTAMPTZ NOT NULL
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'interview_notes_run_fk') THEN
    ALTER TABLE interview_notes
      ADD CONSTRAINT interview_notes_run_fk
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'interview_notes_artifact_fk') THEN
    ALTER TABLE interview_notes
      ADD CONSTRAINT interview_notes_artifact_fk
      FOREIGN KEY (note_artifact_id) REFERENCES artifacts(artifact_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_interview_notes_case_created ON interview_notes (case_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_interview_notes_run          ON interview_notes (run_id);

CREATE TABLE IF NOT EXISTS entities (
  entity_id                 TEXT PRIMARY KEY,
  case_id                   TEXT NOT NULL,
  canonical_name            TEXT NOT NULL,
  entity_type               TEXT NOT NULL, -- person|org|location|other
  aliases_json              JSONB NOT NULL DEFAULT '[]'::jsonb,
  source_artifact_id        TEXT NULL,
  created_by_run_id         TEXT NOT NULL,
  updated_at_utc            TIMESTAMPTZ NOT NULL
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'entities_source_artifact_fk') THEN
    ALTER TABLE entities
      ADD CONSTRAINT entities_source_artifact_fk
      FOREIGN KEY (source_artifact_id) REFERENCES artifacts(artifact_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'entities_created_by_run_fk') THEN
    ALTER TABLE entities
      ADD CONSTRAINT entities_created_by_run_fk
      FOREIGN KEY (created_by_run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_entities_case_name   ON entities (case_id, canonical_name);
CREATE INDEX IF NOT EXISTS idx_entities_case_type         ON entities (case_id, entity_type);

CREATE TABLE IF NOT EXISTS facts (
  fact_id                   TEXT PRIMARY KEY,
  case_id                   TEXT NOT NULL,
  run_id                    TEXT NOT NULL,
  statement_bounded         TEXT NULL,
  statement_artifact_id     TEXT NULL,  -- if full statement stored as artifact
  confidence                NUMERIC(5,4) NULL, -- 0.0000 - 1.0000
  supporting_artifacts_json JSONB NOT NULL DEFAULT '[]'::jsonb, -- array of artifact_ref
  created_at_utc            TIMESTAMPTZ NOT NULL
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'facts_run_fk') THEN
    ALTER TABLE facts
      ADD CONSTRAINT facts_run_fk
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'facts_statement_artifact_fk') THEN
    ALTER TABLE facts
      ADD CONSTRAINT facts_statement_artifact_fk
      FOREIGN KEY (statement_artifact_id) REFERENCES artifacts(artifact_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_facts_case_created ON facts (case_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_facts_run          ON facts (run_id);

CREATE TABLE IF NOT EXISTS evidence_map (
  map_id                    TEXT PRIMARY KEY,
  case_id                   TEXT NOT NULL,
  run_id                    TEXT NOT NULL,
  evidence_artifact_id      TEXT NULL,   -- if you store evidence as registered artifact
  evidence_artifact_ref_json JSONB NULL, -- otherwise store artifact_ref directly
  fact_ids_json             JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at_utc            TIMESTAMPTZ NOT NULL
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'evidence_map_run_fk') THEN
    ALTER TABLE evidence_map
      ADD CONSTRAINT evidence_map_run_fk
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'evidence_map_artifact_fk') THEN
    ALTER TABLE evidence_map
      ADD CONSTRAINT evidence_map_artifact_fk
      FOREIGN KEY (evidence_artifact_id) REFERENCES artifacts(artifact_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_evidence_map_case_created ON evidence_map (case_id, created_at_utc DESC);

CREATE TABLE IF NOT EXISTS coa_map (
  coa_map_id                TEXT PRIMARY KEY,
  case_id                   TEXT NOT NULL,
  run_id                    TEXT NOT NULL,
  coa_version               TEXT NOT NULL,
  mappings_json             JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at_utc            TIMESTAMPTZ NOT NULL
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'coa_map_run_fk') THEN
    ALTER TABLE coa_map
      ADD CONSTRAINT coa_map_run_fk
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_coa_map_case_version_created ON coa_map (case_id, coa_version, created_at_utc DESC);

-- --------------------------------------------------------------------
-- 5B) SHARED PLANE TABLES (Governed write via PROMOTE_SHARED_KNOWLEDGE)
-- --------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS shared_playbooks (
  playbook_id               TEXT PRIMARY KEY,
  created_by_run_id         TEXT NOT NULL,
  promotion_ticket_id       TEXT NOT NULL,
  title_bounded             TEXT NULL,
  summary_bounded           TEXT NULL,
  content_artifact_id       TEXT NULL,
  created_at_utc            TIMESTAMPTZ NOT NULL
);

DO $
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'shared_playbooks_run_fk') THEN
    ALTER TABLE shared_playbooks
      ADD CONSTRAINT shared_playbooks_run_fk
      FOREIGN KEY (created_by_run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'shared_playbooks_artifact_fk') THEN
    ALTER TABLE shared_playbooks
      ADD CONSTRAINT shared_playbooks_artifact_fk
      FOREIGN KEY (content_artifact_id) REFERENCES artifacts(artifact_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $;

CREATE INDEX IF NOT EXISTS idx_shared_playbooks_created ON shared_playbooks (created_at_utc DESC);

CREATE TABLE IF NOT EXISTS shared_heuristics (
  heuristic_id              TEXT PRIMARY KEY,
  created_by_run_id         TEXT NOT NULL,
  promotion_ticket_id       TEXT NOT NULL,
  name_bounded              TEXT NULL,
  description_bounded       TEXT NULL,
  content_artifact_id       TEXT NULL,
  created_at_utc            TIMESTAMPTZ NOT NULL
);

DO $
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'shared_heuristics_run_fk') THEN
    ALTER TABLE shared_heuristics
      ADD CONSTRAINT shared_heuristics_run_fk
      FOREIGN KEY (created_by_run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'shared_heuristics_artifact_fk') THEN
    ALTER TABLE shared_heuristics
      ADD CONSTRAINT shared_heuristics_artifact_fk
      FOREIGN KEY (content_artifact_id) REFERENCES artifacts(artifact_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $;

CREATE INDEX IF NOT EXISTS idx_shared_heuristics_created ON shared_heuristics (created_at_utc DESC);

-- --------------------------------------------------------------------
-- 5C) OVERRIDE EVENTS (Break-glass actions audited + timeboxed)
-- --------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS override_events (
  override_event_id         TEXT PRIMARY KEY,
  override_ticket_id        TEXT NOT NULL,
  run_id                    TEXT NOT NULL,

  actor_id                  TEXT NULL,
  role_id                   TEXT NULL,

  action_bounded            TEXT NOT NULL,       -- enable|disable|rerun.force|taxonomy.unlock|run.state.override
  reason_bounded            TEXT NOT NULL,

  before_json               JSONB NOT NULL DEFAULT '{}'::jsonb,
  after_json                JSONB NOT NULL DEFAULT '{}'::jsonb,

  created_at_utc            TIMESTAMPTZ NOT NULL
);

DO $
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'override_events_run_fk') THEN
    ALTER TABLE override_events
      ADD CONSTRAINT override_events_run_fk
      FOREIGN KEY (run_id) REFERENCES runs(run_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $;

CREATE INDEX IF NOT EXISTS idx_override_events_run_created ON override_events (run_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_override_events_ticket      ON override_events (override_ticket_id);

-- --------------------------------------------------------------------
-- 6) OPTIONAL: Policy & Taxonomy snapshots (replay support)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS policy_snapshots (
  snapshot_id               TEXT PRIMARY KEY,
  policy_type               TEXT NOT NULL CHECK (policy_type IN ('lanes','roles')),
  git_sha                   TEXT NOT NULL UNIQUE,
  content_hash_sha256       TEXT NOT NULL,
  stored_at_utc             TIMESTAMPTZ NOT NULL,
  blob_uri                  TEXT NULL,
  content_json              JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS taxonomy_snapshots (
  snapshot_id               TEXT PRIMARY KEY,
  taxonomy_type             TEXT NOT NULL CHECK (taxonomy_type IN ('coa','tags','entities')),
  git_sha                   TEXT NOT NULL UNIQUE,
  content_hash_sha256       TEXT NOT NULL,
  stored_at_utc             TIMESTAMPTZ NOT NULL,
  blob_uri                  TEXT NULL,
  content_json              JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- --------------------------------------------------------------------
-- 7) OPTIONAL: Case isolation enforcement (Row-Level Security skeleton)
-- --------------------------------------------------------------------
-- If Antigravity uses RLS, you typically set a session var like:
--   SET app.case_id = 'CASE123';
-- and enforce case_id = current_setting('app.case_id')::text
--
-- IMPORTANT: Even with RLS, service-layer enforcement is still required by Contract v1.

-- Example (commented; enable in implementation phase):
-- ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY runs_case_isolation ON runs
--   USING (case_id IS NULL OR case_id = current_setting('app.case_id', true));
--
-- ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY transcripts_case_isolation ON transcripts
--   USING (case_id = current_setting('app.case_id', true));
--
-- Repeat for all case-plane tables.

COMMIT;
