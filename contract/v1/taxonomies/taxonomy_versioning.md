# Taxonomy Versioning (Contract v1)

Purpose: Define deterministic version identifiers for taxonomies used by the system.

Authoritative taxonomy sources:
- contract/v1/taxonomies/coa/
- contract/v1/taxonomies/tags/
- contract/v1/taxonomies/entities/

Version identifier rule:
Taxonomy versions MUST be the Git commit SHA where the taxonomy artifact was last modified.

These values MUST be recorded in:
- run_record.schema.yaml outputs
- audit_event.schema.yaml
- export_bundle.schema.yaml

Validity rule:
If a derived artifact references taxonomy versions that do not match repository state,
the artifact is invalid.

Future upgrade:
Contract v2 may replace Git SHAs with canonical content hashes.
Until then, Git commit SHAs are authoritative.
