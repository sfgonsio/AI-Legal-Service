# /casecore-spec/validators/README.md

# CASECORE VALIDATOR LAYER

## Purpose
This directory contains local and CI-ready validation utilities for CASECORE contract enforcement.

## Scope
Current validator coverage includes:
- JSON schema parse validation
- schema/example instance validation
- explicit failure on invalid artifacts

## Rule
No builder may claim contract enforcement without running this validator layer successfully.

## Primary Files
- validate_json_artifact.py
- validate_schema_examples.ps1
- /examples/*.valid.json
