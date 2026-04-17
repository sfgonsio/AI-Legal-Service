# Discovery Workflows v1
**Layer:** Brain (Post-Spine Baseline v1.0-spine-stable)  
**Status:** Draft – Brain v1  
**Purpose:** Define procedural workflow sequencing for discovery actions and escalation.

---

# 1. Purpose
This document defines the platform’s discovery workflow patterns:
- Interrogatories (question-driven discovery)
- Requests for Production (document-driven discovery)
- Depositions (testimony-driven discovery)
- Meet & Confer (required escalation step)
- Motion to Compel (formal court escalation)

These workflows are governed, auditable, and case-context driven.

---

# 2. Workflow Principles
1. Discovery is driven by COA element gaps and evidentiary insufficiency.
2. Every discovery request theme must map to:
   - COA element(s), and/or
   - credibility/impeachment objective, and/or
   - damages computation objective.
3. Meet & Confer is a required gate before Motion to Compel.
4. Motion to Compel is a readiness artifact, not an auto-file action.
5. All steps must be audit logged and cite supporting case artifacts.

---

# 3. Interrogatories Workflow (Questions)
## 3.1 Trigger Conditions
- OPPOSITION_AGENT weakness_map identifies element gaps
- Evidence coverage below threshold for one or more elements
- Contradictions flagged in facts / testimony / documents

## 3.2 Outputs
- Interrogatory Themes (structured)
- Draft interrogatories (optional; attorney-reviewed)
- Mapping table: interrogatory → COA element → proof type
- Priority ranking and rationale

## 3.3 Success Criteria
- Each theme has explicit gap coverage objective
- Each interrogatory has citation to the gap evidence basis

---

# 4. Production Requests Workflow (Documents)
## 4.1 Trigger Conditions
- Missing documents inferred (e.g., contracts, invoices, logs)
- Damages proof missing
- Custody/possession facts unclear

## 4.2 Outputs
- RFP Themes
- Draft RFPs (optional)
- Custodian hypotheses
- Link to evidence gaps / timelines

---

# 5. Deposition Objectives Workflow
## 5.1 Trigger Conditions
- Witness credibility risk
- Contradictions present
- Key custody/intent elements require testimony

## 5.2 Outputs
- Deposition Objectives by witness
- Exhibits list (from evidence_map)
- “Must-lock” admissions list (by COA element)

---

# 6. Meet & Confer Workflow (Escalation Gate)
## 6.1 Trigger Conditions
- Inadequate responses
- Objections without substantiation
- Missing production deadlines
- Evasive interrogatory answers

## 6.2 Outputs
- Meet & Confer Agenda
- Issue list (each mapped to request + deficiency)
- Proposed resolution asks
- Deadline + follow-up plan
- Recordkeeping checklist (for later MTC support)

---

# 7. Motion to Compel Workflow
## 7.1 Trigger Conditions
- Meet & Confer attempted and documented
- Deficiencies persist beyond deadlines
- The missing items materially impact COA elements or defenses

## 7.2 Outputs (Readiness Packet)
- MTC Readiness Checklist
- Evidence of Meet & Confer (timeline + communications)
- Deficiency matrix: request → response → defect → harm
- Legal authority anchors (trusted authority_text only)
- Proposed exhibit list

**Note:** The platform does not file motions. It produces packets for attorney review.

---

# 8. Governance and Audit
All workflow runs must log:
- discovery_workflow_started
- discovery_packet_generated
- meet_and_confer_initiated
- meet_and_confer_completed
- motion_to_compel_packet_ready
- attorney_approval_required (for filing/serving)

---

# 9. Integration Points
- OPPOSITION_AGENT provides weakness_map and tactical priorities
- RESEARCH_AGENT/RESEARCH_CAPTURE may provide candidate authority (not binding)
- program_DISCOVERY_PACKET produces structured artifacts for attorney review