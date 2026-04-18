# Execution Rules

- No UI change without Product Strategy Agent framing the work.
- No UI implementation without Design System Agent or approved UX direction.
- No legal-meaningful workflow change without Case Guidance Agent review.
- No code implementation without Code Assistant Agent routing to the proper builder.
- No repo action when repo root, branch, or working tree scope is unclear.
- No commit or push without release-gatekeeper verification.
- No skipped agent sequence when AgentOps Orchestrator identifies required gates.
- Keep the human operator in the approver role with directional input.
## Parking Lot Review Requirement

Before creating or modifying any agent or subagent:

- The builder MUST review:
  .claude/agents/PARKING_LOT.md

- The builder MUST:
  - identify relevant items
  - decide to implement, defer, or ignore
  - explicitly confirm review in output

Failure Condition:
- Any agent created without reviewing PARKING_LOT.md is INVALID
