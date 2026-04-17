# /casecore-spec/validators/runtime/README.md

# CASECORE RUNTIME ENFORCEMENT

## Purpose
This directory contains runtime validation utilities used to enforce schema, state, and audit rules on actual program outputs and promotion requests.

## Scope
Current runtime checks include:
- artifact schema validation
- proposal envelope validation
- allowed state transition validation
- required audit record validation

## Rule
No program output or promotion request may be accepted without runtime enforcement passing.
