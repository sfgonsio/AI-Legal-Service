# Program Contract: BURDEN_MAP_BUILDER
**Version:** v1  
**Layer:** Brain  
**Type:** Deterministic Program  
**Purpose:** Build an archetype-specific burden map from SSOT authority catalogs.

---

# 1. Objective

Given:
- `archetype_id`
- `taxonomies/pattern_packs/archetypes.yaml`
- `knowledge/authority_catalog.yaml`

Produce:
- `burden_map.yaml`

This program is deterministic and performs **no legal reasoning**.

---

# 2. Inputs

- `archetype_id` (string; must exist in archetypes.yaml)
- `jurisdiction` (defaults to CA in v1)
- `run_id` (string)

---

# 3. Output

- `burden_map.yaml`
- Must validate against: `schemas/pattern_packs/burden_map.schema.json`

---

# 4. Deterministic Build Rules

## 4.1 Archetype Lookup
- Find `archetype_id` in `archetypes.yaml`
- Read:
  - `coa_family`
  - `jury_instruction_refs[]`
  - `default_modules[]`
  - `conditional_modules[]`

Fail if not found.

## 4.2 Authority Expansion
For each `jury_instruction_ref`:
- Find matching entry in `authority_catalog.yaml`
- Expand into burden elements:
  - `element_id`
  - `proof_types[]`

Fail if any referenced instruction is missing from authority catalog.

## 4.3 Element Identity & De-duplication
If multiple instructions yield the same `element_id`:
- Merge proof_types (set union)
- Record all instruction refs in `authority_refs[]`

## 4.4 Output Ordering
- Preserve the order of `jury_instruction_refs` as listed in the archetype definition.
- Within an instruction, preserve element order as listed in authority_catalog.

---

# 5. Constraints

Must not:
- invent elements
- infer facts
- infer case-specific coverage
- alter proof_types beyond set-union merges

---

# 6. Audit Events

- burden_map_builder_started
- burden_map_emitted
- burden_map_builder_failed

---

# 7. Acceptance Criteria

Given:
- a valid `archetype_id`
- all referenced authority entries present

Then:
- burden_map.yaml is produced
- schema validation passes
- all elements have at least 1 proof_type