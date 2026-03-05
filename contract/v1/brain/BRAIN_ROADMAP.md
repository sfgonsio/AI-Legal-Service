# Brain Development Roadmap (Deferred / Future Work)

This document tracks architectural work intentionally deferred during Brain v1 development so it cannot be lost.

---

# 1. Citation & Provenance Contract

Define canonical identifiers for signal citations.

Planned file:
contract/v1/brain/citation_provenance_contract.md

Topics to define:
- doc_uid
- chunk_uid
- exhibit_id
- interview_turn_id
- artifact_uid
- run_id
- citation linking rules
- cross artifact references

Purpose:
Guarantee reproducibility and auditability across the system.

Status: Deferred until schema phase.

---

# 2. Case Signal Profile Schema

Planned file:
schemas/case_layer/case_signal_profile.schema.json

Purpose:
Canonical schema for all normalized case signals.

Dependencies:
case_signal_model.md

Status: Next architecture step.

---

# 3. Pattern Module Schema

Planned file:
schemas/pattern_modules/pattern_module.schema.json

Purpose:
Deterministic rule structure mapping signals → burden elements.

Status: Next architecture step.

---

# 4. Evidence Code Integration

Future artifact:
knowledge/evidence_code_catalog.yaml

Purpose:
Add evidence admissibility and foundation rules to the reasoning engine.

Status: Phase 2.

---

# 5. Cross-Case Knowledge Learning (DIKW)

Future work:
Create a governance framework for cross-case learning that promotes new pattern modules without allowing uncontrolled drift.

Possible location:
brain/memory_lobe/

Status: Phase 2 research.

---

# 6. Attorney Validation Workflow

Define the workflow where attorneys review:

- authority mappings
- pattern modules
- interview prompts
- coverage scoring

Status: Phase 2 governance.

---

End of roadmap.
