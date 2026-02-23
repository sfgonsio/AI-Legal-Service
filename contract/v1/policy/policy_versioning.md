# Policy Versioning (Contract v1)

**Purpose:** Define deterministic, verifiable version identifiers for Contract v1 policy artifacts, used by Run Records, Audit Events, and Export Bundles.

## Authoritative Policy Files (v1)
- `contract/v1/policy/lanes.yaml`
- `contract/v1/policy/roles.yaml`

## Version Identifier (Required)
For Contract v1, **policy version identifiers are Git commit SHAs**.

- `policy_versions.lanes` MUST equal the Git commit SHA where `contract/v1/policy/lanes.yaml` was last modified.
- `policy_versions.roles` MUST equal the Git commit SHA where `contract/v1/policy/roles.yaml` was last modified.

These fields MUST be recorded on:
- Run Records (`policy_versions`)
- Audit Events (`policy_versions`)
- Export Bundles (`policy_versions`)

## How to Compute (Implementation Rule)
Compute the version SHA as the most recent commit that changed the file:

- Lanes:
  `git log -n 1 --pretty=format:%H -- contract/v1/policy/lanes.yaml`

- Roles:
  `git log -n 1 --pretty=format:%H -- contract/v1/policy/roles.yaml`

If the file has never been committed, it is **invalid for use** (no version pin).

## Drift / Validity Rule (Non-Negotiable)
If a derived artifact (run record, audit event, export bundle, or any generated visual/document) references policy versions that do not match the committed policy file SHAs, the artifact is **invalid** and MUST NOT be used for implementation, decision-making, or review.

## Future Upgrade (Optional)
A future contract version may replace Git SHAs with:
- a canonical content hash (e.g., SHA-256 over normalized YAML), and/or
- a signed policy release manifest.

Until Contract v2, **Git commit SHAs are the authoritative policy version pins**.
