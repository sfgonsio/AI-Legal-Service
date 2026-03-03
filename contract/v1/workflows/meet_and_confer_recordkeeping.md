# Meet & Confer Recordkeeping v1
**Layer:** Brain (Post-Spine Baseline v1.0-spine-stable)  
**Status:** Draft – Brain v1  
**Purpose:** Define a court-defensible record of discovery deficiencies and meet & confer efforts.

---

# 1. Why This Exists
Motions to Compel succeed or fail based on the record:
- What was requested
- What was produced (or not)
- What objections were raised
- Whether meet & confer was attempted in good faith
- Whether deadlines were honored

This workflow defines the “paper trail” structure required for court readiness.

---

# 2. Core Objects (Conceptual)
## 2.1 discovery_request
- request_id
- type: interrogatory | rfp | rfa
- served_date
- due_date
- text (or reference)
- mapped_to: coa_id/element_id OR objective tag

## 2.2 discovery_response
- request_id
- response_date
- response_text (or reference)
- objections (coded)
- production_refs (documents produced)
- completeness_score

## 2.3 deficiency_item
- deficiency_id
- request_id
- deficiency_type:
  - no_response
  - late_response
  - evasive
  - incomplete
  - improper_objection
  - privilege_claim_unsubstantiated
  - missing_documents
- materiality:
  - critical (COA element)
  - high (credibility/damages)
  - medium
  - low
- harm_statement (why it matters)
- supporting_citations (requests/responses + evidence_map)

## 2.4 meet_and_confer_event
- event_id
- date
- method: email | phone | letter | in_person
- participants
- agenda (linked deficiency_items)
- outcome:
  - resolved
  - partially_resolved
  - not_resolved
- commitments + deadlines
- artifacts: email pdf, letter, call memo

---

# 3. Workflow Sequence
1. Serve discovery (requests recorded)
2. Receive responses (responses recorded)
3. Generate deficiency matrix (deficiency_items)
4. Initiate meet & confer (event logged)
5. Capture outcomes and commitments
6. Re-evaluate deficiencies after deadline
7. If unresolved and material → MTC readiness evaluation

---

# 4. Court-Ready Standards
To qualify as “MTC-ready,” the record must include:
- served requests (with dates)
- responses (or proof of non-response)
- deficiency matrix (request → response → defect → harm)
- meet & confer attempts with artifacts
- follow-up deadlines and failure evidence

---

# 5. Audit Events
- discovery_request_recorded
- discovery_response_recorded
- deficiency_matrix_generated
- meet_and_confer_logged
- meet_and_confer_artifact_attached
- deficiency_reassessment_completed
- mtc_readiness_requested

---

# 6. Human Presentation Lens
This workflow turns chaos into a clean court narrative:
- “We asked for X on date Y.”
- “They responded with Z or refused.”
- “We met and conferred in good faith.”
- “The deficiency remains and prevents proof of element E.”
- “Here is the record to support compulsion.”