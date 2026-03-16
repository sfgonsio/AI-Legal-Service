# AGENT CONTRACT — OPPOSITION_AGENT

**Contract Version:** v1  
**Agent Role:** Adversarial Risk & Weakness Discovery (Defense/Adversary Emulation)  
**Layer:** Brain (Post-Spine Baseline v1.0-spine-stable)  
**Status:** Draft – Brain v1  
**Owner:** Platform SSOT  
**Determinism:** Reasoning output must be replay-stable when inputs are fixed (see §17)

## 1) Mission

Produce a structured, evidence-cited, authority-grounded **Opposition View** of the case: identify weaknesses, gaps, contradictions, and exploitable procedural/tactical vectors, and propose strategies/tactics an opposing counsel would use.

## 2) Non-Goals

- Does not ingest external sources live
- Does not modify facts, entities, evidence mapping, or COA mapping
- Does not promote or mutate knowledge trust levels
- Does not draft final legal filings as authoritative law, though it may produce draft options for attorney review

## 3) Primary Users

- Plaintiff-side attorney (primary)
- Litigation support team / paralegal
- Strategy lead / trial consultant
- Case architect (secondary)

## 4) Inputs (Authoritative)

OPPOSITION_AGENT consumes only SSOT-approved artifacts.

### 4.1 Case Layer (Run-Scoped)

- Facts (`facts` / normalized facts view)
- Entities (`entities`)
- Timeline / event graph (if present)
- Evidence map (`evidence_map`)
- COA map (`coa_map`)
- Interview notes / transcripts (optional)

### 4.2 Knowledge Layer (Trusted-Only by Default)

- authority_text (trusted)
- burden_map (trusted)
- heuristic_rule (trusted)
- practice_guide (trusted)

**Default Query Constraint:** `trust_level == trusted`

Optional override requires explicit run flag plus audit event.

### 4.3 Config / Constraints

- `case_config.yaml`: opposition settings (thresholds, scope, trusted-only mode, etc.)
- Jurisdiction context (e.g., California)

## 5) Outputs (Structured)

OPPOSITION_AGENT outputs a single structured bundle.

### 5.1 Weakness Map (by COA Element)

For each COA and element:

- `element_id`
- burden statement
- current evidence coverage score
- gaps and missing proof types
- contradiction flags
- credibility risk flags
- recommended remediation actions
- citations to evidence plus `authority_text` / `burden_map`

### 5.2 Opposition Strategy Map

- likely defenses (legal + factual)
- attack vectors (how opposing counsel would frame, narrow, or discredit)
- pressure points for discovery and motion practice
- negotiation leverage hypotheses

### 5.3 Tactical Playbook (Prioritized)

- next 10 actions (discovery, meet and confer, motion posture)
- proposed interrogatory themes (not full sets unless requested)
- document request themes
- deposition objectives
- motion-to-compel readiness checklist

### 5.4 Confidence + Assumptions

- confidence score per assertion
- explicit assumptions list
- unknowns list (what must be learned)

## 6) Success Criteria

- Finds real gaps the team missed
- Every claim is traceable to:
  - evidence artifacts, or
  - trusted `authority_text` / `burden_map`
- Produces prioritized, actionable remediation steps
- Generates a coherent adversarial narrative, not disconnected bullet points

## 7) Guardrails & Policy

### 7.1 No Hallucinated Authority

- Must not cite cases or statutes not present in the trusted knowledge layer
- If case law research is required, route to deterministic ingestion workflow (`KNOWLEDGE_INGESTION`) or mark as `needs_research`

### 7.2 No Final Legal Advice

- Output is a decision-support artifact requiring attorney review

### 7.3 Privacy & Security

- Follow platform data handling rules
- No external exfiltration

## 8) Operating Modes

### 8.1 Baseline Mode (Default)

- Trusted knowledge only
- Produce weakness map, strategy map, and tactical playbook

### 8.2 Adversary Simulation Mode

- Generate the most damaging plausible opposing narrative
- Must label speculative items explicitly

### 8.3 Litigation Phase Mode

Discovery phase emphasis:

- interrogatories
- RFPs
- deposition objectives
- motion-to-compel posture

Pre-trial phase emphasis:

- evidentiary objections
- jury instruction risk
- case themes

## 9) Core Reasoning Steps (Deterministic Skeleton)

1. Load COA map and enumerate elements
2. For each element:
   - retrieve `burden_map` plus linked `authority_text` (trusted)
   - compute evidence coverage from `evidence_map` plus `facts`
   - identify gaps, contradictions, and required proof types
3. Build opposition narrative:
   - strongest defenses first (procedural + substantive)
4. Generate tactical plan:
   - discovery themes, meet-and-confer posture, and motion triggers
5. Produce structured output bundle with citations and confidence

## 10) Required Data Contracts (References)

- Knowledge Contract v1 (`contract/v1/knowledge/knowledge_contract.md`)
- Program `KNOWLEDGE_INGESTION` (`contract/v1/programs/program_KNOWLEDGE_INGESTION.md`)
- Evidence map, COA map, and facts/entity schemas (spine)

## 11) Allowed Program Invocations

This section defines the complete and exclusive set of programs the **OPPOSITION_AGENT** may invoke.

No program may be invoked unless declared here.

All invocations must execute through orchestrator-approved execution paths and conform to:

- schema validation requirements
- policy snapshot binding
- knowledge snapshot binding
- workflow rules
- state machine constraints
- lane permissions
- audit logging requirements

Direct agent-to-agent invocation is prohibited.

The **OPPOSITION_AGENT** may not overwrite approved artifacts in place. All promoted outputs must be emitted as new immutable versioned artifacts.

### 11.1 Global Invocation Constraints

The **OPPOSITION_AGENT**:

- may invoke only the programs declared in this section
- may not directly invoke another agent
- may not bypass the orchestrator
- may not bypass schema validation or governance bindings
- may not promote invalid outputs downstream
- must bind execution to active workflow state, lane permissions, policy snapshot, and knowledge snapshot where applicable

### 11.2 Program: `PROGRAM_RESEARCH_ASSIGNMENT`

#### Purpose

Generate a structured research assignment payload when authority gaps or litigation weaknesses require targeted follow-up research.

#### Invocation Trigger

Invocation is permitted only when research-enabled mode is explicitly active and the agent identifies an authority gap, doctrinal uncertainty, or weakness requiring targeted research support.

#### Required Inputs

- `coa_map`
- `evidence_map`
- `facts`
- jurisdiction context
- run configuration with `research_mode: true`

#### Optional Inputs

- interview notes / transcripts
- prior opposition analysis artifacts

#### Outputs Produced

- structured research assignment payload

#### Output Artifacts Affected

- research assignment artifact for downstream research workflow

#### Preconditions / Guards

- Research-enabled mode must be explicitly set
- Targeted weakness must be identified and scoped
- Jurisdiction must be specified

#### Determinism Requirements

Execution must bind to:

- workflow state snapshot
- policy snapshot
- knowledge snapshot
- run configuration

Outputs must pass schema validation before artifact promotion.

Prior artifacts remain immutable.

#### Human Approval Requirements

Attorney approval may be required by workflow policy before assignment submission to downstream research workflow.

#### Failure Behavior

If required targeting fields are missing or research mode is not enabled:

- program execution halts
- research assignment is not emitted
- structured error event is emitted to the audit ledger

#### Audit Requirements

The system must log:

- agent identity
- invoked program name
- `run_id`
- input artifact identifiers
- output artifact identifiers
- snapshot identifiers
- validation results

### 11.3 Program: `PROGRAM_KNOWLEDGE_INGESTION`

#### Purpose

Provide deterministic ingestion path for authority or knowledge gaps identified by the agent.

#### Invocation Trigger

Used only when authority is absent from the trusted knowledge layer and workflow policy permits formal ingestion routing.

#### Required Inputs

- research or authority gap description
- jurisdiction context
- approved ingestion request parameters

#### Optional Inputs

- structured research assignment payload

#### Outputs Produced

- routed ingestion request or `needs_research` classification support

#### Output Artifacts Affected

- ingestion request artifact
- audit references supporting later knowledge capture

#### Preconditions / Guards

- Missing authority must be explicitly identified
- Workflow must permit deterministic ingestion routing

#### Determinism Requirements

Execution must bind to:

- workflow state snapshot
- policy snapshot
- knowledge snapshot
- approved config parameters

Outputs must pass schema validation before artifact promotion.

Prior artifacts remain immutable.

#### Human Approval Requirements

Attorney or authorized operator approval may be required before formal ingestion workflow activation.

#### Failure Behavior

If ingestion routing is not permitted or required inputs are missing:

- program execution halts
- authority gap remains labeled `needs_research`
- structured error event is emitted to the audit ledger

#### Audit Requirements

The system must log:

- agent identity
- invoked program name
- `run_id`
- input artifact identifiers
- output artifact identifiers
- snapshot identifiers
- validation results

## 12) Tool Access (Through Tool Gateway Only)

OPPOSITION_AGENT may call only tools explicitly assigned in lanes policy and tool registry.

No direct network or web calls.

Typical allowed tool categories:

- `retrieval.query_knowledge` (trusted-only filter enforced)
- `retrieval.query_case_artifacts`
- `scoring.coverage_matrix`
- `export.bundle_writer`

If the tool is not in registry or lanes policy, it is disallowed.

## 13) Human Checkpoints

### 13.1 Attorney Review Required

Before any tactical recommendation becomes a task in the system:

- attorney approval gate required

### 13.2 Knowledge Promotion Boundary

OPPOSITION_AGENT may request promotion (“this heuristic should be trusted”), but cannot perform promotion.

## 14) Audit Ledger Events (Must Log)

For every run:

- `opposition_agent_run_started`
- `opposition_agent_inputs_bound` (`run_id`, knowledge snapshot id)
- `opposition_agent_output_emitted` (artifact ids)
- `opposition_agent_override_used` (if trusted-only overridden)

Override event must include:

- who approved
- why
- scope
- timestamp

## 15) Failure Modes & Safe Degradation

If knowledge layer is missing:

- produce `needs_research` flags
- proceed using evidence-only gaps

If COA map is missing:

- refuse to perform element-level coverage
- produce case-wide adversarial risk list with citations

If evidence map is sparse:

- prioritize discovery gap identification

## 16) Output Format (Canonical Bundle)

OPPOSITION_AGENT writes:

- `artifacts/opposition/weakness_map.json`
- `artifacts/opposition/strategy_map.json`
- `artifacts/opposition/tactical_playbook.json`
- `artifacts/opposition/opposition_summary.md` (human-readable)

All artifacts must include:

- `run_id`
- `ingest_run_id` / knowledge snapshot reference
- timestamp
- hashes / fingerprints

## 17) Determinism & Replay Requirements

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

## 18) Testing & Acceptance (Brain v1)

Minimum acceptance:

- Given a small fixture case, produces:
  - at least 1 gap per COA element with missing proof type
  - at least 5 prioritized tactical actions
  - citations on >95% of assertions
- Fails safely when trusted knowledge is not available

## 19) Open Questions (Tracked)

- Do we model opposition counsel personas (aggressive vs. conservative)?
- Do we include settlement leverage modeling later?
- Do we integrate DissoMaster outputs as a trusted knowledge object type in the future?

## 20) Human Presentation Lens (Attorney-Friendly Narrative)

OPPOSITION_AGENT is the platform’s red-team attorney:

- It assumes the opposing side will exploit every weakness
- It checks whether each legal claim is supported by:
  - evidence, and
  - the elements required to prove that claim
- It reveals what the other side will argue
- It proposes what we do next—discovery, motions, and strategy—before the other side does

The value is not automation for its own sake.

The value is reducing surprise in litigation.

## 21) Research-Enabled Mode (Optional Extension)

### 21.1 Default Behavior

OPPOSITION_AGENT operates in Trusted-Only Mode by default.

It consumes:

- Case evidence
- Trusted knowledge objects (Knowledge Contract v1)
- Approved internal playbooks

No external discovery occurs in this mode.

### 21.2 Research-Enabled Toggle

If explicitly invoked with:

`research_mode: true`

OPPOSITION_AGENT may:

1. Identify authority gaps or weaknesses requiring research
2. Generate a structured Research Assignment payload
3. Submit that assignment to `RESEARCH_AGENT` through approved orchestrated workflow
4. Await Research Findings Packet output
5. Consume only captured artifacts processed through `RESEARCH_CAPTURE`

OPPOSITION_AGENT may not:

- directly browse or fetch sources
- treat raw findings as trusted
- modify knowledge base without promotion workflow

### 21.3 Adversarial Research Assignment Structure

When requesting research, OPPOSITION_AGENT must define:

- `targeted_coa_element`
- `weakness_statement`
- `jurisdiction`
- `desired_authority_type`
- `strategic_goal` (`undermine / limit / procedural attack / impeachment support`)

### 21.4 Output Separation

Outputs must clearly separate:

- Section A: Trusted Analysis
- Section B: Research-Based Candidates (clearly labeled)

All research-derived reasoning must reference:

- `artifact_id`
- `content_hash`
- `policy_snapshot_id`

### 21.5 Safety Guarantee

Even in Research-Enabled Mode:

- No candidate authority is treated as binding
- No strategy recommendation may claim certainty without Tier 1 support
- All uncertainty must be explicitly labeled

### 21.6 Audit Events

Must log:

- `opposition_agent_research_requested`
- `opposition_agent_research_consumed`
- `opposition_agent_research_cited` (`artifact_ids`)