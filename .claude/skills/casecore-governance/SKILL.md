---
name: casecore-governance
description: Use when work affects legal platform architecture, workflow, evidence handling, deployment boundaries, or repo placement.
---

# CASECORE Governance Checklist

Run this checklist before coding when a task touches architecture or governed behavior.

## Checklist
1. Confirm the real repo root.
2. Identify whether the request affects:
   - workflow/state
   - authority/traceability
   - intake/evidence/deposition
   - frontend/backend boundary
   - deployment target
3. Identify canonical vs proposal implications.
4. Identify smallest safe file set.
5. Identify required subagent review:
   - migration-manager when repo or branch risk exists
   - legal-architect
   - workflow-governor
6. Only after those pass, let a builder edit files.

## Output
- Scope
- Risks
- Required reviews
- Safe edit boundary