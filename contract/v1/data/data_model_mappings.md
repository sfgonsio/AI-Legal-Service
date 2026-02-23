# Data Model Mappings (Contract v1)

Purpose: Map Contract v1 schemas and governed artifacts to physical storage structures (tables/collections, indexes, partitions, retention) so implementation is deterministic and reviewable. This document is design-and-build instruction for Antigravity.

Authoritative sources:
- Schemas:
  - `contract/v1/schemas/artifact_ref.schema.yaml`
  - `contract/v1/schemas/run_record.schema.yaml`
  - `contract/v1/schemas/audit_event.schema.yaml`
  - `contract/v1/schemas/export_bundle.schema.yaml`
- Policies:
  - `contract/v1/policy/lanes.yaml`
  - `contract/v1/policy/roles.yaml`
- Execution:
  - `contract/v1/execution/run_lifecycle.md`

Non-Negotiable:
- Case data MUST be case-scoped and isolated by default.
- Shared knowledge MUST only be written via governed promotion lanes.
- All artifacts referenced in run/audit/export MUST conform to `artifact_ref` (SSOT binding).

---

## 1) Storage Planes (Physical Separation)

### 1.1 Case Plane (isolated)
Stores all case-scoped data and artifacts. Default plane for runs, audit correlation, transcripts, extracted facts, evidence maps, etc.

Required partition key: `case_id`

### 1.2 Shared Knowledge Plane (curated)
Stores sanitized, promoted insights only (no raw case text, no identities, no privileged notes). Writes allowed only via promotion lanes.

Required partition key: `shared_scope` (e.g., "global") + `promotion_ticket_id`

### 1.3 System Plane (operational)
Stores system configuration, policy snapshots/versions, tool adapters, job metadata, health metrics. Does NOT store case facts.

---

## 2) Database Selection Guidance (Implementation Choice)

Contract v1 supports either:
- Relational DB (PostgreSQL recommended) for structured entities + audit integrity
- Object storage (S3-equivalent) for large artifacts (PDFs, audio, transcripts)

Recommended hybrid:
- Postgres for: runs, audit ledger, export bundles, structured mappings, entity indexes
- Object storage for: raw documents, audio, large transcripts, derived files

Rule: Large payloads are stored as artifacts; DB stores references + hashes + metadata.

---

## 3) Canonical Tables / Collections (Minimum Required)

### 3.1 `runs`  (from run_record schema)
Stores a single run record per run_id.

Minimum columns:
- run_id (PK)
- parent_run_id (nullable)
- root_run_id (nullable)
- correlation_id (nullable)
- run_kind
- status
- contract_version
- policy_versions_lanes
- policy_versions_roles
- taxonomy_versions_coa (nullable)
- taxonomy_versions_tags (nullable)
- taxonomy_versions_entities (nullable)
- case_id (nullable; required for case-scoped runs)
- lane_id (nullable)
- actor_type, actor_id, role_id (nullable)
- created_at_utc
- started_at_utc (nullable)
- completed_at_utc (nullable)
- error_code (nullable)
- error_message_bounded (nullable)
- retryable (nullable boolean)
- metadata_json (jsonb; bounded)

Artifact refs:
- inputs_artifacts_json (jsonb array of artifact_ref)
- outputs_artifacts_json (jsonb array of artifact_ref)

Indexes:
- PK: (run_id)
- idx_runs_case_created: (case_id, created_at_utc DESC)
- idx_runs_root: (root_run_id)
- idx_runs_parent: (parent_run_id)
- idx_runs_kind_status: (run_kind, status)
- idx_runs_policy: (policy_versions_lanes, policy_versions_roles)

Retention:
- Case Plane: per firm policy; recommended retain >= litigation lifecycle
- System Plane: retain operational runs per SRE policy

---

### 3.2 `audit_ledger`  (from audit_event schema)
Append-only authoritative ledger.

Minimum columns:
- event_id (PK)
- timestamp_utc
- action_type
- outcome
- outcome_reason_bounded (nullable)
- contract_version
- policy_versions_lanes
- policy_versions_roles
- case_id (nullable)
- lane_id (nullable)
- run_id
- parent_run_id (nullable)
- root_run_id (nullable)
- actor_type, actor_id, role_id (nullable)
- target_json (jsonb; tool/db/promotion/export targets)
- request_hash_sha256 (nullable)
- response_hash_sha256 (nullable)
- input_artifacts_json (jsonb array of artifact_ref; nullable)
- output_artifacts_json (jsonb array of artifact_ref; nullable)
- error_code (nullable)
- error_message_bounded (nullable)
- retryable (nullable boolean)

Append-only enforcement:
- DB permissions must disallow UPDATE/DELETE to this table in production.
- If corrections are needed, emit a new compensating audit event referencing the prior event_id.

Indexes:
- PK: (event_id)
- idx_audit_run: (run_id, timestamp_utc)
- idx_audit_case: (case_id, timestamp_utc DESC)
- idx_audit_action: (action_type, outcome, timestamp_utc DESC)
- idx_audit_lane: (lane_id, timestamp_utc DESC)

Retention:
- High: audit retention is legal-grade; typically long-lived.

---

### 3.3 `artifacts`  (canonical artifact registry; binds artifact_ref)
One row per artifact_id (or per content hash).

Minimum columns:
- artifact_id (PK) OR (content_hash_sha256 as PK) depending on design
- artifact_kind (e.g., source_document, transcript, evidence_map, export_bundle)
- case_id (nullable; required if case-scoped)
- plane (case|shared|system)
- storage_uri (opaque locator to object storage)
- content_hash_sha256 (64 hex)
- size_bytes (nullable)
- mime_type (nullable)
- created_at_utc
- created_by_run_id (nullable)
- created_by_actor_id (nullable)
- tags_json (jsonb array; optional)
- metadata_json (jsonb; bounded)

Indexes:
- PK: (artifact_id) or (content_hash_sha256)
- idx_artifacts_case: (case_id, created_at_utc DESC)
- idx_artifacts_hash: (content_hash_sha256)
- idx_artifacts_kind: (artifact_kind)

Rule:
- No raw content in this table. Content lives in object storage.

---

### 3.4 `export_bundles`  (from export_bundle schema)
Stores export bundle manifest + integrity hashes.

Minimum columns:
- bundle_id (PK)
- bundle_kind
- bundle_name (nullable)
- bundle_description_bounded (nullable)
- scope (case|shared|system)
- case_id (nullable; required for case export)
- contract_version
- policy_versions_lanes
- policy_versions_roles
- taxonomy_versions_coa/tags/entities (nullable)
- status
- created_at_utc
- completed_at_utc (nullable)
- created_by_actor_type, created_by_actor_id, created_by_role_id (nullable)
- approvals_json (jsonb; nullable)
- contents_json (jsonb: artifacts[], included_tables[], filters)
- integrity_json (jsonb: manifest_hash_sha256, package_hash_sha256, package_locator)
- signatures_json (jsonb; nullable)
- audit_json (jsonb: audit_event_ids[], run_ids[])
- redaction_json (jsonb; nullable)

Indexes:
- PK: (bundle_id)
- idx_bundles_case: (case_id, created_at_utc DESC)
- idx_bundles_status: (status, created_at_utc DESC)

Rule:
- Bundle contents must reference artifacts via artifact_ref (SSOT binding).

---

## 4) Domain Tables (Case Plane Modules)

These are “capability tables.” They are written only by specific governed lanes per `lanes.yaml`.

### 4.1 `transcripts`
- transcript_id (PK)
- case_id
- run_id
- session_id (nullable)
- artifact_id (FK to artifacts) OR artifact_ref_json
- created_at_utc

Indexes:
- (case_id, created_at_utc DESC)
- (run_id)

### 4.2 `entities`
- entity_id (PK)
- case_id
- canonical_name
- entity_type (person|org|location|other)
- aliases_json (jsonb)
- source_artifact_id (nullable)
- created_by_run_id
- updated_at_utc

Indexes:
- (case_id, canonical_name)
- (case_id, entity_type)

### 4.3 `facts`
- fact_id (PK)
- case_id
- run_id
- statement_bounded (or artifact_ref to full statement)
- confidence (nullable numeric)
- supporting_artifacts_json (artifact_ref array)
- created_at_utc

Indexes:
- (case_id, created_at_utc DESC)
- (run_id)

### 4.4 `evidence_map`
- map_id (PK)
- case_id
- run_id
- evidence_artifact_ref (artifact_ref)
- fact_ids_json (array)
- created_at_utc

Indexes:
- (case_id, created_at_utc DESC)

### 4.5 `coa_map`
- coa_map_id (PK)
- case_id
- run_id
- coa_version
- mappings_json (structured mapping results; bounded)
- created_at_utc

Indexes:
- (case_id, coa_version, created_at_utc DESC)

Rule:
- These tables are examples aligned to your current lanes (WRITE_INTAKE_ARTIFACTS, WRITE_MAPPING_OUTPUTS).
- Antigravity may refine names but MUST preserve governed write boundaries and case partitioning.

---

## 5) Policy + Taxonomy Storage

### 5.1 Policy snapshots (optional but recommended)
Store committed copies or resolved effective policy sets used at runtime for evidence-grade replay.

Table: `policy_snapshots`
- snapshot_id (PK)
- policy_type (lanes|roles)
- git_sha (unique)
- content_hash_sha256
- stored_at_utc
- blob_uri or content_json

### 5.2 Taxonomy snapshots (optional but recommended)
Table: `taxonomy_snapshots`
- snapshot_id (PK)
- taxonomy_type (coa|tags|entities)
- git_sha (unique)
- content_hash_sha256
- stored_at_utc
- blob_uri or content_json

Rule:
- Run records can reference the SHA; snapshot storage enables later replay even if repo changes.

---

## 6) Partitioning and Isolation Rules (Defect Prevention)

Non-negotiable:
- Any table with case-scoped data MUST include `case_id`.
- Any query for case-scoped data MUST be filtered by `case_id`.
- Cross-case queries are denied unless explicitly allowed by a lane.

Recommended enforcement:
- DB row-level security (RLS) or equivalent ABAC enforcement using case_id.
- Service-level enforcement is required even if DB-level enforcement exists.

---

## 7) Indexing and Performance Minimums

Minimum required indexes are specified above. Additionally:
- Use JSONB indexes sparingly (only for high-frequency filters).
- Prefer structured columns for frequently queried fields (case_id, run_id, created_at).

---

## 8) Artifact Storage (Object Store)

Artifacts live in object storage with:
- storage_uri (opaque)
- content_hash_sha256 (integrity)
- plane partition path (recommended):
  - case: `case/{case_id}/artifacts/{artifact_id}`
  - shared: `shared/{category}/artifacts/{artifact_id}`
  - system: `system/artifacts/{artifact_id}`

Rule:
- Audit/run/export records reference artifacts; they do not embed raw binary or privileged content by default.

---

## 9) Minimal Build Checklist (Antigravity)

Antigravity implementation MUST:
- Create tables/collections corresponding to runs, audit_ledger, artifacts, export_bundles.
- Enforce case partitioning via case_id for all case-plane tables.
- Implement append-only semantics for audit_ledger.
- Ensure all referenced artifacts conform to artifact_ref schema.
- Ensure policy_versions are pinned and recorded on all run/audit/export records.
- Ensure governed lanes restrict tool calls and writes to allowed targets.

End.