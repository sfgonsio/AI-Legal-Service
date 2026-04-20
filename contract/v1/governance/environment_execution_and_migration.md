# CASECORE — ENVIRONMENT EXECUTION + MIGRATION REQUIREMENT

## PURPOSE

This document defines the mandatory execution and migration standards for all environment-aware changes in CaseCore.

It ensures:
- proper runtime separation (sandbox, demo, live)
- safe deployment and updates across environments
- strict protection of live case data
- consistent, governed system evolution

This is a non-optional governance contract.

---

## RUNTIME MODEL (REQUIRED)

CaseCore operates as ONE codebase with THREE governed runtimes:

- sandbox
- demo
- live

All runtime behavior must be:

- configuration-driven
- centrally enforced
- consistent across frontend and backend

---

## REQUIRED FOR EVERY ENVIRONMENT CHANGE

Any change affecting runtime behavior MUST include ALL of the following:

### 1. Implementation

- Code changes (frontend and backend)
- Runtime-aware logic (no hardcoding)
- Centralized runtime capability model

---

### 2. Environment Wiring

Must explicitly define:

- how CASECORE_RUNTIME is used
- how environment variables differ per runtime
- how database connections differ per runtime
- how storage is isolated per runtime (if applicable)

---

### 3. Migration / Update Strategy

Must explicitly define:

- what is changing (schema, config, services, UI)
- which environments are impacted
- rollout order:

  1. sandbox
  2. demo
  3. live

---

### 4. Live Data Protection

Must explicitly confirm:

- no reset assumptions
- no destructive operations
- no mixing of live and non-live data
- backward compatibility where required

---

### 5. Separation of Concerns

The following MUST remain separate:

Concern | Description
--------|------------
Migration | Schema and structural changes
Scenario | Non-live seeded data
Demo Baseline | Controlled demo state

These must never be combined.

---

## REQUIRED OUTPUT FORMAT FROM CLAUDE

For every environment-related change, Claude MUST return:

1. Files changed
2. What was added
3. What was patched
4. Runtime wiring changes
5. Migration plan (sandbox → demo → live)
6. Live protection explanation
7. Validation steps per environment

---

## HARD RULES

The following are absolute:

- Live cannot be reset
- Live cannot be seeded
- Live cannot load scenarios
- Runtime must be configuration-driven (not inferred)
- Backend must enforce all runtime rules
- Frontend hiding is NOT sufficient protection

---

## LIVE DATA PROTECTION (CRITICAL)

Live runtime must protect:

- case records
- intake audio/video
- evidence files
- workflow state/history
- generated artifacts
- all persisted case data

Live must be treated as durable and non-recoverable via reset.

---

## FORBIDDEN PATTERNS

The following are strictly prohibited:

- shared database with runtime flag separation
- frontend-only environment gating
- hostname-only runtime detection
- hidden demo or seed endpoints accessible in live
- mixing migration logic with seed/scenario logic
- relying on reset to fix live data issues

---

## MIGRATION PRINCIPLES

- migrations are schema-only
- migrations are append-only and versioned
- migrations run in order: sandbox → demo → live
- migrations must preserve all live data
- migrations must not assume empty or resettable state

---

## FAILURE CONDITION

Any environment-related implementation is INVALID if it:

- lacks migration sequencing
- lacks runtime wiring
- risks live data integrity
- mixes migration and seeding logic
- bypasses backend runtime enforcement

Such implementations must be rejected and reworked.

---

## ENFORCEMENT

This file must be explicitly referenced in all environment-related implementation prompts.

Compliance is mandatory.
