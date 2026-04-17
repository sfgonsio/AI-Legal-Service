# /casecore-spec/docs/governance/EVENT_BUS_AND_RETRY_MODEL.md

# EVENT BUS AND RETRY MODEL

## Purpose
Define async behavior and retry discipline.

## Rules
- retries must be bounded
- idempotency must be considered for material handlers
- failed async work must not silently disappear
- dead-letter or quarantine behavior must exist for repeated failure
- retry may not create duplicate canonical mutations
