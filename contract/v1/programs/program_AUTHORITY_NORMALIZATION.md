# program_AUTHORITY_NORMALIZATION
(Authoritative Program Contract — v1 | Authority Pack Normalization Dispatcher)

## 1. Purpose

Normalizes any enabled authority pack into machine-reasonable legal structure.

Supported pattern:
Authority Pack -> Harvested Sections -> Normalization -> Litigation Reasoning

Initial supported pack:
- CA_BPC_DIV10_CANNABIS

Planned packs:
- CA_EVIDENCE_CODE
- CA_CACI
- additional governed legal-library materials

## 2. Inputs

- contract/v1/authority_packs/authority_pack_registry.yaml
- authority_packs/*/authority_pack_manifest.yaml
- pack-specific section artifacts

## 3. Outputs

- pack-specific normalized JSON artifacts
- optional consolidated normalization summaries

## 4. Determinism Rules

- every normalized artifact must retain authority_id
- every normalized rule must retain source_section
- pack manifests drive behavior, not hardcoded branching where avoidable
- malformed pack inputs must be logged, not silently ignored

## 5. Forward-Only Governance

This program must not rewrite or mutate historical downstream artifacts.
It produces new authority-derived outputs for supersession and impact analysis.

## 6. Versioning

Bound to contract_manifest.yaml
