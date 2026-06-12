# LEGAL_SPINE_DOCTRINE

## Scope

Defines the canonical-spine doctrine for the CaseCore legal library. Governs how legal authority relates to evidence, case facts, AI proposals, attorney strategy, and downstream analysis.

## Core principle

The **spine is canonical legal authority**.

Evidence is not the spine. Actors are not the spine. Timeline is not the spine. Triangulation is not the spine. AI proposals are not the spine. Attorney strategy is not the spine.

The entire case is viewed through the lens of legal authority.

## Direction of flow

```text
LEGAL LIBRARY / AUTHORITY PACKS
        ↓
CANONICAL SPINE
        ↓
Case-specific analysis
Evidence mapping
COA proposals
Burden mapping
Remedy mapping
Complaint drafting
War Room strategy
Attorney directives / interpretation overlays
AI proposals
```

## One-way boundary

```text
Canonical authority MAY flow outward into non-canonical analysis.

Non-canonical, commingled, inferred, evidence-derived, AI-generated,
attorney-strategy, timeline, actor, triangulation, or case-specific material
may NEVER flow back into canonical authority.
```

## Three-layer model

- **Layer 1 — Spine Index.** `contract/v1/knowledge/authority_catalog.yaml`. Holds authority IDs, titles, element structure, proof-type hints. Does not hold canonical text. Mutation requires explicit reconciliation approval.
- **Layer 2 — Canonical Authority Files.** `/legal/canonical/` (when populated). Holds official text, normalized text, citation, provenance, version, hashes, review state. Mutation requires the canonical promotion gate.
- **Layer 3 — Human-Readable Library.** Rendered downstream from Layer 2. Edited only by regenerating from Layer 2. Never an upstream source.

## Hard controls

- No drift.
- No hallucination.
- No fabrication.
- No evidence-driven mutation of law.
- No AI-created authority.
- No case facts modifying canonical law.
- Legal authority governs; evidence is mapped to the spine; AI proposes mappings; attorney approves case-specific use; canonical authority remains pristine.

## References

- `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` Sections 1, 1.A
- `contract/v1/doctrine/CANONICAL_PROMOTION_GATE.md`
- `contract/v1/doctrine/REJECTION_QUARANTINE_PROTOCOL.md`

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This doctrine document is authoritative for the legal-library program, but no agent may act on it for live ingestion, normalization, mutation, canonical promotion, or DB writes until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved.
