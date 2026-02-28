# contract/v1/harness/harness_contract.md
# Gate 5 (Option B): Deterministic Run + Audit JSON Harness (Contract v1)

AUTHORITATIVE STATUS
This document is a Contract v1 SSOT artifact.

Purpose
Provide a deterministic, implementation-independent harness that proves:
- run lifecycle semantics
- lane authorization semantics
- tool registry enforcement (enabled flag)
- audit emission ordering
- deterministic hashing for request/response objects

Scope
- No database required
- No external tool execution
- No network access
- Output is JSON artifacts only

Inputs
- tool request JSON (see sample_payloads/tool_request.json)
- policy artifacts referenced by contract_manifest.yaml:
  - policy/roles.yaml
  - policy/lanes.yaml
  - tools/tool_registry.yaml

Determinism Rules (MANDATORY)
1) Canonical JSON serialization:
   - UTF-8
   - no whitespace
   - sorted keys at all levels
2) Hashing:
   - sha256(hex) of canonical JSON bytes
3) Timestamps:
   - Harness accepts a fixed timestamp via CLI argument (--now_utc).
   - If omitted, harness uses current UTC; however, acceptance tests MUST provide --now_utc.
4) IDs:
   - Harness accepts run_id via CLI (--run_id).
   - If omitted, harness generates a deterministic run_id from request hash (RUN_<first12>).
   - Acceptance tests MUST provide --run_id for strict reproducibility.

Policy Enforcement (MANDATORY)
- Validate role exists in roles.yaml
- Validate lane exists in lanes.yaml
- Validate lane allows caller role
- Validate tool exists in tool_registry.yaml
- Validate tool is listed in lane.allowed_actions.tools
- Deny if tool enabled == false OR implementation_status != implemented

Audit Event Chain (MANDATORY ORDER)
The harness MUST emit audit_ledger events in the following order:

1) run_created        outcome: success
2) lane_authorized    outcome: success | denied
3) tool_requested     outcome: success
4) tool_allowed       outcome: success | denied
5) tool_denied OR tool_executed
6) run_completed      outcome: success | failed

For the default v1 setup (tools enabled:false), the expected path is:
- tool_allowed outcome: denied
- tool_denied emitted
- run_completed outcome: success (the run "completed with denial" deterministically)

Output Artifacts
Harness writes two JSON files to contract/v1/harness/outputs/:
1) run_record.json
2) audit_ledger.json  (array of audit events)

Acceptance Criteria
- Output JSON passes canonical determinism checks
- Event sequence matches the mandatory order
- All events include:
  - run_id, lane_id, role_id, tool_name (where applicable)
  - policy_versions_lanes, policy_versions_roles
  - request_hash_sha256, response_hash_sha256 where applicable
- When tool is disabled, denial reason is deterministic and structured
