# /casecore-runtime/packages/pipeline/README.md

# CASECORE RUNTIME PIPELINE PACKAGE

## Purpose
Provide executable pipeline stage shells aligned to CASECORE contracts and validator layers.

## Covered Stages
- FACT_NORMALIZATION
- TAGGING
- COMPOSITE_ENGINE
- COA_ENGINE

## Rule
Each stage must:
- accept explicit input
- produce explicit output
- validate output before downstream use
- avoid hidden side effects
