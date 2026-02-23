# Tool Gateway Contract (Contract v1)

Purpose: Define the authoritative interface and runtime rules for mediated tool access. Agents MUST NOT call external tools directly; all tool interactions MUST be executed through the Tool Gateway under lane enforcement, audit logging, and deterministic version pinning.

Applies to:
- Run Records: `contract/v1/schemas/run_record.schema.yaml`
- Audit Events: `contract/v1/schemas/audit_event.schema.yaml`
- Policies: `contract/v1/policy/lanes.yaml`, `contract/v1/policy/roles.yaml`
- Run Lifecycle: `contract/v1/execution/run_lifecycle.md`

Non-Negotiable: Any direct tool access that bypasses the Tool Gateway is a Contract v1 defect.

---

## 1. Core Rules (Non-Negotiable)

1) Only the Tool Gateway may invoke tools (e.g., dictation, transcription, OCR, external APIs).
2) Every tool invocation MUST be governed by a lane (lane_id required).
3) Every tool invocation MUST emit an Audit Event (`action_type: tool_call`) regardless of success/deny/failure.
4) All tool calls MUST be pinned to:
   - `contract_version: v1`
   - `policy_versions.lanes` and `policy_versions.roles` (Git SHAs)
5) Tool requests and responses MUST be hashable:
   - `request_hash_sha256` required when any payload is provided
   - `response_hash_sha256` required when a response payload exists
6) Raw privileged content MUST NOT be embedded in audit events; store content as artifacts and reference via artifact_ref.

---

## 2. Tool Call Lifecycle (Canonical)

A tool call is executed as a child run:

- Parent: agent run (or orchestrator run)
- Child: tool_gateway run

State transitions (per Run Lifecycle):
created → running → completed | failed | denied | cancelled

---

## 3. Authorization and Lane Enforcement

Before invoking a tool, the Tool Gateway MUST validate:

- Caller identity (actor_type + actor_id)
- Caller role is permitted to initiate the lane (`allowed_callers.roles`)
- Lane permits the requested tool name in `allowed_actions.tools`
- Lane scope requirements are present (e.g., case_id, client_session_id, run_id)
- Lane prohibitions are enforced (e.g., prohibits cross_case_lookup, external_export)

If any check fails:
- Emit `authz_decision` audit event with outcome `deny`
- Emit `tool_call` audit event with outcome `deny`
- Return a standardized deny response (see Section 6)

---

## 4. Canonical Tool Call Request Shape (Runtime Contract)

The Tool Gateway MUST accept requests with these logical fields (implementation language may vary):

- tool_name (string)
- operation (string) e.g., transcription.run
- lane_id (string)
- actor (object: actor_type, actor_id, optional agent_name)
- case_id (nullable for system/global tools; usually required)
- run_id (string) - the tool_gateway run id
- parent_run_id (string)
- correlation_id (optional)
- input_artifacts[] (artifact_ref) - references to inputs (audio file, doc, prompt pack)
- parameters (object) - tool-specific parameters
- request_hash_sha256 (computed over normalized request payload)

Normalization rule (for hashing): stable key ordering, stable whitespace rules, exclude volatile timestamps.

---

## 5. Canonical Tool Call Response Shape (Runtime Contract)

The Tool Gateway MUST return:

- outcome: allow|deny|success|failure
- tool_name
- operation
- run_id
- correlation_id (if provided)
- output_artifacts[] (artifact_ref) - references to produced outputs (transcript, extracted text)
- response_hash_sha256 (computed over normalized response payload)
- error (nullable object: error_code, message bounded, retryable)

No raw privileged text should be returned inline if policy prohibits; store as artifact and reference.

---

## 6. Standardized Deny / Failure Responses

### 6.1 Deny (Policy)
- outcome: deny
- error_code: POLICY_DENIED
- message: bounded, non-sensitive reason (e.g., "lane prohibits requested tool")
- retryable: false

### 6.2 Failure (Runtime)
- outcome: failure
- error_code: TOOL_TIMEOUT | TOOL_ERROR | INVALID_REQUEST | DEPENDENCY_DOWN
- message: bounded; must not leak privileged payloads
- retryable: true|false depending on error_code

---

## 7. Required Audit Emissions (Tool Gateway)

For every tool call attempt (including deny):
- Emit `authz_decision` (allow/deny) at tool_gateway run start
- Emit `tool_call` event with:
  - actor, lane_id, tool/operation in target
  - request_hash_sha256
  - response_hash_sha256 (if response exists)
  - outcome + outcome_reason
  - timestamps

Tool payload content is referenced as artifacts (artifact_ref), not embedded.

---

## 8. Data Handling & Storage Rules

- Inputs and outputs MUST be persisted as artifacts in case-scoped storage by default.
- The Tool Gateway may request a db_write child run for persistence if needed.
- Cross-case access is prohibited unless a lane explicitly permits it (default: prohibited).
- Any export of tool outputs must be governed by an export lane and export run (default: prohibited).

---

## 9. Minimal Implementation Checklist (Antigravity Build Guide)

Implementation MUST:
- enforce lane tool allowlists
- enforce required scope fields and prohibitions
- create tool_gateway child runs for tool calls
- emit audit events for authz + tool_call
- compute request/response hashes
- store tool outputs as artifacts, referenced via artifact_ref
- deny on any missing policy/version pins

Any bypass of Tool Gateway or missing audit/hash/policy pins is a Contract v1 defect.

End.