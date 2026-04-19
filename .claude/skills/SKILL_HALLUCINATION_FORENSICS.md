# SKILL_HALLUCINATION_FORENSICS

## Mission
Detect unsupported claims, fabricated structure, or false certainty not grounded in provided artifacts.

## Detect
- assumed repository structure not present in files
- assumed DB tables or columns not present in models
- assumed runtime behavior not supported by main.py, routes, or database files
- unsupported claims about storage, APIs, or infrastructure
- fabricated explanations that present guesses as facts

## Required Checks
1. Every structural claim must map to provided file evidence
2. Every schema claim must map to actual models/schemas
3. Every route claim must map to actual route files
4. If evidence is missing, require STOP and explicit missing-artifact report

## Required Outcome
If unsupported claims are found:
- BLOCK before generation, or
- HALT after generation