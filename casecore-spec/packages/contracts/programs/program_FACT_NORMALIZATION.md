# /casecore-spec/packages/contracts/programs/program_FACT_NORMALIZATION.md

# PROGRAM CONTRACT — FACT_NORMALIZATION

## Purpose
Convert extracted/raw textual assertions into structured fact proposal artifacts.

## Type
Deterministic program

## Reads
- source document text
- source chunks
- matter context
- schema definitions
- taxonomy support where applicable

## Writes
- fact proposal artifacts conforming to proposal envelope rules
- provenance references
- processing metadata

## Does Not Write
- canonical facts directly
- legal conclusions
- approvals

## Required Rules
- provenance required
- schema-valid output required
- run_id required
- audit event required for material stage completion
