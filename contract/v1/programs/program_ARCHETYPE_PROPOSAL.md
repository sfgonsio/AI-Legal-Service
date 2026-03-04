# Program Contract: ARCHETYPE_PROPOSAL
Version: v1
Layer: Brain
Type: Deterministic (GPT-constrained candidate stage)

---

# 1. Purpose

Given:
- case_signal_profile.json
- archetypes.yaml
- authority_catalog.yaml

Produce:
- archetype_candidates.json

---

# 2. Rules

GPT may be used to propose candidates BUT must:

- Select only archetype_ids defined in archetypes.yaml
- Provide signal_citations referencing case_signal_profile fields
- Assign confidence score (0-1)
- Provide short rationale (<300 chars)

Reject output if:
- Unknown archetype_id
- Missing signal_citations
- Claims outside extracted signals

---

# 3. Output Structure

[
  {
    "archetype_id": "string",
    "confidence": 0.0,
    "signal_citations": ["$.alleged_events[3]", "$.agreements"],
    "rationale": "string"
  }
]

---

# 4. Validation

Fail if:
- 0 candidates
- >3 candidates
- duplicate archetype_ids
- missing citation references