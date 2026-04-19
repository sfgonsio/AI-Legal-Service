# SKILL_NO_DRIFT_PATCHING

## Purpose
Force file-grounded, contract-bound, patch-only code generation with zero unauthorized drift.

## Applies To
- AGENT_CODE_ASSISTANT_AGENT
- SUB_BACKEND_BUILDER
- SUB_FRONTEND_BUILDER

## Mandatory Behavior

### 1. Read actual artifacts first
Never infer repository structure, fields, routes, or semantics.
Only build from provided files and approved contracts.

### 2. Validate before coding
Before code generation, produce:
- files validated
- confirmed model fields
- confirmed route pattern
- unresolved blockers

If a required artifact is missing, STOP.

### 3. Patch only
Modify only files explicitly listed in the active slice contract.
Do not rename, reorganize, modernize, or broadly refactor.

### 4. Respect truth ownership
Do not duplicate current-state ownership into audit/history artifacts.
Do not treat proposal artifacts as canonical.

### 5. Respect forbidden semantics
Never:
- introduce inferred legal state
- use deprecated scoring fields in new logic
- invent API flags not present in contract
- create new folders or routes unless explicitly approved

### 6. Return structured output
Always return:
1. Validation
2. Drift Check
3. Patch Plan
4. Code

### 7. Stop on ambiguity
If any required fact is missing, do not code.
List the exact missing artifact and why it blocks implementation.

## Drift Triggers
Reject your own output if it includes:
- invented fields
- invented tables
- invented routes
- out-of-scope file edits
- deprecated field reuse
- canonical/non-canonical leakage
- hidden coupling not allowed by contract

## Output Standard
Code must be:
- minimal
- directly mappable to actual files
- free of opportunistic cleanup
- aligned to existing repo pattern