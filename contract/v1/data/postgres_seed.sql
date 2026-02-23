-- contract/v1/data/postgres_seed.sql
-- Contract v1 Seed Dataset
-- Purpose: deterministic bootstrap dataset for validation + smoke testing

BEGIN;

-- =========================================================
-- 1) POLICY SNAPSHOTS
-- =========================================================
INSERT INTO policy_snapshots (
  snapshot_id,
  policy_type,
  git_sha,
  content_hash_sha256,
  stored_at_utc,
  content_json
)
VALUES
(
  'policy_lanes_v1_seed',
  'lanes',
  'SEED_SHA_LANES',
  'SEED_HASH_LANES',
  NOW(),
  '{}'::jsonb
),
(
  'policy_roles_v1_seed',
  'roles',
  'SEED_SHA_ROLES',
  'SEED_HASH_ROLES',
  NOW(),
  '{}'::jsonb
)
ON CONFLICT DO NOTHING;

-- =========================================================
-- 2) CASE IDENTIFIER
-- =========================================================
-- canonical test case
-- replace with real cases in production

-- no case table required by contract
-- case_id is authoritative string

-- =========================================================
-- 3) ROOT RUN
-- =========================================================
INSERT INTO runs (
  run_id,
  parent_run_id,
  root_run_id,
  run_kind,
  status,
  contract_version,
  policy_versions_lanes,
  policy_versions_roles,
  case_id,
  created_at_utc
)
VALUES (
  'RUN_ROOT_001',
  NULL,
  NULL,
  'orchestrator',
  'completed',
  'v1',
  'SEED_SHA_LANES',
  'SEED_SHA_ROLES',
  'CASE_DEMO_001',
  NOW()
)
ON CONFLICT DO NOTHING;


-- =========================================================
-- 4) ARTIFACT — SOURCE DOCUMENT
-- =========================================================
INSERT INTO artifacts (
  artifact_id,
  artifact_kind,
  case_id,
  plane,
  storage_uri,
  content_hash_sha256,
  created_at_utc
)
VALUES (
  'ART_DOC_001',
  'source_document',
  'CASE_DEMO_001',
  'case',
  's3://case/CASE_DEMO_001/artifacts/doc1.pdf',
  'HASH_DOC_001',
  NOW()
)
ON CONFLICT DO NOTHING;


-- =========================================================
-- 5) AGENT RUN (child of root)
-- =========================================================
INSERT INTO runs (
  run_id,
  parent_run_id,
  root_run_id,
  run_kind,
  status,
  contract_version,
  policy_versions_lanes,
  policy_versions_roles,
  case_id,
  created_at_utc
)
VALUES (
  'RUN_AGENT_001',
  'RUN_ROOT_001',
  'RUN_ROOT_001',
  'agent',
  'completed',
  'v1',
  'SEED_SHA_LANES',
  'SEED_SHA_ROLES',
  'CASE_DEMO_001',
  NOW()
)
ON CONFLICT DO NOTHING;


-- =========================================================
-- 6) TOOL GATEWAY RUN
-- =========================================================
INSERT INTO runs (
  run_id,
  parent_run_id,
  root_run_id,
  run_kind,
  status,
  contract_version,
  policy_versions_lanes,
  policy_versions_roles,
  case_id,
  lane_id,
  created_at_utc
)
VALUES (
  'RUN_TOOL_001',
  'RUN_AGENT_001',
  'RUN_ROOT_001',
  'tool_gateway',
  'completed',
  'v1',
  'SEED_SHA_LANES',
  'SEED_SHA_ROLES',
  'CASE_DEMO_001',
  'TOOL_INTERVIEW_CAPTURE',
  NOW()
)
ON CONFLICT DO NOTHING;


-- =========================================================
-- 7) AUDIT EVENTS
-- =========================================================

-- authorization
INSERT INTO audit_ledger (
  event_id,
  timestamp_utc,
  action_type,
  outcome,
  contract_version,
  policy_versions_lanes,
  policy_versions_roles,
  case_id,
  lane_id,
  run_id
)
VALUES (
  'AUDIT_001',
  NOW(),
  'authz_decision',
  'allow',
  'v1',
  'SEED_SHA_LANES',
  'SEED_SHA_ROLES',
  'CASE_DEMO_001',
  'TOOL_INTERVIEW_CAPTURE',
  'RUN_TOOL_001'
);

-- tool call
INSERT INTO audit_ledger (
  event_id,
  timestamp_utc,
  action_type,
  outcome,
  contract_version,
  policy_versions_lanes,
  policy_versions_roles,
  case_id,
  lane_id,
  run_id,
  target_json
)
VALUES (
  'AUDIT_002',
  NOW(),
  'tool_call',
  'success',
  'v1',
  'SEED_SHA_LANES',
  'SEED_SHA_ROLES',
  'CASE_DEMO_001',
  'TOOL_INTERVIEW_CAPTURE',
  'RUN_TOOL_001',
  '{"tool":"transcription.run"}'
);


-- =========================================================
-- 8) GENERATED ARTIFACT (TRANSCRIPT)
-- =========================================================
INSERT INTO artifacts (
  artifact_id,
  artifact_kind,
  case_id,
  plane,
  storage_uri,
  content_hash_sha256,
  created_at_utc,
  created_by_run_id
)
VALUES (
  'ART_TRANSCRIPT_001',
  'transcript',
  'CASE_DEMO_001',
  'case',
  's3://case/CASE_DEMO_001/artifacts/transcript1.txt',
  'HASH_TRANSCRIPT_001',
  NOW(),
  'RUN_TOOL_001'
)
ON CONFLICT DO NOTHING;


-- =========================================================
-- 9) DOMAIN TABLE WRITE
-- =========================================================
INSERT INTO transcripts (
  transcript_id,
  case_id,
  run_id,
  artifact_id,
  created_at_utc
)
VALUES (
  'TRANSCRIPT_001',
  'CASE_DEMO_001',
  'RUN_TOOL_001',
  'ART_TRANSCRIPT_001',
  NOW()
)
ON CONFLICT DO NOTHING;


-- =========================================================
-- 10) EXPORT BUNDLE
-- =========================================================
INSERT INTO export_bundles (
  bundle_id,
  bundle_kind,
  scope,
  case_id,
  contract_version,
  policy_versions_lanes,
  policy_versions_roles,
  status,
  created_at_utc
)
VALUES (
  'EXPORT_001',
  'case_export',
  'case',
  'CASE_DEMO_001',
  'v1',
  'SEED_SHA_LANES',
  'SEED_SHA_ROLES',
  'completed',
  NOW()
)
ON CONFLICT DO NOTHING;


COMMIT;