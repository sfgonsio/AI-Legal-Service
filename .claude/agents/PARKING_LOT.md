# PARKING LOT — AGENT SYSTEM ENHANCEMENTS

## Purpose
Capture ideas, requirements, and structural improvements that are not yet implemented but must be revisited.

## Rule
Any agent creation or modification MUST review this file and determine:
- if any item applies
- if it should now be implemented
- if it should remain parked

---

## CURRENT ITEMS

### Workflow / Design

- SUB_WORKFLOW_DESIGN  
  Add SIPOC and RACI model to skills and product requirements  
  Status: PENDING  
  Owner: TBD  

---

### Product Strategy Enhancements

- Introduce conditional SIPOC requirement for multi-agent workflows  
- Introduce RACI enforcement at execution layer  
- Ensure separation of strategy vs solution design responsibilities  

---

### Architecture / System

- Define formal Solution Design subagent (workflow + process modeling)
- Define execution planning agent or subagent (RACI ownership clarity)

---

### Data Governance

- Ensure all future UX and workflow designs explicitly represent:
  - canonical vs non-canonical data
  - data trust levels in UI
  - promotion pathways (non-canonical ? canonical)

---

### UX / Design Evolution

- Evaluate need for:
  - SUB_INFORMATION_ARCHITECTURE
  - SUB_INTERACTION_REVIEW
  - SUB_WORKFLOW_VALIDATION

---

## Notes

- Items in this file are NOT active requirements
- They must be consciously evaluated during agent design
- Nothing is implemented implicitly

### Case Guidance Expansion

- Consider future subagents under AGENT_CASE_GUIDANCE for specialized disciplines:
  - SUB_COA_MAPPER
  - SUB_BURDEN_ANALYZER
  - SUB_REMEDY_ANALYZER
  - SUB_FORENSIC_EVIDENCE_LITERACY
  - SUB_APPLIED_LITIGATION_PSYCHOLOGY

- Parent agent should not “train” subagents dynamically.
- Parent agent should define, scope, govern, and invoke subagents through explicit contracts.