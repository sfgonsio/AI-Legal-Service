# /casecore-spec/docs/governance/CONFIG_GOVERNANCE.md

# CONFIG GOVERNANCE

## Purpose
Define what is configurable and how config changes are controlled.

## Configurable
- taxonomy values explicitly marked configurable
- model routing settings
- feature flags
- environment-specific infrastructure settings
- UI display defaults that do not alter legal semantics

## Not Freely Configurable
- canonical artifact definitions
- audit requirements
- approval requirements
- naming conventions
- truth-labeling rules
- core workflow control semantics

## Rule
Config may not be used to bypass governance, approval, traceability, or audit controls.
