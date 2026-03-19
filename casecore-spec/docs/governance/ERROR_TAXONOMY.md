# /casecore-spec/docs/governance/ERROR_TAXONOMY.md

# ERROR TAXONOMY

## Purpose
Define standardized error classes and required behavior.

## Error Classes
### Validation Errors
Examples:
- missing required field
- invalid enum
- malformed schema payload

Behavior:
- reject write
- log error with run_id
- do not silently coerce

### Workflow Errors
Examples:
- invalid state transition
- missing prerequisite stage
- promotion attempted before review

Behavior:
- halt transition
- log workflow event
- present explicit UI state

### Authorization Errors
Examples:
- unauthorized review action
- export attempted by restricted actor

Behavior:
- deny action
- log actor and attempted action

### Model Output Errors
Examples:
- schema-invalid proposal
- missing provenance
- unsupported proposal type

Behavior:
- reject proposal artifact
- quarantine output if needed
- log model metadata

### Data Integrity Errors
Examples:
- broken artifact lineage
- orphaned foreign reference
- conflicting canonical identity link

Behavior:
- block promotion or downstream use
- raise operational alert

## Rule
No service may suppress a material error that affects canonical state, approval state, provenance, or auditability.
