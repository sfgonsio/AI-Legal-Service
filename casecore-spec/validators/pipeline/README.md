# /casecore-spec/validators/pipeline/README.md

# CASECORE PIPELINE VALIDATION

## Purpose
Validate that pipeline-stage outputs conform to locked schemas and governed expectations.

## Covered Stages
- FACT_NORMALIZATION
- TAGGING
- COMPOSITE / EVENT MAPPING
- COA ENGINE
- AI PROPOSAL ENVELOPE

## Rule
A pipeline stage is not considered valid unless:
- output artifact validates against the required schema
- required metadata is present
- invalid artifacts cause failure, not silent continuation
