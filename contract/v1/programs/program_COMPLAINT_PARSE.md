# Program Contract: COMPLAINT_PARSE
**Version:** v1  
**Layer:** Brain  
**Type:** Deterministic Program  
**Purpose:** Extract structured “case signals” from a complaint document.

---

## Authority Citation Gate (v1 amendment)

Complaint parse and downstream complaint mapping MUST NOT cite a CACI
unless its resolved authority meets one of:

- `certified.present == true` (a certified authority is available, e.g. statute or case law), OR
- `case_decision.state == ACCEPTED` with a non-null `pinned_record_id` (cited with a "based on provisional authority, attorney-accepted" footnote), OR
- `case_decision.state == REPLACED` (cite the replacement authority, not the original CACI)

CACIs with `effective_grounding ∈ {PROPOSED, NONE}` may be surfaced in the
attorney review queue but are blocked from pleading citation. Complaint
finalization is gated on all COA elements satisfying this rule.

All complaint citations MUST record `(decision_id, pinned_record_id)` for audit.

---

# 1. Objective

Given:
- complaint text (PDF → extracted text)
- jurisdiction

Produce:
- `case_signal_profile.json`

This program performs **no legal conclusions** and **no archetype inference**.
It extracts structured signals only.

---

# 2. Inputs

- complaint_text (plain text)
- jurisdiction
- run_id

---

# 3. Outputs

`case_signal_profile.json`

Must validate against:
`scripts/pattern_packs/case_signal_profile.schema.json`

---

# 4. Extraction Categories

## 4.1 Parties
- plaintiff_names
- defendant_names
- cross-complainant_names
- cross-defendant_names
- entity_types (individual, LLC, corp, unknown)

## 4.2 Alleged Events
Each event object must include:
- event_id
- approximate_date (if present)
- actors
- action_verb
- object
- location (if present)
- source_paragraph_ref

No interpretation. Use text-based references.

## 4.3 Agreements Mentioned
- written_contract_reference (yes/no)
- oral_agreement_reference (yes/no)
- contract_descriptions (short literal phrases)
- exhibit_references (if present)

## 4.4 Alleged Harms
- monetary_damage_reference
- injunctive_relief_reference
- attorney_fee_reference
- punitive_damage_reference

## 4.5 Causes of Action Headings
Extract literal headings.

## 4.6 Evidence Mentions
- emails
- invoices
- screenshots
- text messages
- contracts
- bank records
- other documentary references

## 4.7 Statutory References
Extract literal statute mentions if present.

---

# 5. Hard Constraints

Must not:
- infer archetype
- summarize intent
- infer legal conclusions
- reword allegations
- fabricate dates or amounts

All extracted values must tie to paragraph references.

---

# 6. Validation Rules

Fail if:
- missing required top-level keys
- event objects missing required fields
- paragraph references missing
- schema violation

---

# 7. Audit Events

- complaint_parse_started
- case_signal_profile_emitted
- complaint_parse_failed