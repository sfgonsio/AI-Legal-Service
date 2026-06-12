# GOVERNANCE_INDEX

## Purpose

Resolve governance precedence between the two governance documents that currently coexist in this repository:

- `contract/v1/knowledge/knowledge_contract.md` (Knowledge Contract v1 — Brain v1, Draft)
- The new legal-library scaffold doctrine, consisting of `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` plus the files under `contract/v1/doctrine/`

This index does not mutate either source. It states which document governs which subject and provides the explicit mappings needed to read both consistently.

## 1. Document scope

- `knowledge_contract.md` remains the **broader Brain v1 knowledge governance document.** It governs the full set of Brain-layer knowledge artifacts, including but not limited to legal authority. Its scope encompasses five object classes: `authority_text`, `case_summary`, `burden_map`, `heuristic_rule`, `practice_guide`.
- The **new legal-library scaffold doctrine** governs **canonical legal authority** (the `authority_text` class). Its scope is narrower than `knowledge_contract.md` but its rules are stricter and more specific within that scope. The scaffold doctrine comprises:
  - `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md`
  - `contract/v1/doctrine/LEGAL_SPINE_DOCTRINE.md`
  - `contract/v1/doctrine/LEGAL_SOURCE_HIERARCHY.md`
  - `contract/v1/doctrine/AUTHORITY_INTAKE_MANIFEST_SCHEMA.md`
  - `contract/v1/doctrine/AUTHORITY_PACK_FORMAT.md`
  - `contract/v1/doctrine/CANONICAL_PROMOTION_GATE.md`
  - `contract/v1/doctrine/REJECTION_QUARANTINE_PROTOCOL.md`
  - `contract/v1/doctrine/HUMAN_READABLE_LIBRARY_FORMAT.md`
  - `contract/v1/doctrine/RENDER_DB_AUTHORITY_MODEL.md`

## 2. Precedence for `authority_text` (canonical legal authority)

**For the `authority_text` knowledge object class, the new legal-library scaffold doctrine supersedes `knowledge_contract.md` Sections 3.1, 6, and 7.**

- `knowledge_contract.md` § 3.1 (object class definition for `authority_text`) is superseded by `AUTHORITY_PACK_FORMAT.md` for the canonical record shape, and by `AUTHORITY_INTAKE_MANIFEST_SCHEMA.md` for the per-item intake manifest.
- `knowledge_contract.md` § 6 (provenance requirements) is superseded for `authority_text` by the manifest schema's full provenance block (`source_name`, `source_url`, `source_accessed_at`, `effective_date`, `version`, `citation`, `provenance_hash`, etc.). The field-level mapping is in § 5 of this index.
- `knowledge_contract.md` § 7 (promotion gate) is superseded for `authority_text` by `CANONICAL_PROMOTION_GATE.md`, which defines 16 sub-gates and a human-signed promotion packet via `SKILL_PROMOTION_PACKET`.

For `authority_text` items, **all** of the following must hold (no gate may be bypassed):

- Source verification per `LEGAL_SOURCE_HIERARCHY.md`.
- Capture, normalization, judge review, attorney review, no-drift review, completeness scoring per the scaffold pipeline.
- Promotion packet assembled by `AGENT_CANONICAL_SPINE_GOVERNOR`.
- Human approval recorded in the promotion packet's signature block before any write to `/legal/canonical/`.

## 3. Precedence for non-`authority_text` knowledge artifacts and system-wide concerns

`knowledge_contract.md` **remains primary** for:

- The `case_summary` object class (attorney-reviewed case analysis).
- The `burden_map` object class (COA → element → required proof → jury-instruction linkage).
- The `heuristic_rule` object class (pattern-recognition guidance).
- The `practice_guide` object class (attorney-approved structured guidance).
- The **trust lifecycle** (`candidate` / `reviewed` / `trusted` / `deprecated`) as a broad Brain projection across all five classes. For `authority_text`, see the mapping in § 4.
- **Agent consumption rules** (`knowledge_contract.md` § 8): agents consume only `trusted` knowledge by default; OPPOSITION_AGENT defaults to trusted-only; optional override requires explicit declaration, audit logging, and run-id scoping. This applies to all knowledge classes including `authority_text`.
- **Replay integrity** (`knowledge_contract.md` § 9): version-pinned, trust-filtered, deterministically selectable. This applies to all knowledge classes including `authority_text`.
- **Broader Brain governance**: `knowledge_contract.md` § 10 (knowledge_objects / knowledge_promotions / knowledge_audit tables for non-authority classes), § 11 (governance boundary — no modification of `contract_manifest.yaml`, validator core, or overlay/config binding), § 12 (OPPOSITION_AGENT integration), § 13 (out-of-scope future expansion).

Within these sections, where the subject is the `authority_text` class specifically, defer to the scaffold doctrine. Where the subject is non-authority knowledge or a system-wide concern, `knowledge_contract.md` is the authoritative reference.

## 4. Trust-level ↔ scaffold review-state mapping

`knowledge_contract.md`'s 4-state trust lifecycle is a **derived projection** of the scaffold's per-record review state for `authority_text`. The mapping is:

| `knowledge_contract.md` trust_level | Scaffold equivalent for `authority_text` |
|---|---|
| `candidate` | `manifest.normalization_status ∈ {not_started, draft}`; `review.*` flags all `false`. Equivalent shorthand: **draft / unreviewed**. |
| `reviewed` | `manifest.judge_review_status = pass` AND `manifest.attorney_review_status = pass` AND `manifest.no_drift_review_status = pass` AND `manifest.canonical_promotion_decision = pending`. Equivalent shorthand: **judge + attorney + no-drift reviewed, pending promotion**. |
| `trusted` | `manifest.canonical_promotion_decision = approved` AND `review.canonical_promoted = true`. The canonical record is present in `/legal/canonical/` and the signed promotion packet is on file. Equivalent shorthand: **canonical promotion approved and applied**. |
| `deprecated` | The canonical record's `relationships.superseded_by` is populated AND a revocation event has been recorded. Equivalent shorthand: **superseded / deprecated authority or knowledge object**. |

For non-`authority_text` classes, `trust_level` retains its original meaning from `knowledge_contract.md` § 4 without translation.

## 5. Provenance-field mapping

`knowledge_contract.md` § 6 fields map to scaffold manifest / canonical fields as follows:

| `knowledge_contract.md` field | Scaffold field (manifest + canonical) |
|---|---|
| `source_identifier` | `source_name` + `source_url` (combined) |
| `original_citation` | `citation.official_citation` and `citation.short_citation` |
| `ingest_timestamp` | `source_accessed_at` (manifest) / `versioning.accessed_at` (canonical) |
| `content_hash` | `provenance_hash` (SHA-256 over captured bytes) |
| `jurisdiction` | `jurisdiction` as a nested object: `{country, state, county, city}`. The scaffold's nested form supersedes `knowledge_contract`'s flat string for `authority_text`. |
| `effective_date` | `effective_date` (semantically identical) |
| `trust_level` | derived from review-block flags and `canonical_promotion_decision`; see § 4 |

For non-`authority_text` classes, the `knowledge_contract.md` § 6 field shapes remain authoritative.

## 6. Known follow-up — `ingest_run_id` gap

`knowledge_contract.md` § 6 requires `ingest_run_id` on every knowledge object to satisfy the deterministic-replay guarantee in § 9. The scaffold's `AUTHORITY_INTAKE_MANIFEST_SCHEMA.md` does **not currently include** an `ingest_run_id` field. This is a known gap.

**Follow-up amendment to schedule:** add `ingest_run_id` to `AUTHORITY_INTAKE_MANIFEST_SCHEMA.md` (and a corresponding pass-through to the canonical record's `versioning` block) so that `authority_text` ingestion remains compatible with Brain v1's deterministic-replay contract. This is not done here; this index only records the gap.

Until that amendment is in place, any `authority_text` ingestion must record the `ingest_run_id` in the per-item `notes` field of the manifest (as a temporary measure) so the replay invariant is not silently broken.

## 7. Canonical spine doctrine — reaffirmation

The following rules apply across both governance documents and are not negotiable by either:

- **Legal authority is the spine.** The canonical spine is the authoritative legal authority of the platform. No other artifact carries that status.
- **Evidence is mapped to the spine.** Evidence, case facts, attorney strategy, timeline, actor, and triangulation material are mapped to the canonical spine for use; they are never substituted for it.
- **Canonical authority may flow outward.** Canonical authority informs case-specific analysis, COA proposals, burden mapping, remedy mapping, complaint drafting, War Room strategy, attorney directives, and AI proposals.
- **Non-canonical material may NEVER flow back into canonical authority.** No reverse flow. No evidence-driven mutation of law. No AI-invented authority. No case facts modifying canonical law. No attorney strategy or interpretation rewritten into the spine.

These rules are restated, not introduced, by this index. They are present in `LEGAL_SPINE_DOCTRINE.md`, `LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` § 1, and implicit in `knowledge_contract.md`'s § 1 design principles. Where any future amendment or implementation would weaken these rules, this index records that such an amendment is not authorized.

## 8. How to read both documents together

A reader encountering a question about a knowledge artifact should consult this index first to identify which document governs:

1. If the artifact is in the `authority_text` class (i.e., a canonical legal authority record):
   - Use the scaffold doctrine for record format (`AUTHORITY_PACK_FORMAT.md`), intake manifest (`AUTHORITY_INTAKE_MANIFEST_SCHEMA.md`), promotion gates (`CANONICAL_PROMOTION_GATE.md`), source hierarchy (`LEGAL_SOURCE_HIERARCHY.md`), and rendering (`HUMAN_READABLE_LIBRARY_FORMAT.md`).
   - Use `knowledge_contract.md` § 8 for agent consumption rules and § 9 for replay integrity.
2. If the artifact is in any of the other four classes (`case_summary`, `burden_map`, `heuristic_rule`, `practice_guide`):
   - Use `knowledge_contract.md` § 3.x for the class definition.
   - Use `knowledge_contract.md` §§ 6, 7 for provenance and promotion.
   - Use `knowledge_contract.md` §§ 8, 9, 10, 11, 12 for agent consumption, replay, data layer, governance boundary, and OPPOSITION_AGENT integration.
3. If the question concerns the database schema for legal authority storage, defer to `RENDER_DB_AUTHORITY_MODEL.md`. For non-authority knowledge classes, defer to `knowledge_contract.md` § 10's generic tables.

## 9. Stop conditions

This index is itself a doctrine document. It does not authorize ingestion, capture, normalization, canonical writes, catalog mutation, Render DB writes, agent execution, commits, or pushes. It records governance precedence only.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This governance index is authoritative for the legal-library program's relationship to broader Brain v1 governance, but no agent may act on it for live ingestion, normalization, mutation, canonical promotion, or DB writes until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` (defined in `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md`) is completed and approved.

Per the report you accepted on this branch, that gate is **cleared for INSPECT / REPORT mode only.** It is **not** cleared for ingestion, source capture, authority normalization, canonical file creation, catalog mutation, Render DB writes, promotion, commits, or pushes.
