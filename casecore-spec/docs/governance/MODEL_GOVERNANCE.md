# /casecore-spec/docs/governance/MODEL_GOVERNANCE.md

# MODEL GOVERNANCE

## Purpose
Define how LLM/model behavior is governed within CASECORE.

## Rules
- Models may generate proposals, not canonical truth.
- Prompted outputs must conform to typed schemas where defined.
- Model version and prompt version must be captured for proposal artifacts.
- Model changes require controlled review.
- Temperature and other generation parameters must be controlled by use case.

## Required Metadata
- provider
- model name
- prompt version
- run_id
- matter_id
- proposal type

## Prohibited
- freeform canonical writes
- hidden model substitution in production
- unlogged prompt changes
- provider/model drift without test revalidation
