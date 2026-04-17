# Program Contract: PATTERN_PACK_COMPILER
**Version:** v1  
**Layer:** Brain (Post-Spine Baseline v1.0-spine-stable)  
**Type:** Deterministic Program (Non-Agent)  
**Status:** Brain v1  

---

# 1. Purpose
PATTERN_PACK_COMPILER deterministically builds a **candidate Pattern Pack bundle** from case inputs (e.g., a complaint) using:

- structured extraction (“case signal profile”)
- curated/approved authority sources (jury instructions, evidence code, etc.)
- a reusable module library
- gap-driven discovery and evidence hygiene rules

It produces machine-validated artifacts for attorney review and promotion.

**Key Rule:** The compiler may use GPT as a drafting subroutine, but GPT outputs are treated as **untrusted candidates** until validated by this program and promoted by an attorney.

---

# 2. Inputs
## 2.1 Case Input
- complaint_pdf_path (or extracted text)
- jurisdiction (e.g., CA)
- posture (e.g., initial pleading, discovery, pre-motion)

## 2.2 Reference Inputs
- archetype taxonomy (allowed archetype_ids)
- pattern module library catalog (allowed module_ids + triggers + required_fields)
- approved_sources policy (allowed domains / corpora / tools)
- authority_text corpora (jury instructions, evidence code, statutes) as curated knowledge objects

## 2.3 Config
- max_archetypes_proposed (default: 3)
- strictness: strict | standard
- output_root (default: contract/v1/pattern_packs/_candidates)

---

# 3. Outputs
A candidate bundle directory with:

- `case_signal_profile.json` (deterministic extraction)
- `archetype_candidates.json` (ranked list with citations to signal fields)
- `burden_map.yaml`
- `module_activation.yaml` (default + conditional + element-to-module map)
- `evidence_hygiene.yaml`
- `discovery_triggers.yaml`
- `pattern_pack.yaml` (consolidated pack)
- `bundle_manifest.yaml` (inventory + hashes)
- `compiler_report.json` (validation results, warnings, blocked items)

All outputs must have:
- run_id
- created_at
- deterministic sort keys
- provenance pointers to inputs

---

# 4. Deterministic Pipeline Stages
## Stage 1 — Parse / Extract → Case Signal Profile (Deterministic)
Generate `case_signal_profile.json` with:
- parties/entities (names, roles)
- claimed events (dates, locations, actions)
- agreements mentioned (written/oral references)
- alleged harms/damages categories
- cited statutes/claims headings (if present)
- evidence mentions (emails, invoices, screenshots, contracts)
- procedural requests (injunction, fees, etc.)

No legal conclusions.

## Stage 2 — Archetype Proposal (Candidate; GPT Optional)
If GPT is used, it MUST output strictly structured JSON:
- archetype_id (from taxonomy)
- confidence (0–1)
- rationale (short)
- **signal_citations**: list of JSON pointers to fields in `case_signal_profile.json`

Program rejects:
- archetype_ids not in taxonomy
- missing signal citations
- fabricated frequency stats
- freeform outputs

## Stage 3 — Burden Map Build (Authority-anchored)
Build `burden_map.yaml` using curated authority_text objects:
- elements (id, name, plain)
- proof_types
- defenses_placeholders (unknown unless sourced)
- failure_modes_placeholders (heuristic label if not sourced)

GPT may summarize plain-language labels, but the element set is sourced.

## Stage 4 — Module Activation (Rule Engine)
Produce `module_activation.yaml`:
- default_modules (from archetype)
- conditional_modules (from triggers detected in signal profile)
- element_to_module_map (every element maps to >=1 module)

Reject if any element lacks module coverage.

## Stage 5 — Evidence Hygiene (Rules + Extensions)
Produce `evidence_hygiene.yaml`:
- universal hygiene rules (authentication, witness sourcing, privilege flags)
- archetype extensions
- rule triggers
- required fields + question clusters

## Stage 6 — Discovery Triggers (Gap Engine)
Produce `discovery_triggers.yaml`:
- minimum evidence set per element (by proof_types)
- gap conditions (missing/weak signals)
- recommended discovery themes (INT/RFP/DEPO objectives)
- meet & confer prerequisites
- MTC readiness gating hooks

## Stage 7 — Consolidate Pack + Bundle Manifest
Emit `pattern_pack.yaml` (references above) and `bundle_manifest.yaml` with SHA256 hashes.
Emit `compiler_report.json` with:
- pass/fail per stage
- warnings
- blocked items requiring attorney input

---

# 5. Validation Rules (Hard Fail)
Compiler must fail if:
- outputs violate schemas
- archetype_ids/modules not in allowed catalogs
- element_to_module mapping incomplete
- bundle_manifest missing or hash mismatch
- any stage produces un-cited assertions about the case input

---

# 6. Governance
PATTERN_PACK_COMPILER:
- does not provide legal advice
- does not file anything
- does not promote knowledge

Promotion requires attorney review (teacher gate).

---

# 7. Audit Events
- pattern_pack_compile_started
- case_signal_profile_emitted
- archetype_candidates_emitted
- burden_map_emitted
- module_activation_emitted
- evidence_hygiene_emitted
- discovery_triggers_emitted
- pattern_pack_bundle_emitted
- pattern_pack_compile_failed (if any stage fails)

---

# 8. Acceptance Tests (Brain v1)
Minimum acceptance:
- Given a complaint text, produce a candidate bundle that:
  - validates against schemas
  - includes >=1 archetype candidate (from taxonomy)
  - maps all burden elements to modules
  - emits discovery triggers and M&C/MTC gating hooks
  - produces bundle_manifest with hashes