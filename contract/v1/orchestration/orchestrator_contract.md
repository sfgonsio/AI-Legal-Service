# Orchestrator Contract (v1)

**Status:** Authoritative  
**Applies To:** `contract/v1/*`  
**SSOT Rule:** Contract v1 text supersedes all visuals.  
**Purpose:** Define the deterministic run orchestration model, gates, lane enforcement, and auditability requirements for the AI Legal Service platform.

---

## 1. Authoritative References (SSOT)

This orchestrator contract is governed by and must remain consistent with:

- **Manifest (SSOT index):** `../contract_manifest.yaml`
- **Roles:** `../policy/roles.yaml`
- **Lanes:** `../policy/lanes.yaml`
- **Policy Versioning:** `../policy/policy_versioning.md`
- **Taxonomy Versioning:** `../taxonomies/taxonomy_versioning.md`
- **Tool Registry:** `../tools/tool_registry.yaml`
- **Tool Gateway Contract:** `../tools/tool_gateway_contract.md`
- **Run Lifecycle:** `../execution/run_lifecycle.md`
- **Run Status Model:** `../execution/run_status_model.md`

Schemas (must remain aligned):
- `../schemas/run_record.schema.yaml`
- `../schemas/audit_event.schema.yaml`
- `../schemas/artifact_ref.schema.yaml`
- `../schemas/export_bundle.schema.yaml`

Data layer (must support schemas):
- `../data/postgres_ddl.sql`
- `../data/data_model_mappings.md`

---

## 2. Core Orchestrator Responsibilities

The orchestrator MUST:

1. Enforce **case-scoped execution** (no cross-case access).
2. Enforce **lane-based authorization** for every tool call and write action.
3. Produce **run_record** entries and maintain a single **authoritative run state**.
4. Emit **audit_event** records for:
   - run state transitions
   - lane invocations (authorized/denied)
   - tool gateway calls (requested/executed/failed)
   - taxonomy lock/unlock events
   - exports created and signed off
5. Enforce **gates** that require attorney approval, including:
   - knowledge promotion
   - export creation/signoff
   - break-glass overrides
6. Provide deterministic, replayable ordering of execution steps.

---

## 3. Deterministic Run Model

### 3.1 Run Identity
Each orchestrated run MUST be bound to:
- `case_id`
- `run_id`
- `contract_version` (v1)
- `policy_version` (from policy versioning)
- `taxonomy_versions` (coa/entities/tags used)
- `tool_registry_version` (from tool_registry.yaml)

### 3.2 Immutable Inputs
Once a run begins, the following are immutable for that run:
- contract_version
- policy_version
- taxonomy versions (or case-instance lock versions)
- tool registry version
- input artifact set (artifact refs)

If new inputs arrive after validation, rerun policy applies (see §7).

---

## 4. Lane Enforcement

### 4.1 General Rule
All actions MUST map to exactly one lane declared in `lanes.yaml`.

- If no lane applies → **DENY** and emit an audit event.
- If caller role is not allowed in the lane → **DENY** and emit an audit event.
- If required scope fields are missing → **DENY** and emit an audit event.

### 4.2 Lane Invocation Event
Every lane invocation MUST emit:
- `lane_id`
- caller `role_id`
- `case_id`
- `run_id`
- `authorized` boolean
- `reason` (if denied)
- `timestamp`

---

## 5. Canonical Orchestration Flow (v1)

This is the normative order. Variations require explicit policy in `policy_versioning.md`.

### Stage 0 — Run Create (System)
**Goal:** Create a run container and initial run_record.

- Create `run_record` with status = `CREATED`
- Emit audit_event `run_state_change: CREATED`

**Outputs:**
- run_record (CREATED)
- audit_event

---

### Stage 1 — Interview Capture (INTERVIEW_AGENT)
**Lane:** `TOOL_INTERVIEW_CAPTURE`  
**Goal:** Capture client narrative and structured responses.

- Tool calls must be mediated through the tool gateway
- All produced artifacts must be stored as artifact refs (transcript segments, audio refs, structured Q/A)

**Gate:** None (but must be auditable)

**Outputs:**
- artifact_ref(s): transcripts/audio/qa
- audit_event(s): tool calls + lane invoked

---

### Stage 2 — Persist Intake Artifacts (INTERVIEW_AGENT, INTAKE_AGENT)
**Lane:** `WRITE_INTAKE_ARTIFACTS`  
**Goal:** Persist interview artifacts into case storage.

- Append transcript rows
- Append interview notes
- Upsert entity candidates (status=candidate unless attorney-promoted)

**Gate:** None

**Outputs:**
- case tables updated (transcripts, interview_notes, entities)
- audit_event(s): lane invoked + writes performed

---

### Stage 3 — Case Validation (ATTORNEY_ADMIN)
**Lane:** `SYSTEM_OVERRIDE` is NOT used for normal validation.  
**Goal:** Attorney confirms understanding and locks “validated case snapshot”.

**Required Outcomes:**
- A “validation checkpoint” artifact is created (artifact_ref)
- Run status set to `VALIDATED`
- Taxonomy versions for the run are fixed (see Stage 4)

**Gate:** Attorney action required (normal authority, not break-glass)

**Outputs:**
- artifact_ref: validation_checkpoint
- audit_event: validation_completed
- run_record: status VALIDATED

---

### Stage 4 — Taxonomy Lock (ATTORNEY_ADMIN)
**Goal:** Ensure the run uses fixed taxonomies:
- COA base version (and/or case-instance COA)
- Tags schema version
- Entity schema version

**Rules:**
- If case-instance taxonomies exist, they become authoritative for this case once locked.
- Lock events must be recorded in run_record.

**Outputs:**
- run_record updated with taxonomy versions/lock refs
- audit_event: taxonomy_lock

---

### Stage 5 — COA Mapping (MAPPING_AGENT)
**Lane:** `WRITE_MAPPING_OUTPUTS`  
**Goal:** Map facts/evidence to COAs using locked taxonomies.

- Append facts
- Append evidence_map entries
- Append coa_map entries

**Gate:** Must be post-validation + post-taxonomy-lock

**Outputs:**
- facts, evidence_map, coa_map appended
- audit_event(s): lane invoked + writes performed

---

### Stage 6 — Promote Shared Knowledge (optional)
**Lane:** `PROMOTE_SHARED_KNOWLEDGE`  
**Goal:** Promote sanitized, non-identifying insights into shared knowledge plane.

**Hard Requirements (from lane scope):**
- `promotion_ticket_id`
- `run_id`
- `attorney_signoff`

**Prohibitions:**
- raw case text
- client identity
- privileged notes

**Outputs:**
- shared_playbooks/shared_heuristics appended (sanitized only)
- audit_event: promotion_completed

---

### Stage 7 — Export Case Data (optional)
**Lane:** `EXPORT_CASE_DATA`  
**Goal:** Create export bundles for downstream attorney work (filing prep, discovery preparation, client delivery).

**Requirements:**
- `case_id`
- `run_id`
- `export_reason`

**Outputs:**
- export_bundle artifact(s)
- export_bundles table row
- audit_event: export_created + export_signed_off

---

### Stage 8 — Run Close
**Goal:** Freeze run and declare terminal state.

- Set run status to terminal state (e.g., `COMPLETED` or `FAILED`)
- Ensure all artifacts have artifact_ref entries
- Emit audit_event `run_state_change: COMPLETED|FAILED`

---

## 6. Tool Gateway Requirements

All tool invocations MUST:
- go through the tool gateway
- be allowlisted in `tool_registry.yaml`
- produce audit events for:
  - request
  - execution
  - response summary
  - failure (if any)

Any direct tool call path outside the gateway is a contract violation.

---

## 7. Rerun Policy (Late Evidence / Changed Inputs)

### 7.1 Late Evidence Trigger
If new evidence or material input arrives after Stage 3 (VALIDATED), the orchestrator MUST:

1. Mark run status as `STALE_INPUTS`
2. Emit audit_event `late_evidence_received`
3. Block downstream stages until attorney chooses a rerun option

### 7.2 Attorney Rerun Options (ATTORNEY_ADMIN)
- **Partial Rerun:** Re-run mapping only (Stages 5+)
- **COA Remap:** Re-run taxonomy lock (Stage 4) + mapping (Stage 5+)
- **Full Regeneration:** Re-run from interview persistence onward (Stages 2+)

The selection must be recorded:
- in run_record (rerun_mode, rerun_reason, approval identity)
- as an audit_event `rerun_approved`

---

## 8. Break-Glass Override (SYSTEM_OVERRIDE)

**Lane:** `SYSTEM_OVERRIDE`  
**Role:** `ATTORNEY_ADMIN` only  
**Purpose:** Emergency intervention when normal workflow cannot proceed.

### 8.1 Allowed Break-Glass Actions
- Force a run state override (with explicit reason)
- Unlock a taxonomy (with explicit reason)
- Force a rerun (with explicit reason)

### 8.2 Mandatory Controls
- Requires `override_ticket_id`
- Requires `override_reason`
- Must emit audit_event with:
  - who initiated override
  - what was overridden
  - before/after state
  - timestamp

Break-glass is never used for normal approvals; it is an exception path only.

---

## 9. Acceptance Criteria (Semantic)

This orchestrator contract is valid when:

1. All referenced files exist and are non-empty.
2. Stages map to defined lanes (no “implicit permissions”).
3. Any denial path emits audit_event.
4. Rerun policy blocks downstream processing until attorney decision.
5. Shared knowledge promotion requires `attorney_signoff` and prohibits raw/identifying content.
6. Export requires explicit reason and produces an export_bundle artifact_ref and audit trail.
7. SYSTEM role remains empty (no content authority lanes) until execution wiring begins (tracked in semantic_debt).

---

## 10. Change Control

Changes to this document require:
- policy version bump per `policy_versioning.md`
- documentation of change rationale
- alignment check against `contract_manifest.yaml`

End of contract.