# Program Contract: AUTHORITY_COVERAGE_CHECK
**Version:** v1  
**Layer:** Brain  
**Type:** Deterministic Program  
**Purpose:** Fail-fast validation that archetype references are present in the authority catalog.

---

# 1. Objective

Given:
- `taxonomies/pattern_packs/archetypes.yaml`
- `knowledge/authority_catalog.yaml`

Validate that:
- every `jury_instruction_ref` used by any archetype exists in `authority_catalog`.

This program prevents silent drift and ensures Burden Map Builder cannot reference missing authority.

---

# 2. Inputs

- `jurisdiction` (defaults to CA in v1)
- optional: `archetype_id` (if supplied, validate only that archetype; otherwise validate all)

---

# 3. Output

- On success: emit `authority_coverage_report.json` (optional artifact; v1 may log only)
- On failure: exit non-zero with precise missing keys

---

# 4. Deterministic Validation Rules

## 4.1 Validate Catalog Presence
- `authority_catalog.yaml` must contain top-level `authority_catalog:` mapping.

## 4.2 Validate Archetypes Inventory
- `archetypes.yaml` must contain top-level `archetypes:` list.
- Each archetype must include:
  - `archetype_id`
  - `jury_instruction_refs` (array, may be empty but discouraged)

## 4.3 Coverage Check
For each archetype in scope:
- For each `jury_instruction_ref`:
  - Must exist as a key under `authority_catalog:`.

Fail if any missing.

---

# 5. Failure Messaging (Required)

If missing references exist, fail with message:

`Missing authority_catalog entries: <comma-separated list>`

Example:
`Missing authority_catalog entries: CACI_304, CACI_4102`

---

# 6. Audit Events

- authority_coverage_check_started
- authority_coverage_check_passed
- authority_coverage_check_failed

---

# 7. Acceptance Criteria

- If all refs exist → pass
- If any ref missing → fail and list all missing refs
- Must not attempt to infer or “best match” missing refs