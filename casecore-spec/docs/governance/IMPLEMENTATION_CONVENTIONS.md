# /casecore-spec/docs/governance/IMPLEMENTATION_CONVENTIONS.md

# IMPLEMENTATION CONVENTIONS

## Purpose
Define coding and artifact conventions across CASECORE.

## Naming
- internal technical name: casecore
- APIs: lowercase paths
- events: dot.separated.lowercase
- files: lowercase-with-dashes where practical
- IDs: prefixed stable identifiers

## Logging
- include run_id where applicable
- include matter_id where applicable
- do not log sensitive payloads unnecessarily

## Contracts
- all schema changes must be versioned
- all workflow changes require traceability updates
- no implicit contract drift

## Rule
Implementation convenience may not override system clarity, auditability, or determinism.
