# program_AUTHORITY_BINDING
(Authoritative Program Contract — v1 | Authority Governance / Scope Binding Layer)

---

## 1. Purpose

AUTHORITY_BINDING is the universal governance layer that determines **which legal authority may be used, for what purpose, in which matter, and under what constraints**.

This program prevents legal drift by ensuring downstream workflows consume only:
- authority packs explicitly bound to the matter
- authority packs permitted for the requested reasoning mode
- authority records within approved topic, jurisdiction, and role boundaries

AUTHORITY_BINDING does **not** invent law, broaden scope, or substitute unbound authority.

It governs the lawful use of authority already harvested, normalized, and registered.

---

## 2. Architectural Position

AUTHORITY_BINDING sits between:

- authority pack ingestion / normalization / impact analysis
and
- downstream legal reasoning, evidence alignment, burden analysis, deposition support, trial preparation, and narrative generation

It serves as the **mandatory gate** for all authority-aware downstream programs.

No downstream program may consume legal authority directly without passing through AUTHORITY_BINDING or reading an artifact produced by it.

---

## 3. Inputs

Primary inputs may include:

- authority pack registry
- authority pack manifests
- normalized authority artifacts
- authority impact artifacts
- matter configuration / workspace configuration
- case scope declarations
- role / mode declarations for requested downstream task
- controlled vocabularies for authority roles and topic domains

Examples:
- contract/v1/authority_packs/authority_pack_registry.yaml
- authority_packs/<pack_id>/authority_pack_manifest.yaml
- casecore-runtime/data/law_normalized/*.json
- casecore-runtime/data/authority_impact/*.json
- matter-level binding configuration artifacts
- workspace-level scope declarations

---

## 4. Outputs

Primary outputs:

- AUTHORITY_BINDING_DECISION.json
- AUTHORITY_BINDING_SCOPE_MAP.json
- AUTHORITY_BINDING_AUDIT.json

Optional outputs:
- matter-specific authority activation records
- downstream-ready filtered authority lists
- stale/superseded authority warnings
- conflict escalation records

Outputs must be deterministic and reproducible from the same inputs and binding configuration.

---

## 5. Program Responsibilities

AUTHORITY_BINDING must:

1. determine which authority packs are active for a matter
2. classify active packs by legal role
3. enforce topic and jurisdiction scope
4. enforce allowed downstream usage by authority role
5. exclude unbound authority from downstream use
6. identify stale or superseded authority-derived artifacts
7. emit deterministic binding decisions and audit traces
8. prevent silent expansion of legal scope

---

## 6. Legal Authority Roles

Authority packs shall be classified into one or more of the following roles:

- substantive
- evidentiary
- instructional
- regulatory
- procedural
- reference_only

### Role meanings

**substantive**
Defines legal duties, prohibitions, conditions, exceptions, or rights relevant to the underlying matter.

**evidentiary**
Defines admissibility, burden mechanics, presumptions, witness rules, privileges, or evidentiary constraints.

**instructional**
Defines element framing, jury-facing standards, or instruction-level articulation.

**regulatory**
Defines agency or regulatory requirements, compliance rules, or administrative obligations.

**procedural**
Defines process constraints, sequencing, filing, timing, or court-process-related rules.

**reference_only**
May be surfaced for attorney review but may not drive deterministic downstream reasoning without explicit promotion.

---

## 7. Scope Dimensions

AUTHORITY_BINDING shall evaluate scope across these dimensions:

- jurisdiction
- authority type
- topic domain
- matter type
- workspace / task mode
- legal role
- supersession state
- permitted downstream usage

Examples:
- jurisdiction = CA
- topic_domain = cannabis
- authority_type = statute
- legal_role = substantive
- task_mode = deposition_preparation

---

## 8. Matter Binding Model

Each matter must declare, directly or indirectly:

- active authority packs
- inactive authority packs
- optional packs permitted only for limited uses
- topic scope
- jurisdiction scope
- permitted reasoning modes
- supersession policy

Example:
- CA_BPC_DIV10_CANNABIS → active, substantive
- CA_EVIDENCE_CODE → active, evidentiary only
- CA_CACI → inactive until admitted
- unrelated corporate or criminal packs → inactive

If a pack is not bound to the matter, it may not drive downstream outputs.

---

## 9. Core Invariants

### Invariant 1 — No Unbound Authority
No downstream artifact may use authority from a pack not explicitly bound to the matter.

### Invariant 2 — No Silent Scope Expansion
A downstream request may not silently broaden topic, jurisdiction, or authority role.

### Invariant 3 — Role Constrained Usage
Authority may only be used for the purposes permitted by its role and binding declaration.

### Invariant 4 — Forward-Only Supersession
New authority does not rewrite historical artifacts; it marks them stale, superseded, or rerun-required.

### Invariant 5 — Citation Traceability
Every downstream authority use must remain traceable to source section identifiers and binding decisions.

### Invariant 6 — Deterministic Decisioning
The same inputs and configuration must yield the same binding outputs.

---

## 10. Binding Decision Logic

AUTHORITY_BINDING shall determine whether an authority record is:

- ALLOWED
- ALLOWED_WITH_LIMITS
- BLOCKED
- BLOCKED_PENDING_REVIEW
- SUPERSEDED
- STALE_RERUN_REQUIRED

Decision logic must account for:

- whether the pack is active
- whether the authority role is permitted for the requested task
- whether the topic scope matches the matter
- whether a newer pack supersedes prior derived artifacts
- whether an attorney-review gate is required

---

## 11. Downstream Consumption Rules

AUTHORITY_BINDING shall enforce task-mode restrictions such as:

### deposition_preparation
May use:
- substantive authority bound to matter
- evidentiary authority bound to matter

May not use:
- unbound instructional or reference-only packs as legal drivers

### burden_mapping
May use:
- substantive
- evidentiary
- instructional (if active)

### trial_theme_workspace
May use:
- substantive
- evidentiary
- instructional
subject to explicit matter binding

### narrative_only
May surface reference_only materials only if clearly labeled non-authoritative

---

## 12. Supersession and Staleness

When a new authority pack is activated or an active pack changes:

AUTHORITY_BINDING must not rewrite prior derived artifacts.

Instead, it shall:
- identify affected downstream artifact classes
- mark them stale or superseded
- require rerun from authority binding forward where applicable
- preserve historical runs and auditability

Statuses may include:
- ACTIVE
- LEGACY
- SUPERSEDED_BY_AUTHORITY
- STALE_RERUN_REQUIRED

---

## 13. Conflict Handling

If two active authority packs conflict or appear to conflict:

AUTHORITY_BINDING must:
- record the conflict
- avoid silent selection unless priority rules explicitly resolve it
- emit BLOCKED_PENDING_REVIEW or explicit conflict warnings where necessary

Conflict resolution may consider:
- authority hierarchy
- jurisdiction
- recency
- explicit pack priority
- attorney override

---

## 14. Attorney Override Model

Attorney override may:
- activate a normally inactive pack
- restrict an otherwise active pack
- permit limited use of a pack for a specific task mode
- acknowledge and resolve a conflict

Overrides must be:
- explicit
- auditable
- scoped
- non-silent
- non-destructive to historical records

---

## 15. Audit Requirements

AUTHORITY_BINDING must emit an audit artifact that records:

- matter identifier
- task mode
- active packs considered
- excluded packs and reasons
- authority role decisions
- supersession findings
- conflicts identified
- override use, if any
- output decision hashes or references

This audit artifact is mandatory for downstream trust.

---

## 16. Failure Modes

AUTHORITY_BINDING must fail safely if:

- no authority packs are bound
- a required pack is missing
- normalized authority artifacts are missing
- scope declarations are ambiguous
- conflicting active packs cannot be resolved
- downstream request exceeds permitted authority role boundaries

Failure behavior must prefer BLOCKED or REVIEW_REQUIRED over silent permissive behavior.

---

## 17. Non-Goals

AUTHORITY_BINDING does not:
- harvest legal sources
- normalize raw statutory text
- determine factual truth
- perform evidentiary weighting
- generate persuasive narrative by itself
- silently admit new legal authority into a matter

---

## 18. Example Usage

### Cannabis matter
Matter scope:
- jurisdiction = CA
- topic_domain = cannabis

Active packs:
- CA_BPC_DIV10_CANNABIS (substantive)
- CA_EVIDENCE_CODE (evidentiary only)

Inactive packs:
- CA_CACI (until explicitly added)

Result:
- substantive duties must come from Cannabis pack
- evidentiary objections/burdens may come from Evidence Code
- no unrelated authority may drive deposition or burden outputs

---

## 19. Versioning and Governance

This contract is part of Contract v1.

Any change to:
- binding logic
- legal role definitions
- scope dimensions
- downstream permissions
- supersession behavior

must be treated as a contract-governed change and reviewed for architectural impact.

AUTHORITY_BINDING is a platform-level control program and must remain aligned with:
- authority pack registry
- workflow orchestration
- system index
- platform build index
- downstream legal reasoning programs

---
