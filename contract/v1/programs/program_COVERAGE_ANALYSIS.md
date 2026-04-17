# Program Contract: COVERAGE_ANALYSIS
**Version:** v1  
**Layer:** Brain  
**Type:** Deterministic Program  
**Status:** Brain v1  

---

# 1. Purpose
COVERAGE_ANALYSIS evaluates how well **structure signals** (case_signal_profile) cover the **structure target** (burden_map) and produces a machine-valid **coverage report** used by all agents to:
- ask better questions (INTERVIEW_AGENT)
- map evidence to elements (MAPPING_AGENT)
- find weaknesses (OPPOSITION_AGENT)
- guide research (RESEARCH_AGENT)
- generate discovery/motion readiness (DISCOVERY + M&C/MTC programs)

---

# 2. Inputs
- `case_signal_profile.json` (signals only)
- `burden_map.yaml` (authority-anchored elements + proof_types)
- optional: `evidence_map.json` (if already mapped; may be absent in early stage)
- run_id

---

# 3. Output
- `coverage_report.json` (must validate against `schemas/evaluation/coverage_report.schema.json`)

---

# 4. Core Concepts
## 4.1 Element Coverage Levels
- **covered_strong**: signals include specific facts/events tied to element + at least one proof_type indicated
- **covered_weak**: element appears only as conclusory allegation or missing specificity
- **not_covered**: no signals associated
- **unknown**: insufficient info to assess (rare; prefer not_covered)

## 4.2 Traceability
Every element assessment MUST include:
- `signal_citations` (JSON pointers into case_signal_profile)
- `notes` (brief; no legal conclusions)

---

# 5. Deterministic Scoring (v1)
Per element:
- covered_strong = 2
- covered_weak = 1
- not_covered = 0

Compute:
- `overall_score = sum(element_scores) / (2 * element_count)`
- element_count excludes “informational-only” elements if flagged in burden_map (future)

---

# 6. Gap & Next-Step Generation Rules
For each element:
- If covered_weak or not_covered:
  - Emit `missing_information_prompts` (fact questions)
  - Emit `requested_evidence_types` (from proof_types)
  - Emit `discovery_themes` (INT/RFP/DEPO labels, not drafted content)

No discovery drafting in this program—only themes and triggers.

---

# 7. Hard Constraints
Must not:
- invent facts
- infer intent, credibility, or legal conclusions
- cite sources not present in inputs
- generate motion language

---

# 8. Audit Events
- coverage_analysis_started
- coverage_report_emitted
- coverage_analysis_failed

---

# 9. Acceptance Test (Brain v1)
Given a burden_map with >=4 elements and a case_signal_profile:
- produce a coverage_report with per-element coverage classification
- produce overall_score
- include signal_citations for every element assessment
- validate against schema