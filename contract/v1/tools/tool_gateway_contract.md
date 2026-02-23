# contract/v1/tools/tool_gateway_contract.md
# Tool Gateway Contract (Contract v1)

Purpose:
Define deterministic rules governing all agent -> tool execution across the AI Legal Service platform. This file is authoritative for tool invocation permissions, validation, auditing, and enforcement.

------------------------------------------------------------

AUTHORITATIVE STATUS
This document is a Contract v1 SSOT artifact.

Tool execution MUST conform exactly to this specification.

If any implementation behavior conflicts with this contract,
THIS CONTRACT GOVERNS.

------------------------------------------------------------

CORE PRINCIPLE

Agents NEVER call tools directly.

All tool execution MUST flow through the Tool Gateway.

------------------------------------------------------------

TOOL GATEWAY RESPONSIBILITIES

The gateway MUST:

- validate caller identity
- verify run_id exists
- validate lane authorization
- validate tool authorization
- validate required scope keys
- enforce lane prohibition rules
- enforce tool prohibition flags
- emit audit events
- execute the tool via adapter
- record outputs (as artifacts when applicable)
- return a structured response

------------------------------------------------------------

EXECUTION PIPELINE (MANDATORY ORDER)

1. receive request
2. verify caller identity (role_id)
3. verify run_id exists
4. validate lane authorization (roles.yaml + lanes.yaml)
5. validate tool is registered (tool_registry.yaml)
6. validate lane permits tool_name (allowlist)
7. validate required scope keys
8. enforce prohibition rules (lane + tool)
9. emit audit event: tool_requested
10. execute tool via adapter
11. capture output and register derived artifacts (if any)
12. emit audit event: tool_executed | tool_failed | tool_denied | tool_timeout
13. return response

If any step fails -> execution MUST abort.

------------------------------------------------------------

TOOL CALL REQUEST FORMAT

Required fields:
- role_id
- run_id
- lane_id
- tool_name
- arguments
- scope

Optional fields:
- timeout_ms
- idempotency_key

Scope requirements:
- scope MUST include at minimum the keys required by the lane and tool (see lanes.yaml and tool_registry.yaml)
- scope MUST include case_id whenever the lane requires case_id

------------------------------------------------------------

TOOL RESPONSE FORMAT

- status: success | failed | denied | timeout
- execution_time_ms
- output
- error_code
- error_message
- audit_event_id
- diagnostic (required on failed/denied/timeout)

------------------------------------------------------------

AUTHORIZATION MODEL

Authorization is determined by:
- policy/roles.yaml
- policy/lanes.yaml
- tools/tool_registry.yaml

Gateway MUST verify:
1) Caller role is allowed for the lane
AND
2) The lane allows the tool_name
AND
3) The tool is registered and enabled
AND
4) Required scope keys are present
AND
5) No prohibition flags are violated

------------------------------------------------------------

DENIAL CONDITIONS (MANDATORY)

Gateway MUST deny execution if:
- lane not allowed for role
- tool not allowed in lane
- tool is unregistered or disabled
- required scope missing
- prohibited action requested
- run_id invalid
- run status not active / not in allowed state for this lane
- policy versions mismatch with run_record
- system safety lock engaged

------------------------------------------------------------

AUDIT EMISSION RULES

Gateway MUST emit audit events:
- tool_requested
- tool_allowed (optional but recommended)
- tool_denied
- tool_executed
- tool_failed
- tool_timeout

Audit event MUST include:
- run_id
- role_id
- lane_id
- tool_name
- arguments_hash_sha256
- output_hash_sha256 (when applicable)
- contract_version
- policy_versions (lanes + roles)
- timestamp_utc

------------------------------------------------------------

IMMUTABILITY RULE

Tool outputs MUST NOT be modified by agents.

Any transformation must be recorded as a derived artifact and linked through artifact_ref.

------------------------------------------------------------

TIMEOUT RULE

If tool exceeds timeout:
- status = timeout

Gateway MUST:
- terminate execution
- emit audit event: tool_timeout
- return a structured failure response

------------------------------------------------------------

RETRY RULE

Retries are allowed ONLY if tool.idempotent == true AND idempotency_key is provided.

------------------------------------------------------------

SIDE EFFECT RULE

Tools that perform writes MUST:
- declare write targets in tool_registry.yaml
- be bound to write lanes
- emit write audit events (either within tool_executed payload or as explicit write events)

------------------------------------------------------------

TOOL REGISTRY REQUIREMENT

All tools MUST be registered in tools/tool_registry.yaml.

Registry entry MUST define:
- tool_name
- description
- enabled
- idempotent
- timeout_default_ms
- allowed_lanes
- required_scope_keys
- prohibited_flags
- write_targets (if any)

Unregistered tools MUST NOT execute.

------------------------------------------------------------

FAILURE HANDLING

If a tool crashes or errors, Gateway MUST:
- record failure event
- capture error payload (bounded)
- attach stack trace if available (bounded / redacted)
- mark run segment failed (via run_record/audit)
- return structured failure

------------------------------------------------------------

SECURITY REQUIREMENT

Gateway MUST sanitize:
- arguments
- file paths
- command strings
- URLs
before execution.

------------------------------------------------------------

DETERMINISM RULE

Gateway execution MUST be:
- deterministic
- reproducible
- fully auditable

------------------------------------------------------------

ADAPTER IMPLEMENTATION REQUIREMENT (v1)

Each registered tool MUST be implemented behind an adapter that supports:
- validate(arguments, scope) -> allow|deny with error_code
- execute(arguments, scope) -> output or error_code
- normalize(arguments) -> deterministic arguments_hash input
- classify_error(exception) -> standardized error_code and retryable flag

Standard error codes:
- TOOL_NOT_IMPLEMENTED
- TOOL_DENIED
- TOOL_INVALID_ARGUMENTS
- TOOL_TIMEOUT
- TOOL_DEPENDENCY_DOWN
- TOOL_INTERNAL_ERROR

------------------------------------------------------------

DIAGNOSTIC BLOCK REQUIREMENT

Any failure, denial, or timeout response MUST include a diagnostic object with:
- error_code
- category
- message
- likely_cause
- suggested_fix
- retryable
- severity

This block MUST be structured and deterministic.
Implementations MUST NOT return unstructured error text.

END OF CONTRACT
