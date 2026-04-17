# program_LAW_NORMALIZATION
(Authoritative Program Contract — v1 | Legal Structuring Layer)

## Purpose
Transforms statutory authority into structured legal components:
- definitions
- obligations
- prohibitions
- conditions
- burden mapping

## Inputs
casecore-runtime/data/authority_store/*.json

## Outputs
casecore-runtime/data/law_normalized/LAW_NORMALIZED.json

## Rules
- Every output must trace to source_section
- No free-text interpretation
- Deterministic parsing required

## Extraction Triggers
Definitions: means, refers to, defined as
Obligations: shall, must, required to
Prohibitions: shall not, may not, unlawful
Conditions: if, unless, except

## Burden Mapping
- obligations → defendant
- prohibitions → plaintiff
- exceptions → shifting

## Execution
1. Load authority
2. Parse sections
3. Extract rules
4. Map burden
5. Write output

## Failure Modes
- Missing section_id → fail
- Empty text → skip
- Unparsed rule → log

## Versioning
Bound to contract_manifest.yaml
