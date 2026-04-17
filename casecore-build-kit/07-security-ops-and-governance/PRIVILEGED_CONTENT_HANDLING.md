# /casecore-spec/docs/governance/PRIVILEGED_CONTENT_HANDLING.md

# PRIVILEGED CONTENT HANDLING

## Purpose
Define rules for privileged, work-product, and sensitive matter content.

## Rules
- Privileged/restricted artifacts must be flaggable.
- Access to flagged content must be role-controlled.
- Export of flagged content must be governed.
- LLM access to flagged content must be explicitly governed and not assumed.
- Logs must not unnecessarily expose sensitive payload content.

## Required Capabilities
- artifact restriction flags
- restricted-view UI states
- export restriction enforcement
- audit log of access where required

## Prohibited
- casual model access to privileged content
- unrestricted export of flagged artifacts
- silent downgrade of restricted flags
