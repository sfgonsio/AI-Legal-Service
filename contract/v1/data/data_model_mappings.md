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
- Orchestration:
  - `contract/v1/orchestration/orchestrator_contract.md`
- Execution:
  - `contract/v1/execution/run_lifecycle.md`
  - `contract/v1/execution/run_status_model.md`

Non-Negotiable:
- Case data MUST be case-scoped and isolated by default.
- Shared knowledge MUST only be written via governed promotion lanes.
- All artifacts referenced in run/audit/export MUST conform to `artifact_ref` (SSOT binding).
- Tool calls MUST be mediated by the tool gateway; audit events MUST be emitted for allow/deny and outcomes.

---

## 1) Storage Planes (Physical Separation)

### 1.1 Case Plane (isolated)
Stores all case-scoped data and artifacts. Default plane for runs, audit correlation, transcripts, extracted facts, evidence maps, etc.

- Required partition key: `case_id`

### 1.2 Shared Knowledge Plane (curated)
Stores sanitized, promoted insights only (no raw case text, no identities, no privileged notes). Writes allowed only via promotion lanes.

- Required partition key: `promotion_ticket_id`
- Required gate: `attorney_signoff` (as required by lane `PROMOTE_SHARED_KNOWLEDGE`)

### 1.3 System Plane (operational)
Stores system configuration, policy snapshots/versions, tool adapters, job metadata, health metrics. Does NOT store case facts.

---

## 2) Database Selection Guidance (Implementation Choice)

Contract v1 supports either:
- Relational DB (PostgreSQL recommended) for structured entities + audit integrity
- Object storage (S3-equivalent) for large artifacts (PDFs, audio, transcripts)

Recommended hybrid:
- Postgres for: runs, audit ledger, export bundles, domain/capability tables, entity indexes
- Object storage for: raw documents, audio, large transcripts, derived files

Rule: Large payloads are stored as artifacts; DB stores references + hashes + metadata.

---

## 3) Canonical Schema → Physical Table Mappings (SSOT)

This section resolves naming differences between schema documents and physical DDL.

| Contract Schema | Canonical Meaning | Physical Table (Postgres DDL) |
|---|---|---|
| `run_record.schema.yaml` | Run record / run envelope | `runs` |
| `audit_event.schema.yaml` | Append-only audit events | `audit_ledger` |
| `artifact_ref.schema.yaml` | Artifact reference binding | `artifacts` (registry) + `*_artifacts_json` fields holding `artifact_ref` arrays |
| `export_bundle.schema.yaml` | Export bundle manifest + integrity | `export_bundles` |

Rule:
- Physical naming MAY differ, but this mapping is authoritative for v1.
- Any implementation changes must update this mapping document and preserve semantics.

---

## 4) Canonical Tables / Collections (Minimum Required)

### 4.1 `runs`  (maps to `run_record` schema)
Stores a single run record per `run_id`.

Minimum columns:
- `run_id` (PK)
- `parent_run_id` (nullable)
- `root_run_id` (nullable)
- `correlation_id` (nullable)
- `run_kind`
- `status`
- `contract_version`
- `policy_versions_lanes`
- `policy_versions_roles`
- `taxonomy_versions_coa` (nullable)
- `taxonomy_versions_tags` (nullable)
- `taxonomy_versions_entities` (nullable)
- `case_id` (nullable; required for case-scoped runs)
- `lane_id` (nullable)
- `actor_type`, `actor_id`, `role_id` (nullable)
- `created_at_utc`
- `started_at_utc` (nullable)
- `completed_at_utc` (nullable)
- `error_code` (nullable)
- `error_message_bounded` (nullable)
- `retryable` (nullable boolean)
- `metadata_json` (jsonb; bounded)

Artifact refs:
- `inputs_artifacts_json` (jsonb array of `artifact_ref`)
- `outputs_artifacts_json` (jsonb array of `artifact_ref`)

Indexes:
- PK: `(run_id)`
- `(case_id, created_at_utc DESC)`
- `(root_run_id)`
- `(parent_run_id)`
- `(run_kind, status)`
- `(policy_versions_lanes, policy_versions_roles)`

Retention:
- Case Plane: retain per firm litigation lifecycle policy (recommended long-lived)
- System Plane: retain operational runs per SRE policy

---

### 4.2 `audit_ledger`  (maps to `audit_event` schema)
Append-only authoritative audit ledger.

Minimum columns:
- `event_id` (PK)
- `timestamp_utc`
- `action_type`
- `outcome`
- `outcome_reason_bounded` (nullable)
- `contract_version`
- `policy_versions_lanes`
- `policy_versions_roles`
- `case_id` (nullable)
- `lane_id` (nullable)
- `run_id`
- `parent_run_id` (nullable)
- `root_run_id` (nullable)
- `actor_type`, `actor_id`, `role_id` (nullable)
- `target_json` (jsonb)
- `request_hash_sha256` (nullable)
- `response_hash_sha256` (nullable)
- `input_artifacts_json` (jsonb array of `artifact_ref`)
- `output_artifacts_json` (jsonb array of `artifact_ref`)
- `error_code` (nullable)
- `error_message_bounded` (nullable)
- `retryable` (nullable boolean)

Append-only enforcement:
- Production DB permissions must disallow UPDATE/DELETE.
- Corrections use compensating audit events referencing prior event_id.

Indexes:
- PK: `(event_id)`
- `(run_id, timestamp_utc)`
- `(case_id, timestamp_utc DESC)`
- `(action_type, outcome, timestamp_utc DESC)`
- `(lane_id, timestamp_utc DESC)`

Retention:
- High: audit retention is legal-grade; typically long-lived.

---

### 4.3 `artifacts`  (artifact registry; binds `artifact_ref`)
One row per registered artifact.

Minimum columns:
- `artifact_id` (PK)
- `artifact_kind` (e.g., source_document, transcript, evidence_map, export_bundle)
- `case_id` (nullable; required for case-scoped)
- `plane` (`case|shared|system`)
- `storage_uri` (opaque locator to object storage)
- `content_hash_sha256`
- `size_bytes` (nullable)
- `mime_type` (nullable)
- `created_at_utc`
- `created_by_run_id` (nullable)
- `created_by_actor_id` (nullable)
- `tags_json` (jsonb array; optional)
- `metadata_json` (jsonb; bounded)

Indexes:
- PK: `(artifact_id)`
- Unique: `(content_hash_sha256)` (dedupe)
- `(case_id, created_at_utc DESC)`
- `(artifact_kind)`

Rule:
- No raw binary content is stored in DB.
- Text payloads should be artifacts when large or privileged; DB stores references.

---

### 4.4 `export_bundles`  (maps to `export_bundle` schema)
Stores export bundle manifest + integrity hashes.

Minimum columns:
- `bundle_id` (PK)
- `bundle_kind`
- `bundle_name` (nullable)
- `bundle_description_bounded` (nullable)
- `scope` (`case|shared|system`)
- `case_id` (nullable; required for case export)
- `export_reason` (required by lane `EXPORT_CASE_DATA`)
- `contract_version`
- `policy_versions_lanes`
- `policy_versions_roles`
- `taxonomy_versions_coa/tags/entities` (nullable)
- `status`
- `created_at_utc`
- `completed_at_utc` (nullable)
- `created_by_actor_type`, `created_by_actor_id`, `created_by_role_id` (nullable)
- `approvals_json` (jsonb)
- `contents_json` (jsonb: artifacts[], included_tables[], filters)
- `integrity_json` (jsonb: manifest_hash_sha256, package_hash_sha256, package_locator)
- `signatures_json` (jsonb)
- `audit_json` (jsonb: audit_event_ids[], run_ids[])
- `redaction_json` (jsonb)

Indexes:
- PK: `(bundle_id)`
- `(case_id, created_at_utc DESC)`
- `(status, created_at_utc DESC)`
- `(export_reason)` (recommended)

Rule:
- Bundle contents must reference artifacts via `artifact_ref` (SSOT binding).

---

## 5) Domain Tables (Case Plane Modules) + Lane Write Boundaries

These are “capability tables.” They are written only by specific governed lanes per `lanes.yaml`.

### 5.1 Lane → Table Write Map (authoritative)

| Lane | Allowed Writes (tables) | Mode |
|---|---|---|
| `WRITE_INTAKE_ARTIFACTS` | `transcripts`, `interview_notes`, `entities` | append / append / upsert |
| `WRITE_MAPPING_OUTPUTS` | `facts`, `evidence_map`, `coa_map` | append |
| `PROMOTE_SHARED_KNOWLEDGE` | `shared_playbooks`, `shared_heuristics` | append |
| `EXPORT_CASE_DATA` | `export_bundles` | append |
| `SYSTEM_OVERRIDE` | `override_events` | append |

Rule:
- Any write outside this mapping is a contract violation and must be denied + audited.

---

### 5.2 Case Plane Tables (minimum)

#### `transcripts` (append)
Minimum columns:
- `transcript_id` (PK)
- `case_id`
- `run_id`
- `session_id` (nullable)
- `artifact_id` (FK to `artifacts`) OR `artifact_ref_json` (if chosen)
- `created_at_utc`

Indexes:
- `(case_id, created_at_utc DESC)`
- `(run_id)`

#### `interview_notes` (append)
Minimum columns:
- `note_id` (PK)
- `case_id`
- `run_id`
- `session_id` (nullable)
- `note_text_bounded` (nullable) OR `note_artifact_id` (nullable)
- `created_at_utc`

Indexes:
- `(case_id, created_at_utc DESC)`
- `(run_id)`

#### `entities` (upsert)
Minimum columns:
- `entity_id` (PK)
- `case_id`
- `canonical_name`
- `entity_type` (`person|organization|government_body|location|other`)
- `aliases_json` (jsonb)
- `source_artifact_id` (nullable)
- `created_by_run_id`
- `updated_at_utc`

Indexes:
- Unique: `(case_id, canonical_name)`
- `(case_id, entity_type)`

#### `facts` (append)
Minimum columns:
- `fact_id` (PK)
- `case_id`
- `run_id`
- `statement_bounded` (nullable) OR `statement_artifact_id` (nullable)
- `confidence` (nullable numeric)
- `supporting_artifacts_json` (jsonb array of `artifact_ref`)
- `created_at_utc`

Indexes:
- `(case_id, created_at_utc DESC)`
- `(run_id)`

#### `evidence_map` (append)
Minimum columns:
- `map_id` (PK)
- `case_id`
- `run_id`
- `evidence_artifact_id` (nullable) OR `evidence_artifact_ref_json` (nullable)
- `fact_ids_json` (jsonb)
- `created_at_utc`

Indexes:
- `(case_id, created_at_utc DESC)`

#### `coa_map` (append)
Minimum columns:
- `coa_map_id` (PK)
- `case_id`
- `run_id`
- `coa_version`
- `mappings_json` (jsonb)
- `created_at_utc`

Indexes:
- `(case_id, coa_version, created_at_utc DESC)`

---

### 5.3 Shared Knowledge Plane Tables (append; sanitized only)

#### `shared_playbooks`
Minimum columns:
- `playbook_id` (PK)
- `promotion_ticket_id`
- `run_id`
- `attorney_signoff` (boolean; required gate)
- `title` (nullable)
- `content_json` (jsonb; sanitized)
- `created_at_utc`

#### `shared_heuristics`
Minimum columns:
- `heuristic_id` (PK)
- `promotion_ticket_id`
- `run_id`
- `attorney_signoff` (boolean; required gate)
- `heuristic_type` (nullable)
- `content_json` (jsonb; sanitized)
- `created_at_utc`

Rules:
- Prohibit raw case text, client identity, privileged notes (per `lanes.yaml`).
- Promotion events MUST be audited with ticket id and signoff.

---

### 5.4 System / Break-Glass Table (append only)

#### `override_events`
Minimum columns:
- `override_event_id` (PK)
- `override_ticket_id`
- `run_id`
- `case_id` (nullable)
- `actor_id` (nullable)
- `role_id` (nullable)
- `override_reason_bounded`
- `action`
- `before_json` (jsonb)
- `after_json` (jsonb)
- `created_at_utc`

Rule:
- Break-glass is exception-only; must be fully auditable.

---

## 6) Policy + Taxonomy Storage (Optional but Recommended for Replay)

### 6.1 Policy snapshots
Table: `policy_snapshots`
- `snapshot_id` (PK)
- `policy_type` (`lanes|roles`)
- `git_sha` (unique)
- `content_hash_sha256`
- `stored_at_utc`
- `blob_uri` (nullable) OR `content_json`

### 6.2 Taxonomy snapshots
Table: `taxonomy_snapshots`
- `snapshot_id` (PK)
- `taxonomy_type` (`coa|tags|entities`)
- `git_sha` (unique)
- `content_hash_sha256`
- `stored_at_utc`
- `blob_uri` (nullable) OR `content_json`

Rule:
- Run records should reference effective versions (and optionally git SHAs) to support replay even if repo changes.

---

## 7) Partitioning and Isolation Rules (Defect Prevention)

Non-negotiable:
- Any table with case-scoped data MUST include `case_id`.
- Any query for case-scoped data MUST filter by `case_id`.
- Cross-case queries are denied unless explicitly allowed by a lane.

Recommended enforcement:
- DB row-level security (RLS) or ABAC enforcement keyed by `case_id`.
- Service-level enforcement is required even if DB-level enforcement exists.

---

## 8) Artifact Storage (Object Store)

Artifacts live in object storage with:
- `storage_uri` (opaque)
- `content_hash_sha256` (integrity)
- recommended plane partition path:
  - case: `case/{case_id}/artifacts/{artifact_id}`
  - shared: `shared/{category}/artifacts/{artifact_id}`
  - system: `system/artifacts/{artifact_id}`

Rule:
- Audit/run/export reference artifacts; they do not embed raw binary or privileged content by default.

---

## 9) Minimal Build Checklist (Antigravity)

Antigravity implementation MUST:
- Create physical tables corresponding to: `runs`, `audit_ledger`, `artifacts`, `export_bundles`, and all lane-driven domain tables.
- Enforce case partitioning via `case_id` for all case-plane tables.
- Implement append-only semantics for `audit_ledger`.
- Ensure all referenced artifacts conform to `artifact_ref` schema.
- Ensure policy_versions are pinned and recorded on all run/audit/export records.
- Ensure governed lanes restrict tool calls and writes to allowed targets.

End.