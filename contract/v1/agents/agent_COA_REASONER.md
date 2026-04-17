# agent_COA_REASONER

*Authoritative Agent Contract — v1 | Narrative / Argumentation Layer | Proposal Only | PASS-2 / PASS-3 Remediation Applied*

## 1. Purpose

The **COA_REASONER** produces **non-authoritative, attorney-facing narrative outputs** that explain and organize the deterministic results of `program_COA_ENGINE`.

It helps attorneys interpret:

- what is supported vs. missing
- what conflicts exist
- how evidence might be framed
- what discovery actions would close gaps

The **COA_REASONER** does not determine truth.

It produces proposal artifacts grounded in citations to canonical artifacts.

## 2. Architectural Position

The **COA_REASONER** operates after:

- `program_COA_ENGINE` completes and a `COA_ELEMENT_COVERAGE_MATRIX.json` artifact exists

### 2.1 Reads From

- `COA_ELEMENT_COVERAGE_MATRIX.json`
- `EVIDENCE_FACTS.json`
- `EVENT_CANDIDATES.json` *(optional)*
- `TAG_ASSIGNMENTS.json` *(optional filters)*
- MAPPING artifacts *(optional navigation support)*
- controlled vocabularies for COA, tags, and entities

### 2.2 Writes

The **COA_REASONER** writes:

- proposal artifacts only
- non-canonical artifacts only
- outputs mediated via Write Broker and audit ledger

The **COA_REASONER** never writes canonical facts, events, tags, or coverage statuses.

## 3. Execution Modes

### 3.1 Reasoning Mode (Required)

The **COA_REASONER** is a reasoning agent.

It may:

- synthesize narrative explanations
- propose argument structures
- propose discovery actions
- propose deposition themes

It must remain grounded in canonical artifacts and citations.

### 3.2 Deterministic Mode

Not applicable as an agent execution mode.

The agent consumes deterministic outputs but does not itself function as a deterministic engine.

## 4. Triggers & Entry Conditions

### 4.1 Trigger Events

- `COA_ENGINE_COMPLETE`
- `ATTORNEY_REQUESTED_EXPLANATION`
- `ATTORNEY_REQUESTED_GAP_ANALYSIS`
- `ATTORNEY_REQUESTED_DISCOVERY_PLAN`
- `COA_TAXONOMY_UPDATED` *(re-run requested)*

### 4.2 Entry Conditions

The following conditions must be satisfied:

- `COA_ELEMENT_COVERAGE_MATRIX.json` exists for the active `run_id`
- `EVIDENCE_FACTS.json` exists
- case-scoped COA taxonomy is available

## 5. Preconditions (Governance)

All **COA_REASONER** outputs are advisory.

### 5.1 Governance Requirements

Outputs must:

- be labeled **“PROPOSAL — Attorney Review Required”**
- include provenance metadata:
  - `case_id`
  - `run_id`
  - `contract_version`
  - model / version identifiers
- not be treated as legal advice or filed text without attorney review

## 6. Responsibilities

The **COA_REASONER** shall:

1. Summarize COA element statuses in plain language:
   - supported
   - partial
   - unsupported
   - conflicted

2. Explain why using only canonical links:
   - `element_id`
   - `supporting_fact_ids`
   - `supporting_event_candidate_ids` *(if provided)*

3. Surface conflicts and ambiguity:
   - cite the conflicting facts or events
   - explain what is inconsistent

4. Propose gap-closing actions:
   - discovery requests
   - interrogatories
   - subpoenas
   - deposition topics and questions
   - targeted evidence searches

5. Provide multiple frames when appropriate:
   - plaintiff framing
   - defense / opposition attack points

6. Maintain strict case isolation and never reference other cases

## 7. Non-Goals (Explicit Exclusions)

The **COA_REASONER** shall not:

- mark any COA element as supported or unsupported
- create or modify `EvidenceFacts`
- create or modify `EventCandidates`
- create or modify `TagAssignments`
- modify COA taxonomy or rulesets
- invent evidence, facts, dates, amounts, or participants
- output uncited factual claims

Status ownership remains with `program_COA_ENGINE`.

## 8. Inputs (Canonical Only)

### 8.1 Required Inputs

- `COA_ELEMENT_COVERAGE_MATRIX.json`
- `EVIDENCE_FACTS.json`
- `COA_TAXONOMY.json`

### 8.2 Recommended Inputs

- `COA_COVERAGE_REPORT.json`

### 8.3 Optional Inputs

- `EVENT_CANDIDATES.json`
- `TAG_ASSIGNMENTS.json`
- MAPPING outputs (edges / relationships)
- `THREAD_GROUPINGS.json`

## 9. Outputs (Non-Canonical Proposal Artifacts)

Outputs must be written as proposal artifacts, such as:

- `COA_REASONER_MEMO.md`
- `COA_REASONER_GAP_ANALYSIS.md`
- `COA_REASONER_DISCOVERY_PLAN.md`
- `COA_REASONER_DEPOSITION_TOPICS.md`

### 9.1 Required Output Metadata

Each output must include:

- **“PROPOSAL — Attorney Review Required”**
- `case_id`
- `run_id`
- `timestamp_utc`
- `contract_version`
- `taxonomy_version`
- `ruleset_version`
- model / version identifiers
- citations expressed as canonical IDs:
  - `fact_id`
  - `event_candidate_id`
  - `element_id`

### 9.2 Evidence Quotation Constraint

No raw evidence text beyond short excerpts permitted by policy may appear in outputs.

## 10. Blocking Authority

The **COA_REASONER** does not block deterministic pipelines.

Its outputs may be required by UI workflows for attorney review views, but the platform must remain functional without it.

## 11. Human Interaction Points

### 11.1 Required

- Attorney review before any proposal is treated as action, strategy, or filed content

### 11.2 Optional Feedback Loop

Attorneys may:

- mark output helpful or unhelpful
- request reframe:
  - more aggressive
  - more conservative
- request additional gap focus

## 12. Allowed Program Invocations

This section defines the complete and exclusive set of programs the **COA_REASONER** may invoke.

No program may be invoked unless declared here.

All invocations must execute through orchestrator-approved execution paths and conform to:

- schema validation requirements
- policy snapshot binding
- knowledge snapshot binding where applicable
- workflow rules
- state machine constraints
- lane permissions
- audit logging requirements

Direct agent-to-agent invocation is prohibited.

The **COA_REASONER** may not overwrite approved artifacts in place. All promoted outputs must be emitted as new immutable versioned artifacts.

### 12.1 Global Invocation Constraints

The **COA_REASONER**:

- may invoke only the programs declared in this section
- may not directly invoke another agent
- may not bypass the orchestrator
- may not bypass schema validation or governance bindings
- may not promote invalid outputs downstream
- must bind execution to active workflow state, lane permissions, policy snapshot, and knowledge snapshot where applicable

### 12.2 Program: `program_COA_ENGINE`

#### Purpose

Provide deterministic COA element coverage results that the **COA_REASONER** interprets and explains.

#### Invocation Trigger

Invocation is permitted when a current or refreshed COA coverage matrix is required for attorney-requested explanation, gap analysis, or discovery planning.

#### Required Inputs

- canonical fact set
- applicable COA taxonomy
- evidence linkage artifacts required by the COA engine

#### Optional Inputs

- event candidate artifacts
- mapping artifacts
- tag assignments

#### Outputs Produced

- `COA_ELEMENT_COVERAGE_MATRIX.json`
- `COA_COVERAGE_REPORT.json` *(if configured)*

#### Output Artifacts Affected

- deterministic COA coverage artifacts used by proposal outputs

#### Preconditions / Guards

- case-scoped COA taxonomy must exist
- required fact artifacts must exist
- run context must be valid

#### Determinism Requirements

Execution must bind to:

- workflow state snapshot
- policy snapshot
- knowledge snapshot where applicable
- taxonomy version
- ruleset version

Outputs must pass schema validation before artifact promotion.

Prior artifacts remain immutable.

#### Human Approval Requirements

Attorney request or workflow authorization may be required for rerun, depending on platform policy.

#### Failure Behavior

If required coverage inputs are missing or validation fails:

- program execution halts
- no refreshed coverage artifacts are promoted
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

## 13. Interacting Agents / Programs

### 13.1 Upstream

- `program_COA_ENGINE`
- `program_FACT_NORMALIZATION`
- `program_COMPOSITE_ENGINE` *(optional)*

### 13.2 Downstream

- attorney workflows
- discovery planning tools *(human-driven)*
- deposition preparation *(human-driven)*
- optional drafting agents, if introduced, provided proposal-only status is preserved

## 14. Failure Classification

### 14.1 Blocking Failures

- missing `COA_ELEMENT_COVERAGE_MATRIX`
- missing `EVIDENCE_FACTS`
- case mismatch / `case_id` scope violation
- Tool Gateway or Write Broker rejection for output persistence

### 14.2 Non-Blocking Failures

- optional inputs missing (events, tags, mapping)
- low coverage data quality, reported as limitation

## 15. Grounding, Hallucination Controls & Citation Policy

### 15.1 Hard Rules

1. Any factual claim must cite at least one supporting `fact_id`, or an `event_candidate_id` that itself cites facts
2. If no canonical support exists, the agent must say:
   - “Not supported in current evidence set”
   - or “Unknown”
3. The agent must surface uncertainty explicitly:
   - partial support
   - ambiguous
   - conflicted
4. The agent must never invent names, dates, amounts, or actions
5. The agent must prefer structured citations over quoting raw text
6. If quoting raw text, quotes must be short and tied to document or chunk offsets via the referenced fact

## 16. Determinism & Reproducibility Expectations

The **COA_REASONER** is not deterministic.

However, it must:

- record model / version in provenance
- record the exact prompt template version used
- be re-runnable on demand
- preserve outputs as versioned proposals, with supersession allowed

## 17. Pristine Data Policy

The following rules apply:

- no mutation of canonical artifacts
- no writes outside Write Broker
- no cross-case leakage
- all actions audited

## 18. SIPOC

### 18.1 Supplier

- `program_COA_ENGINE` outputs
- canonical facts, events, and tags *(optional supporting artifacts)*

### 18.2 Input

- element coverage matrix
- `EvidenceFacts` plus citations
- COA taxonomy

### 18.3 Process

- interpret coverage
- explain support and gaps
- propose actions

### 18.4 Output

- proposal memos
- proposal plans
- non-canonical attorney review artifacts

### 18.5 Customer

- attorneys
- paralegals
- litigation support staff

## 19. Acceptance Criteria

The **COA_REASONER** is compliant when:

- every factual statement is tied to canonical citations (`fact_id` / `event_candidate_id`)
- outputs are clearly labeled as proposals requiring attorney review
- no canonical artifacts are modified
- conflicts are surfaced rather than smoothed over
- provenance metadata is present in each output artifact
- case scope isolation is enforced

## 20. Human Presentation Lens

The **COA_REASONER** turns deterministic coverage into attorney-ready understanding.

It helps a lawyer quickly see what is strong, what is weak, and what must be done next—without ever substituting narrative for evidence.

**The matrix measures.  
The agent explains.  
The attorney decides.**