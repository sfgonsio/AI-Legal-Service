# contract/v1/tools/tool_gateway_contract.md
# Tool Gateway Contract (Contract v1)

Purpose:
Define deterministic rules governing all agent → tool execution across the AI Legal Service platform. This file is authoritative for tool invocation permissions, validation, auditing, and enforcement.

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

• validate caller identity  
• validate lane permission  
• validate tool authorization  
• validate required scope  
• enforce policy constraints  
• emit audit events  
• execute tool  
• record outputs  
• return response  

------------------------------------------------------------

EXECUTION PIPELINE (MANDATORY ORDER)

1. receive request  
2. verify agent identity  
3. verify run_id exists  
4. validate lane authorization  
5. validate tool permission  
6. validate required scope keys  
7. enforce prohibition rules  
8. emit audit event (start)  
9. execute tool  
10. capture output  
11. emit audit event (complete)  
12. return response  

If any step fails → execution MUST abort.

------------------------------------------------------------

TOOL CALL REQUEST FORMAT

Required fields:

agent_role  
run_id  
lane_id  
tool_name  
arguments  

Optional:

timeout_ms  
idempotency_key  

------------------------------------------------------------

TOOL RESPONSE FORMAT

status: success | failed | denied | timeout  
execution_time_ms  
output  
error_code  
error_message  
audit_event_id  

------------------------------------------------------------

AUTHORIZATION MODEL

Authorization is determined by:

roles.yaml  
lanes.yaml  

Gateway MUST verify:

Agent Role is allowed caller of Lane  
AND  
Lane permits tool_name  

------------------------------------------------------------

DENIAL CONDITIONS (MANDATORY)

Gateway MUST deny execution if:

• lane not allowed for role  
• tool not allowed in lane  
• required scope missing  
• prohibited action requested  
• run_id invalid  
• run status not active  
• policy versions mismatch  
• tool disabled  
• system safety lock engaged  

------------------------------------------------------------

AUDIT EMISSION RULES

Gateway MUST emit audit events:

tool_requested  
tool_allowed  
tool_denied  
tool_executed  
tool_failed  

Audit event MUST include:

- run_id  
- agent_role  
- lane_id  
- tool_name  
- arguments_hash  
- output_hash  
- policy_versions  
- timestamp_utc  

------------------------------------------------------------

IMMUTABILITY RULE

Tool outputs MUST NOT be modified by agents.

Any transformation must be recorded as:

derived_artifact

------------------------------------------------------------

TIMEOUT RULE

If tool exceeds timeout:

status = timeout

Gateway MUST:
- terminate execution
- emit audit event
- return failure response

------------------------------------------------------------

RETRY RULE

Retries are allowed ONLY if tool.idempotent == true

------------------------------------------------------------

SIDE EFFECT RULE

Tools that perform writes MUST:

- declare write targets
- be bound to write lanes
- emit write audit events

------------------------------------------------------------

TOOL REGISTRY REQUIREMENT

All tools MUST be registered in a Tool Registry.

Registry entry MUST define:

tool_name  
description  
idempotent  
timeout_default_ms  
allowed_lanes  
required_scope_keys  
prohibited_flags  
write_targets  

Unregistered tools MUST NOT execute.

------------------------------------------------------------

FAILURE HANDLING

If a tool crashes or errors:

Gateway MUST:

• record failure event  
• capture error payload  
• attach stack trace if available  
• mark run segment failed  
• return structured failure  

------------------------------------------------------------

SECURITY REQUIREMENT

Gateway MUST sanitize:

• arguments  
• file paths  
• command strings  
• URLs  

before execution.

------------------------------------------------------------

DETERMINISM RULE

Gateway execution MUST be:

• deterministic  
• reproducible  
• fully auditable  

------------------------------------------------------------

FUTURE EXTENSIONS (NON-BREAKING)

Future versions MAY add:

• signed tool manifests  
• external execution sandboxes  
• hardware isolation  
• execution attestation proofs  

------------------------------------------------------------

ADAPTER IMPLEMENTATION REQUIREMENT (v1)

Each registered tool MUST be implemented behind an adapter that supports:

- validate(arguments, scope) -> allow|deny with error_code
- execute(arguments, scope) -> output or error_code
- normalize(arguments) -> deterministic arguments_hash input
- classify_error(exception) -> standardized error_code, retryable flag

Standard error codes:
- TOOL_NOT_IMPLEMENTED
- TOOL_DENIED
- TOOL_INVALID_ARGUMENTS
- TOOL_TIMEOUT
- TOOL_DEPENDENCY_DOWN
- TOOL_INTERNAL_ERROR



END OF CONTRACT