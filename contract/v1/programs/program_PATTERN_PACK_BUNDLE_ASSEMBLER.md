# Program Contract: PATTERN_PACK_BUNDLE_ASSEMBLER
**Version:** v1  
**Layer:** Brain  
**Type:** Deterministic Orchestrator Program  
**Purpose:** Assemble a complete, validation-ready Pattern Pack bundle from a complaint-derived signal profile.

---

# 1. Objective

Given:
- `case_signal_profile.json`
- `taxonomies/pattern_packs/archetypes.yaml`
- `knowledge/authority_catalog.yaml`
- deterministic program contracts:
  - `program_ARCHETYPE_PROPOSAL.md`
  - `program_AUTHORITY_COVERAGE_CHECK.md`
  - `program_BURDEN_MAP_BUILDER.md`
  - `program_COVERAGE_ANALYSIS.md`

Produce:
- a Pattern Pack bundle directory containing all intermediate and final artifacts plus a bundle manifest.

---

# 2. Inputs

Required:
- `run_id` (string)
- `jurisdiction` (default: CA)
- `case_signal_profile.json` (path)

Optional:
- `max_candidates` (default: 3)
- `selected_archetype_id` (if provided, skip archetype proposal and run only that archetype)
- `mode` (default: neutral_diagnostic)

---

# 3. Output Bundle Layout (Canonical)

`pattern_pack_bundles/<run_id>/`
- `case_signal_profile.json` (copied as input snapshot)
- `archetype_candidates.json` (unless selected_archetype_id provided)
- `authority_coverage_result.json` (pass/fail with missing refs list)
- `burden_map.yaml`
- `coverage_report.json`
- `bundle_manifest.json`

---

# 4. Deterministic Execution Steps

## Step A — Snapshot Inputs
Copy `case_signal_profile.json` into bundle folder as immutable run snapshot.

## Step B — Archetype Selection
If `selected_archetype_id` provided:
- set `archetype_id = selected_archetype_id`
Else:
- run ARCHETYPE_PROPOSAL producing `archetype_candidates.json`
- select top candidate as `archetype_id` for v1 bundle build
  - (Future: build multiple bundles per candidate)

## Step C — Authority Coverage Gate (Fail-Fast)
Run AUTHORITY_COVERAGE_CHECK in scope of selected archetype_id.
- If missing refs → abort bundle build.

Emit `authority_coverage_result.json` either way.

## Step D — Burden Map Build
Run BURDEN_MAP_BUILDER for archetype_id producing `burden_map.yaml`.

## Step E — Coverage Analysis (Grading)
Run COVERAGE_ANALYSIS with:
- case_signal_profile.json
- burden_map.yaml

Emit `coverage_report.json`.

## Step F — Manifest Emit
Emit `bundle_manifest.json` containing:
- run metadata
- artifact list + hashes
- selected archetype_id
- overall_score
- strict traceability pointers

---

# 5. Hard Constraints

- Must not invent facts
- Must not create advocacy content
- Must not draft discovery requests, motions, or arguments
- Must remain jurisdiction-bound (CA in v1)
- Must be reproducible (same inputs => same outputs)

---

# 6. Bundle Manifest Minimum Fields (v1)

- run_id
- jurisdiction
- mode
- archetype_id
- created_at
- artifacts[]: { path, sha256 }
- headline_metrics:
  - overall_score
  - weak_or_missing_elements_count

---

# 7. Audit Events

- bundle_assembly_started
- bundle_assembly_aborted_authority_missing
- bundle_assembly_completed
- bundle_manifest_emitted

---

# 8. Acceptance Criteria

Given a valid case_signal_profile and complete authority coverage:
- bundle folder is produced
- burden_map validates against schema
- coverage_report validates against schema
- manifest lists all artifacts with sha256