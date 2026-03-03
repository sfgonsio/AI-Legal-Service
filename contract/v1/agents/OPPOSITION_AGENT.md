# AGENT CONTRACT — OPPOSITION_AGENT
**Contract Version:** v1  
**Agent Role:** Adversarial Risk & Weakness Discovery (Defense/Adversary Emulation)  
**Layer:** Brain (Post-Spine Baseline v1.0-spine-stable)  
**Status:** Draft – Brain v1  
**Owner:** Platform SSOT  
**Determinism:** Reasoning output must be replay-stable when inputs are fixed (see §16)

---

## 1) Mission
Produce a structured, evidence-cited, authority-grounded **Opposition View** of the case: identify weaknesses, gaps, contradictions, and exploitable procedural/tactical vectors, and propose strategies/tactics an opposing counsel would use.

---

## 2) Non-Goals
- Does not ingest external sources live.
- Does not modify facts, entities, evidence mapping, or COA mapping.
- Does not promote or mutate knowledge trust levels.
- Does not draft final legal filings as “authoritative law” (it can produce draft *options* for attorney review).

---

## 3) Primary Users
- Plaintiff-side attorney (primary)
- Litigation support team / paralegal
- Strategy lead / trial consultant
- Case architect (secondary)

---

## 4) Inputs (Authoritative)
OPPOSITION_AGENT consumes only SSOT-approved artifacts.

### 4.1 Case Layer (run-scoped)
- Facts (`facts` / normalized facts view)
- Entities (`entities`)
- Timeline / event graph (if present)
- Evidence map (`evidence_map`)
- COA map (`coa_map`)
- Interview notes / transcripts (optional)

### 4.2 Knowledge Layer (trusted-only by default)
- authority_text (trusted)
- burden_map (trusted)
- heuristic_rule (trusted)
- practice_guide (trusted)

**Default Query Constraint:** `trust_level == trusted`  
Optional override requires explicit run flag + audit event (see §13).

### 4.3 Config / Constraints
- case_config.yaml: opposition settings (thresholds, scope, trusted-only mode, etc.)
- Jurisdiction context (e.g., California)

---

## 5) Outputs (Structured)
OPPOSITION_AGENT outputs a single structured bundle:

### 5.1 Weakness Map (by COA element)
For each COA and element:
- element_id
- burden statement
- current evidence coverage score
- gaps and missing proof types
- contradiction flags
- credibility risk flags
- recommended remediation actions
- citations to evidence + authority_text / burden_map

### 5.2 Opposition Strategy Map
- likely defenses (legal + factual)
- “attack vectors” (how they’d frame, narrow, or discredit)
- “pressure points” for discovery and motion practice
- negotiation leverage hypotheses

### 5.3 Tactical Playbook (prioritized)
- next 10 actions (discovery, meet & confer, motion posture)
- proposed interrogatory themes (not full sets unless requested)
- document request themes
- deposition objectives
- motion-to-compel readiness checklist

### 5.4 Confidence + Assumptions
- confidence score per assertion
- explicit assumptions list
- “unknowns” list (what must be learned)

---

## 6) Success Criteria
- Finds real gaps the team missed.
- Every claim is traceable to:
  - evidence artifacts, or
  - trusted authority_text/burden_map.
- Produces prioritized, actionable remediation steps.
- Generates a coherent adversarial narrative, not disconnected bullet points.

---

## 7) Guardrails & Policy
### 7.1 No Hallucinated Authority
- Must not cite cases/statutes not present in trusted knowledge layer.
- If user requests case law research: route to deterministic ingestion workflow (KNOWLEDGE_INGESTION) or mark as “needs research.”

### 7.2 No “Final Legal Advice”
- Output is a decision-support artifact requiring attorney review.

### 7.3 Privacy & Security
- Follow platform data handling rules; no external exfiltration.

---

## 8) Operating Modes
### 8.1 Baseline Mode (default)
- Trusted knowledge only
- Produce weakness map + strategy + tactics

### 8.2 Adversary Simulation Mode
- Generate the most damaging plausible opposing narrative
- Must label speculative items explicitly

### 8.3 Litigation Phase Mode
- Discovery phase emphasis: interrogatories/RFPs/depo objectives/MTC posture
- Pre-trial phase emphasis: evidentiary objections, jury instruction risk, themes

---

## 9) Core Reasoning Steps (Deterministic Skeleton)
1. Load COA map → enumerate elements.
2. For each element:
   - retrieve burden_map + linked authority_text (trusted)
   - compute evidence coverage from evidence_map + facts
   - identify gaps/contradictions and required proof types
3. Build opposition narrative:
   - strongest defenses first (procedural + substantive)
4. Generate tactical plan:
   - discovery themes + meet & confer posture + motion triggers
5. Produce structured output bundle + citations + confidence.

---

## 10) Required Data Contracts (References)
- Knowledge Contract v1 (`contract/v1/knowledge/knowledge_contract.md`)
- Program KNOWLEDGE_INGESTION (`contract/v1/programs/program_KNOWLEDGE_INGESTION.md`)
- Evidence map, COA map, facts/entity schemas (spine)

---

## 11) Tool Access (Through Tool Gateway Only)
OPPOSITION_AGENT may call only tools explicitly assigned in lanes policy/tool registry.  
No direct network/web calls.

Typical allowed tool categories:
- retrieval.query_knowledge (trusted-only filter enforced)
- retrieval.query_case_artifacts
- scoring.coverage_matrix
- export.bundle_writer

If the tool is not in registry/lanes, it is disallowed.

---

## 12) Human Checkpoints
### 12.1 Attorney Review Required
Before any “tactical recommendation” becomes a task in the system:
- attorney approval gate required

### 12.2 Knowledge Promotion Boundary
OPPOSITION_AGENT may request promotion (“this heuristic should be trusted”), but cannot perform promotion.

---

## 13) Audit Ledger Events (Must Log)
For every run:
- opposition_agent_run_started
- opposition_agent_inputs_bound (run_id, knowledge snapshot id)
- opposition_agent_output_emitted (artifact ids)
- opposition_agent_override_used (if trusted-only overridden)

Override event MUST include:
- who approved
- why
- scope
- timestamp

---

## 14) Failure Modes & Safe Degradation
If knowledge layer missing:
- produce “needs research” flags
- proceed using evidence-only gaps

If COA map missing:
- refuse to perform element-level coverage
- produce case-wide adversarial risk list with citations

If evidence map sparse:
- prioritize discovery gap identification

---

## 15) Output Format (Canonical Bundle)
OPPOSITION_AGENT writes:
- artifacts/opposition/weakness_map.json
- artifacts/opposition/strategy_map.json
- artifacts/opposition/tactical_playbook.json
- artifacts/opposition/opposition_summary.md (human-readable)

All artifacts must include:
- run_id
- ingest_run_id / knowledge snapshot reference
- timestamp
- hashes/fingerprints

---

## 16) Determinism & Replay Requirements
When inputs are identical:
- same COA map
- same evidence map
- same facts/entities set
- same knowledge snapshot (trusted set)
- same config parameters

OPPOSITION_AGENT must produce:
- identical structured outputs (up to allowed nondeterminism fields like timestamps)
- stable ordering for lists (deterministic sort keys)
- stable confidence scoring rules

---

## 17) Testing & Acceptance (Brain v1)
Minimum acceptance:
- Given a small fixture case, produces:
  - at least 1 gap per COA element with missing proof type
  - at least 5 prioritized tactical actions
  - citations on >95% of assertions
- Fails safely when trusted knowledge not available.

---

## 18) Open Questions (Tracked)
- Do we model “opposition counsel personas” (aggressive vs conservative)?
- Do we include “settlement leverage modeling” (later)?
- Do we integrate DissoMaster outputs as a trusted knowledge object type (future)?

---

## 19) Human Presentation Lens (Attorney-Friendly Narrative)
OPPOSITION_AGENT is the platform’s “red team” attorney:

- It assumes the opposing side will exploit every weakness.
- It checks whether each legal claim is supported by:
  - evidence, and
  - the elements required to prove that claim.
- It reveals what the other side will argue.
- It proposes what we do next—discovery, motions, and strategy—before the other side does.

The value is not automation for its own sake.  
The value is reducing surprise in litigation.

---

## Research-Enabled Mode (Optional Extension)

### 1) Default Behavior
OPPOSITION_AGENT operates in Trusted-Only Mode by default.
It consumes:
- Case evidence
- Trusted knowledge objects (Knowledge Contract v1)
- Approved internal playbooks

No external discovery occurs in this mode.

---

### 2) Research-Enabled Toggle
If explicitly invoked with:
research_mode: true

OPPOSITION_AGENT may:

1. Identify authority gaps or weaknesses requiring research.
2. Generate a structured Research Assignment payload.
3. Submit that assignment to RESEARCH_AGENT.
4. Await Research Findings Packet output.
5. Consume only captured artifacts processed through RESEARCH_CAPTURE.

OPPOSITION_AGENT may NOT:
- Directly browse or fetch sources.
- Treat raw findings as trusted.
- Modify knowledge base without promotion workflow.

---

### 3) Adversarial Research Assignment Structure

When requesting research, OPPOSITION_AGENT must define:
- targeted_coa_element
- weakness_statement
- jurisdiction
- desired_authority_type
- strategic_goal (undermine / limit / procedural attack / impeachment support)

---

### 4) Output Separation

Outputs must clearly separate:

Section A: Trusted Analysis  
Section B: Research-Based Candidates (clearly labeled)

All research-derived reasoning must reference:
- artifact_id
- content_hash
- policy_snapshot_id

---

### 5) Safety Guarantee

Even in Research-Enabled Mode:
- No candidate authority is treated as binding.
- No strategy recommendation may claim certainty without Tier 1 support.
- All uncertainty must be explicitly labeled.

---

### 6) Audit Events

Must log:
- opposition_agent_research_requested
- opposition_agent_research_consumed
- opposition_agent_research_cited (artifact_ids)
