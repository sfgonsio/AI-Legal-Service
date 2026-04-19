# /casecore-runtime/packages/validators/README.md

# CASECORE RUNTIME VALIDATORS PACKAGE

## Purpose
Expose the authoritative CASECORE validation layers to runtime code.

## Scope
- schema example validation entrypoint
- pipeline validation entrypoint
- runtime enforcement entrypoint

## Rule
Runtime services must call this package rather than inventing local validation behavior.
