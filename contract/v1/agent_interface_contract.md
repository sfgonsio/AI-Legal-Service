# Agent Interface Contract (Contract v1)

Purpose: Define canonical agent interfaces (inputs/outputs), permitted lanes, allowed tool actions, and governed write points so Antigravity can implement agents with minimal ambiguity and low defect risk. This document is design-and-build instruction.

Authoritative dependencies:
- Policies:
  - `contract/v1/policy/roles.yaml`
  - `contract/v1/policy/lanes.yaml`
- Schemas:
  - `contract/v1/schemas/run_record.schema.yaml`
  - `contract/v1/schemas/audit_event.schema.yaml`
  - `contract/v1/schemas/artifact_ref.schema.yaml`
  - `contract/v1/schemas/export_bundle.schema.yaml`
- Execution:
  - `contract/v1/execution/run_lifecycle.md`

Non-Negotiable:
- Agents MUST operate only through governed runs and lanes.
- Agents MUST NOT directly call tools or write storage outside mediated runs (tool_gateway, db_write, promotion, export).
- All input/output artifacts MUST be referenced via `artifact_ref` (SSOT binding).
- Case isolation is default; cross-case access is prohibited unless explicitly permitted by lane.

---

## 1) Canonical Agent Run Pattern

Each agent executes as a run:
- run_kind: `agent`
- state transitions per `run_lifecycle.md`

Every agent run MUST:
- pin `contract_version: v1`
- pin `policy_versions.lanes` and `policy_versions.roles` at run start
- record `case_id` for case-scoped work
- record `inputs_artifacts_json` and `outputs_artifacts_json` as artifact_ref arrays
- emit required audit events:
  - authz_decision (allow/deny) at run start
  - terminal outcome event (completed/failed/denied/cancelled)
  - privileged action events via child runs (tool_gateway/db_write/promotion/export)

---

## 2) Canonical Agent Request / Response Shapes (Runtime Contract)

Implementation may vary by language, but the logical contract is fixed.

### 2.1 Agent Request (logical fields)
- agent_name (string) e.g., INTERVIEW_AGENT
- case_id (string)
- run_id (string) for the agent run
- parent_run_id (string) (orchestrator)
- root_run_id (string)
- correlation_id (optional)
- policy_versions (object: lanes, roles)
- taxonomy_versions (optional: coa, tags, entities)
- input_artifacts[] (artifact_ref array)
- parameters (object; agent-specific; must be hashable)
- request_hash_sha256 (required; normalized)

### 2.2 Agent Response (logical fields)
- outcome: success|deny|failure
- agent_name
- run_id
- output_artifacts[] (artifact_ref array)
- response_hash_sha256 (required if payload exists)
- error (nullable object: error_code, message bounded, retryable)

Hashing normalization: stable ordering, exclude volatile timestamps.

---

## 3) Canonical Agents (v1 Minimum Set)

Contract v1 defines these agents as the minimum implementation set:

1) ORCHESTRATOR (system-level)
2) INTAKE_AGENT
3) INTERVIEW_AGENT
4) MAPPING_AGENT
5) GOVERNANCE_AGENT (promotion gatekeeper)
6) EXPORT_AGENT (export bundling gatekeeper)

Antigravity MAY add agents later, but MUST define them here (or in an approved Contract update) before implementation.

---

## 4) Agent Specifications

### 4.1 ORCHESTRATOR (system)
Purpose:
- Top-level workflow coordinator for a case request.
- Creates child agent runs and correlates them via root_run_id/correlation_id.

Inputs:
- case_id
- initial intake artifact(s) (e.g., client form JSON artifact_ref)
- optional: uploaded document artifacts

Outputs:
- workflow summary artifact (artifact_ref)
- references to child run_ids (in metadata_json)

Allowed lanes:
- None directly. Orchestrator does not call tools or write domain tables directly.
- It may initiate child runs that do.

Required child runs:
- agent runs: INTAKE_AGENT, INTERVIEW_AGENT, MAPPING_AGENT, EXPORT_AGENT as needed

Audit:
- authz_decision at start (system allow/deny)
- run terminal event

Writes:
- Only to `runs` (run record) and audit via system channel

---

### 4.2 INTAKE_AGENT
Purpose:
- Evaluate initial client submission for completeness, basic triage, and routing to attorney review (accept/reject/needs-more-info).
- Generates an intake_summary artifact for human review.

Inputs (artifact_ref):
- client_intake_form (structured JSON)
- optional: initial uploads (documents, images)

Outputs (artifact_ref):
- intake_summary (bounded narrative + structured flags)
- intake_checklist (missing info list)
- optional: conflict_check_request (if implemented as artifact)

Allowed lanes:
- READ/ANALYZE only by default (no direct writes unless a lane permits).
- If persisting intake artifacts, must use WRITE_INTAKE_ARTIFACTS lane (via db_write child run).

Tool calls:
- None required in v1.

Writes (via db_write child run only if permitted):
- interview_notes (append) only if policy allows for intake stage
- entities (upsert) optional (e.g., basic name extraction)

Audit:
- authz_decision for agent run
- any db_write emits audit event
- run terminal event

Failure modes:
- POLICY_DENIED (deny)
- INVALID_INPUT (failure)
- DEPENDENCY_DOWN (failure, retryable)

---

### 4.3 INTERVIEW_AGENT
Purpose:
- Capture client narrative via dictation/transcription and structured interview prompts.
- Produce transcripts and structured interview notes.

Inputs (artifact_ref):
- client_session context artifact (session metadata)
- optional: prior intake_summary
- optional: prompt_pack artifact (governed prompts)

Outputs (artifact_ref):
- transcript artifact(s)
- interview_notes artifact(s)
- optional: extracted_entities artifact (early pass)

Allowed lanes:
- TOOL_INTERVIEW_CAPTURE (tool calls: dictation/transcription/interview prompts)
- WRITE_INTAKE_ARTIFACTS (persist transcripts/notes/entities)

Tool calls (must be via tool_gateway child run under lane TOOL_INTERVIEW_CAPTURE):
- dictation.start / dictation.stop (if used)
- transcription.run / transcription.status
- interview.prompt.next (if implemented as a tool)

Writes (must be via db_write child run under lane WRITE_INTAKE_ARTIFACTS):
- transcripts (append)
- interview_notes (append)
- entities (upsert)

Required scope fields (per lanes policy):
- case_id, client_session_id, run_id

Prohibitions:
- cross_case_lookup
- external_export
- shared_knowledge_write

Audit:
- authz_decision for agent run
- for each tool call: tool_gateway run + tool_call audit event
- for each write: db_write run + db_write audit event
- run terminal event

---

### 4.4 MAPPING_AGENT
Purpose:
- Assign evidence and extracted facts to Causes of Action (COA), complaints, and mapping structures.
- Produce COA maps, evidence maps, fact lists.

Inputs (artifact_ref):
- source documents (PDFs, emails, contracts)
- transcripts/interview_notes (optional)
- COA taxonomy snapshot or version pin (coa_version)
- optional: tagging taxonomy

Outputs (artifact_ref):
- facts artifact(s)
- evidence_map artifact(s)
- coa_map artifact(s)
- mapping_summary artifact (human-readable)

Allowed lanes:
- WRITE_MAPPING_OUTPUTS (persist facts/evidence_map/coa_map)
- Optional read lanes if implemented (db_read), but default is reading via artifact refs.

Tool calls:
- None required in v1 (may be internal LLM calls; if treated as tool, must go through tool_gateway).

Writes (must be via db_write child run under lane WRITE_MAPPING_OUTPUTS):
- facts (append)
- evidence_map (append)
- coa_map (append)

Required scope:
- case_id, run_id, coa_version

Prohibitions:
- shared_knowledge_write (unless promoted via promotion lane)
- cross_case_lookup

Audit:
- authz_decision for agent run
- db_write audit events for persistence
- run terminal event

---

### 4.5 GOVERNANCE_AGENT (Promotion Gatekeeper)
Purpose:
- Sanitize and promote insights from case plane into shared knowledge plane.
- Enforce prohibition on raw case text, identity, privileged notes.

Inputs (artifact_ref):
- promotion_ticket artifact (approval + scope)
- candidate insights artifact(s) (sanitized candidates)
- optional: redaction report artifact

Outputs (artifact_ref):
- promoted_shared_playbook artifact
- promoted_shared_heuristics artifact
- promotion_receipt artifact (human-auditable)

Allowed lanes:
- PROMOTE_SHARED_KNOWLEDGE only

Tool calls:
- Optional redaction/sanitization tooling; if used, must be via tool_gateway and lane must allow.

Writes (must be via db_write child run or promotion run under lane PROMOTE_SHARED_KNOWLEDGE):
- shared_playbooks (append)
- shared_heuristics (append)

Required scope:
- promotion_ticket_id, run_id
- No case_id required if purely shared; if derived from a case, record source case_id in bounded metadata (but do not store raw text).

Prohibitions (non-negotiable):
- raw_case_text
- client_identity
- privileged_notes

Audit:
- authz_decision for agent run
- promotion audit event with referenced artifacts
- run terminal event

---

### 4.6 EXPORT_AGENT (Export Bundling Gatekeeper)
Purpose:
- Produce export bundles for a case (discovery packages, attorney review bundles, audit-inclusive exports).

Inputs (artifact_ref):
- export_request artifact (scope, filters, redaction profile)
- selected artifacts (documents, transcripts, maps)
- optional: approvals artifact(s)

Outputs (artifact_ref):
- export_bundle artifact_ref (points to packaged object storage)
- export_manifest artifact (hashes, included items)
- export_receipt artifact

Allowed lanes:
- Export lane(s) as defined in lanes.yaml (if not yet defined, Antigravity must add an explicit EXPORT lane in policy before implementation).

Tool calls:
- packaging/compression tooling via tool_gateway (if treated as tool)
- optional: redaction tooling via tool_gateway

Writes:
- export_bundles table (append)
- audit_ledger entries (required)

Audit:
- authz_decision
- export audit event(s) (authorize, assemble, finalize)
- run terminal event

---

## 5) Lane-to-Agent Matrix (v1)

This matrix is authoritative for minimum enforcement. Implementation must deny actions outside this matrix.

- TOOL_INTERVIEW_CAPTURE:
  - allowed callers: INTERVIEW_AGENT
  - actions: dictation/transcription/interview prompts (per lanes.yaml)

- WRITE_INTAKE_ARTIFACTS:
  - allowed callers: INTERVIEW_AGENT, INTAKE_AGENT
  - actions: append transcripts/interview_notes; upsert entities

- WRITE_MAPPING_OUTPUTS:
  - allowed callers: MAPPING_AGENT
  - actions: append facts/evidence_map/coa_map

- PROMOTE_SHARED_KNOWLEDGE:
  - allowed callers: GOVERNANCE_AGENT, ATTORNEY_ADMIN
  - actions: append shared_playbooks/shared_heuristics

Export lane:
- REQUIRED before implementing EXPORT_AGENT writes/packaging in production.

---

## 6) Required Audit Coverage (Agent-Level)

Agents MUST:
- emit authz_decision at run start
- emit terminal outcome event
- ensure every tool call is audited (tool_gateway child run + tool_call audit event)
- ensure every write is audited (db_write child run + db_write audit event)
- record artifact references (inputs/outputs) per artifact_ref schema

Failure to produce these audit records is a Contract v1 defect.

---

## 7) Minimal Acceptance Tests (Antigravity)

Antigravity must demonstrate:
1) INTERVIEW_AGENT can capture transcription via tool_gateway with lane enforcement and audit logs.
2) INTERVIEW_AGENT can persist transcripts via db_write with lane enforcement and audit logs.
3) MAPPING_AGENT can write facts/evidence_map/coa_map via db_write with lane enforcement and audit logs.
4) GOVERNANCE_AGENT can promote sanitized insight only (raw case text prohibited) with audit logs.
5) Export produces export_bundle manifest + hashes and logs export audit events (once export lane is defined).

End.