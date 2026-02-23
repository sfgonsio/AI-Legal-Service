# Run Status Model (Contract v1)

Purpose:
Define the authoritative run lifecycle states and allowed transitions for all run types in the platform.

This file is SSOT for run status behavior.

------------------------------------------------------------

ALLOWED STATUSES

created
running
waiting
success
failed
denied
timeout
canceled

------------------------------------------------------------

TERMINAL STATUSES

success
failed
denied
timeout
canceled

Once a run reaches a terminal status it MUST NOT transition again.

------------------------------------------------------------

VALID TRANSITIONS

created → running
running → waiting
waiting → running
running → success
running → failed
running → denied
running → timeout
running → canceled
waiting → canceled

No other transitions are allowed.

------------------------------------------------------------

STATUS DEFINITIONS

created
Run record exists but execution not yet started.

running
Execution actively occurring.

waiting
Run paused awaiting external dependency or asynchronous result.

success
Execution completed successfully.

failed
Execution attempted but encountered runtime failure.

denied
Execution prevented by policy.

timeout
Execution exceeded allowed time.

canceled
Execution stopped intentionally by orchestrator or operator.

------------------------------------------------------------

RETRY RULE

Retries MUST create a new run_id.

A run may not transition from:
failed → running
timeout → running
denied → running

Retry must be represented as a new run.

------------------------------------------------------------

ORCHESTRATOR RULE

Orchestrator MUST determine next actions based on:

run status
error_code
retryable flag

It MUST NOT infer success or failure without reading run status.

------------------------------------------------------------

AUDIT REQUIREMENT

Every status transition MUST emit an audit event.

------------------------------------------------------------

INVALID STATE RULE

If an implementation attempts an undefined transition:

System MUST:

- reject the transition
- emit audit event
- mark run failed
- record error_code = INVALID_STATE_TRANSITION

------------------------------------------------------------

FAILURE DIAGNOSTIC REQUIREMENT

Any run entering a terminal failure state:

failed
denied
timeout

MUST include a diagnostic object as defined in:

contract/v1/tools/tool_gateway_contract.md

Implementations MUST NOT generate failure states without diagnostic metadata.


END OF SPEC