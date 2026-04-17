# /casecore-spec/validators/pipeline/PIPELINE_VALIDATION_RULES.md

# PIPELINE VALIDATION RULES

## Purpose
Define fail-fast validation requirements for CASECORE pipeline outputs.

## Rules
1. Every stage output must validate against a governed schema.
2. No invalid stage output may be promoted downstream.
3. Validation failure is a hard stop for that stage.
4. Stage outputs must include required identity and trace fields.
5. Proposal artifacts must remain proposal artifacts until governed promotion.

## Stage-to-Schema Mapping
- FACT_NORMALIZATION -> casecore.fact.schema.json
- TAGGING -> casecore.tag.schema.json
- COMPOSITE / EVENT MAPPING -> casecore.event.schema.json
- COA_ENGINE -> casecore.coa-element-coverage.schema.json
- AI proposal subsystem -> casecore.proposal-envelope.schema.json
