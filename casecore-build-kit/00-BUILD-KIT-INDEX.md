# /casecore-build-kit/00-BUILD-KIT-INDEX.md

# CASECORE BUILD KIT INDEX

## Purpose
This directory is the builder-facing execution kit derived from `/casecore-spec`.

It is organized for engineering execution, not as the authoritative source of truth.

## Source of Truth Rule (Non-Negotiable)
- `/casecore-spec` is the ONLY authoritative source of truth
- `/casecore-build-kit` is a derived execution view
- builders must NOT treat build-kit files as the system-of-record
- all material changes must originate in `/casecore-spec`

## Start Here (Required Reading Order)

1. Read:
   - `/01-start-here/BUILD_SPEC.md`

2. Then read:
   - `/01-start-here/INTEGRATION_CONTRACT.md`
   - `/01-start-here/LOCKED_DECISIONS.md`
   - `/01-start-here/RESPONSIBILITY_MATRIX.md`

3. Then review core mechanics:
   - `/02-platform-core/ENGINEERING_OPERATING_MODEL.md`
   - `/02-platform-core/STATE_TRANSITION_MATRIX.md`
   - `/02-platform-core/state_transitions.yaml`
   - `/02-platform-core/contract_manifest.yaml`

4. Then implement in this order:
   - data and persistence → `/03-data-and-db`
   - contracts and workflows → `/04-workflows-and-contracts`
   - frontend → `/05-frontend`
   - AI proposal subsystem → `/06-ai-proposal-subsystem`
   - security/ops/governance hardening → `/07-security-ops-and-governance`

5. Then validate against:
   - `/08-fixtures-and-acceptance`
   - `/09-traceability-and-review`

## System Mental Model

CASECORE is a deterministic litigation platform built on:

- canonical artifacts
- governed workflows
- contract-driven interfaces
- bounded AI proposal generation
- human review and promotion controls
- traceability and auditability across every material transition

The core processing pattern is:

Input → Normalization → Tagging → Event/Composite Mapping → COA Mapping → Proposal Support → Review → Promotion

## Sections

### 01-start-here
Entry documents that define system intent, builder responsibilities, integration rules, and execution order.

### 02-platform-core
Core platform operating model, state mechanics, workflow rules, and manifest-level control.

### 03-data-and-db
Canonical data model, persistence design, entity relationships, indexing, and migration direction.

### 04-workflows-and-contracts
Schemas, APIs, events, enums, audit rules, deterministic program contracts, and taxonomies.

### 05-frontend
Frontend architecture, design system, truth-labeling rules, component inventory, and view-model constraints.

### 06-ai-proposal-subsystem
Bounded agent contracts, prompt catalog, model governance, and AI collaboration boundaries.

### 07-security-ops-and-governance
Security architecture, authorization, retry behavior, resiliency expectations, and non-functional requirements.

### 08-fixtures-and-acceptance
Fixture inputs, expected outputs, sample matter definitions, and milestone acceptance gates.

### 09-traceability-and-review
Traceability matrix, completeness review, integrated system review, and builder-derivation controls.

## Definition of Done

The system is considered correctly implemented when:

- contracts are implemented and enforced
- workflows follow governed state transitions
- canonical data conforms to defined schemas
- AI outputs remain proposals until governed promotion
- fixture inputs produce expected outputs
- traceability expectations are satisfied
- frontend truth-labeling preserves proposal/canonical distinction
- audit and provenance are preserved across material operations

## Final Rule

This build kit is for execution convenience.

If any file in this build kit conflicts with `/casecore-spec`, the authoritative source is `/casecore-spec`.
