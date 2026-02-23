# Run Lifecycle (Contract v1)

Purpose: Define the canonical lifecycle for a single platform execution "run" and its derived child runs (orchestrator → agent → tool gateway → writes/promotions/exports). This document is authoritative for runtime behavior and must align with Contract v1 schemas and policies.

Applies to:
- Run Records: `contract/v1/schemas/run_record.schema.yaml`
- Audit Events: `contract/v1/schemas/audit_event.schema.yaml`
- Artifact References: `contract/v1/schemas/artifact_ref.schema.yaml`
- Export Bundles: `contract/v1/schemas/export_bundle.schema.yaml`
- Policies: `contract/v1/policy/lanes.yaml`, `contract/v1/policy/roles.yaml`

Non-Negotiable: Contract v1 SSOT governs. Any implementation that deviates from this lifecycle is invalid.

---

## 1. Definitions

### 1.1 Run
A Run is the smallest unit of executed work that must be:
- uniquely identified (`run_id`)
- policy-pinned (`policy_versions`)
- contract-pinned (`contract_version`)
- auditable (audit events correlated to `run_id`)
- reproducible in intent (inputs/outputs as artifact references + hashes)

### 1.2 Run Record vs Audit Event
- Run Record: a summary/manifest of an execution (status, policy pins, artifacts in/out, timings).
- Audit Event: an append-only ledger entry for privileged actions (tool calls, writes, promotions, exports, authz decisions).

### 1.3 Artifact Reference Binding (SSOT)
All artifact references recorded in run/audit/export MUST conform to:
`contract/v1/schemas/artifact_ref.schema.yaml`

---

## 2. Run Kinds (Canonical)

Implementations MUST classify each run using `run_kind`:

- orchestrator
  Owns the top-level workflow and creates child runs.
- agent
  A single agent’s bounded execution in a governed lane.
- tool_gateway
  A mediated tool call run (the only allowed path to external tools).
- db_write
  A mediated persistence run (writes only; governed by lane).
- db_read
  A mediated read run (optional; governed by lane).
- promotion
  A governed run that promotes sanitized insights to shared knowledge.
- export
  A governed run that produces an Export Bundle.

Rule: Agents MUST NOT directly call tools or write storage outside a tool_gateway/db_write run mediated by the platform.

---

## 3. Run States (Canonical State Machine)

Runs MUST use the following states:

- created
  Run record initialized, not yet executing.
- running
  Execution started.
- completed
  Execution ended successfully.
- failed
  Execution ended with error.
- denied
  Execution blocked by authorization/policy.
- cancelled
  Execution intentionally stopped.

Allowed transitions:
- created → running | denied | cancelled
- running → completed | failed | denied | cancelled
- completed/failure/denied/cancelled are terminal.

Rule: Terminal states are immutable.

---

## 4. Determinism Pins (Required at Run Start)

At the moment a run enters `running`, the platform MUST pin:

- `contract_version` = v1
- `policy_versions.lanes` = Git SHA for `contract/v1/policy/lanes.yaml`
- `policy_versions.roles` = Git SHA for `contract/v1/policy/roles.yaml`

If any pin is missing, the run MUST be `denied`.

Optional pins (record if used):
- taxonomy_versions (coa/tags/entities) when mappings, tagging, or COA work is performed.

---

## 5. Lane Enforcement Points (Non-Negotiable)

Lanes govern “what can happen.” Enforcement occurs at three points:

### 5.1 Before any privileged action
Before a tool call, DB write, promotion, or export:
- Validate caller role (from roles policy)
- Validate lane allows caller role
- Validate lane allows action (tool names / write targets / promotion target)
- Validate required scope fields (e.g., case_id, run_id, coa_version)
- Validate prohibitions (e.g., cross_case_lookup, external_export, shared_knowledge_write)

If any check fails:
- Emit Audit Event: `authz_decision` outcome `deny`
- Set run state to `denied`
- Do not perform the action.

### 5.2 During action
- Tool calls must be mediated by tool_gateway
- Writes must be mediated by db_write
- Reads (if implemented) must be mediated by db_read
- Actions must be logged with request/response hashes (when applicable)

### 5.3 After action
- Record produced artifacts as artifact_ref entries
- Emit Audit Event for the action with correlation to `run_id` and `lane_id`
- Update run record outputs

---

## 6. Required Audit Events (Minimum Set)

For every run:
1) authz_decision (allow/deny) at run start
2) system event when state transitions to running
3) on terminal state: completed/failed/denied/cancelled with outcome_reason

For every privileged action within a run:
- tool_call audit event (for tool_gateway)
- db_write audit event (for persistence)
- promotion audit event (for shared knowledge)
- export audit event (for export bundle generation)

Audit events MUST include:
- event_id
- timestamp_utc
- action_type
- outcome
- actor
- contract_version
- policy_versions
- run_id
- (case_id if case scoped)
- (lane_id if lane scoped)

---

## 7. Run Trees and Correlation

### 7.1 Parent/Root Semantics
- `root_run_id`: the orchestration root.
- `parent_run_id`: immediate parent run (orchestrator → agent → tool_gateway → db_write).
- All child runs inherit:
  - contract_version
  - policy_versions
  - case_id (if case scoped)
unless explicitly denied by policy.

### 7.2 Correlation IDs
If a user request spans multiple runs, emit a `correlation_id` shared across the set.

---

## 8. Inputs/Outputs Recording Rules

### 8.1 Inputs
Inputs MUST be recorded as references, not embedded privileged content:
- artifact_refs for documents, transcripts, prompt packs, configs
- request hashes for tool calls (normalized)

### 8.2 Outputs
Outputs MUST be recorded as artifact_refs:
- transcripts
- extracted entities
- fact statements
- evidence maps
- COA maps
- export bundles

Rule: Raw privileged text MUST NOT be embedded in run/audit/export manifests unless a lane explicitly allows it (default: prohibited).

---

## 9. Failure and Retry Rules

### 9.1 Failures
When a run fails:
- Set state to failed
- Emit audit event with error_code, message (bounded), retryable flag
- Record partial outputs as artifacts only if policy permits

### 9.2 Retries
If retryable:
- Create a NEW run_id for each retry
- Set parent_run_id to the original run_id
- Preserve root_run_id
- Record retry_count and retry_reason in run record metadata (if present)

Rule: No “in-place” retries that mutate an existing run record.

---

## 10. Promotion and Export Gates (High-Risk Controls)

### 10.1 Promotion to Shared Knowledge
Promotion runs MUST:
- require promotion_ticket_id
- be restricted to GOVERNANCE_AGENT or ATTORNEY_ADMIN roles per lanes policy
- prohibit raw_case_text, client_identity, privileged_notes
- emit audit event with outcome and references to sanitized artifacts

### 10.2 Export Bundles
Export runs MUST:
- be restricted to authorized roles (typically ATTORNEY_ADMIN)
- produce `export_bundle` artifact_ref
- include bundle integrity hashes
- record approvals (if required by firm policy)
- emit audit events for:
  - export authorization decision
  - bundle assembly
  - completion/failure

---

## 11. Minimal Implementation Checklist (Antigravity Build Guide)

Implementation MUST:
- enforce run state transitions exactly as defined
- enforce lanes.yaml and roles.yaml before any privileged action
- produce run records and audit events with pinned versions
- ensure all artifacts are referenced via artifact_ref schema
- prohibit cross-case reads/writes unless a lane explicitly allows it
- prohibit shared knowledge writes unless a promotion lane explicitly allows it
- treat audit ledger as append-only (no mutation)

Any deviation is a Contract v1 defect.

End.
