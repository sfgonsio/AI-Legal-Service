# MAPPING_AGENT

*Authoritative Agent Contract — v2 | Normalized Schema | PASS-2 / PASS-3 Remediation Applied*

## 1. Purpose

The **MAPPING_AGENT** aligns approved case facts to structured evidence under an attorney-approved **Case Lens**.

It produces support links, conflict candidates, negative findings, and evidence coverage analysis without altering canonical state.

## 2. Architectural Position

The **MAPPING_AGENT** operates after:

- Approved Case Perspective
- Approved Fact Pattern
- Completed evidence ingestion
- Identity resolution complete

Outputs proposals only.

Canonical mutation is handled by deterministic programs.

## 3. Execution Modes

### 3.1 Reasoning Mode

Used during:

- Evidence span interpretation
- Cross-document alignment
- Conflict detection
- Hypothesis-aware search

### 3.2 Deterministic Mode

Used during:

- Link strength scoring
- Artifact compilation
- Coverage reporting
- Provenance logging

Deterministic outputs must be reproducible under identical workflow inputs.

## 4. Triggers & Entry Conditions

### 4.1 Trigger

`ATTORNEY_APPROVED_FACT_PATTERN`

### 4.2 Entry Conditions

- `CASE_LENS_SET_APPROVED`
- `EVIDENCE_INGESTION_COMPLETE`
- `IDENTITY_RESOLUTION_COMPLETE`

### 4.3 Rerun Triggers

- `NEW_EVIDENCE_ADDED`
- `CLARIFICATION_APPROVED`

## 5. Preconditions (Approvals Required)

Mapping may only run against:

- Approved fact set
- Approved lens
- Structured evidence index

Commit requires attorney disposition.

## 6. Responsibilities

The **MAPPING_AGENT** shall:

- Align facts ↔ evidence spans
- Detect contradiction candidates
- Produce deterministic link scoring
- Generate gap report
- Produce mandatory negative findings
- Produce evidence coverage report
- Emit proposed graph edges

## 7. Non-Goals (Explicit Exclusions)

The **MAPPING_AGENT** must not:

- Create new facts
- Modify case lens
- Perform COA mapping
- Perform drafting
- Perform strategy interpretation
- Write directly to canonical state
- Communicate with clients

## 8. Inputs (Canonical Artifacts Only)

The agent consumes the following canonical artifacts:

- `CASE_LENS_SET.json`
- `FACT_PATTERN.json`
- `CASE_CONTEXT_PACK.json`
- `EVIDENCE_OBJECTS.json`
- `EVIDENCE_TEXT_INDEX.json`
- `RESOLVED_ENTITY_INDEX.json`
- `THREAD_GROUPINGS.json`

## 9. Outputs (Versioned Artifacts)

The agent produces the following versioned artifacts:

- `FACT_EVIDENCE_MATRIX.json`
- `GRAPH_EDGE_PROPOSALS.json`
- `CONFLICT_CANDIDATES.json`
- `LENS_GAP_REPORT.json`
- `NEGATIVE_FINDINGS.json` *(mandatory)*
- `EVIDENCE_COVERAGE_REPORT.json`
- `MAPPING_PROVENANCE_LOG.json`

## 10. Blocking Authority

The **MAPPING_AGENT** blocks:

- `COA_AGENT`
- Discovery drafting
- Deposition preparation
- Trial strategy

### 10.1 Blocking Conditions

Until:

- Attorney approves mapping bundles
- Graph commit executed

## 11. Human Interaction Points

### 11.1 Attorney Reviews

- Support bundles
- Conflict bundles
- Gap bundles
- Negative findings

### 11.2 Attorney Actions

- Approve
- Reject
- Clarify
- Defer
- Trigger rerun

## 12. Allowed Program Invocations

This section defines the complete and exclusive set of programs the **MAPPING_AGENT** may invoke.

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

The **MAPPING_AGENT** may not overwrite approved artifacts in place. All promoted outputs must be emitted as new immutable versioned artifacts.

### 12.1 Global Invocation Constraints

The **MAPPING_AGENT**:

- may invoke only the programs declared in this section
- may not directly invoke another agent
- may not bypass the orchestrator
- may not bypass schema validation or governance bindings
- may not promote invalid outputs downstream
- must bind execution to active workflow state, lane permissions, policy snapshot, and knowledge snapshot where applicable

### 12.2 Program: `PROGRAM_TAGGING`

#### Purpose

Apply structured classification and tagging to mapped fact-evidence relationships under the approved case lens.

#### Invocation Trigger

Executed when mapped fact-evidence relationships require normalized tag emission and classification artifacts.

#### Required Inputs

- `FACT_PATTERN.json`
- `CASE_LENS_SET.json`
- `EVIDENCE_TEXT_INDEX.json`

#### Optional Inputs

- `THREAD_GROUPINGS.json`
- `CASE_CONTEXT_PACK.json`

#### Outputs Produced

- tag-enriched mapping annotations
- support for `FACT_EVIDENCE_MATRIX.json`
- support for `NEGATIVE_FINDINGS.json`

#### Output Artifacts Affected

- `FACT_EVIDENCE_MATRIX.json`
- `NEGATIVE_FINDINGS.json`
- `MAPPING_PROVENANCE_LOG.json`

#### Preconditions / Guards

- Approved lens must exist
- Approved fact set must exist
- Structured evidence index must exist

#### Determinism Requirements

Execution must bind to:

- workflow state snapshot
- policy snapshot
- knowledge snapshot where applicable

Outputs must pass schema validation before artifact promotion.

Prior artifacts remain immutable.

#### Human Approval Requirements

Attorney disposition is required before any downstream canonical commit that depends on tag-enriched mapping artifacts.

#### Failure Behavior

If schema validation fails or required structured evidence artifacts are missing:

- program execution halts
- downstream promotion is blocked
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

### 12.3 Program: `PROGRAM_COMPOSITE_ENGINE`

#### Purpose

Generate structured relationship and graph edge proposals between facts, entities, and evidence spans.

#### Invocation Trigger

Executed when mapping outputs require graph edge proposals or structured cross-artifact relationship modeling.

#### Required Inputs

- `FACT_PATTERN.json`
- `RESOLVED_ENTITY_INDEX.json`
- `EVIDENCE_TEXT_INDEX.json`

#### Optional Inputs

- `THREAD_GROUPINGS.json`
- `CASE_CONTEXT_PACK.json`

#### Outputs Produced

- `GRAPH_EDGE_PROPOSALS.json`

#### Output Artifacts Affected

- `GRAPH_EDGE_PROPOSALS.json`
- `MAPPING_PROVENANCE_LOG.json`

#### Preconditions / Guards

- Identity resolution must be complete
- Structured evidence index must exist
- Approved fact pattern must exist

#### Determinism Requirements

Execution must bind to:

- workflow state snapshot
- policy snapshot
- entity resolution snapshot
- knowledge snapshot where applicable

Outputs must pass schema validation before artifact promotion.

Prior artifacts remain immutable.

#### Human Approval Requirements

Attorney approval is required before graph commit execution.

#### Failure Behavior

If identity resolution is incomplete or required artifacts are missing:

- program execution halts
- graph proposal promotion is blocked
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

- `INTERVIEW_AGENT`
- Evidence Ingestion Program
- Identity Resolution Program

### 13.2 Downstream

- `COA_AGENT`
- `IMPACT_ANALYSIS_PROGRAM`
- `REVIEW_PACKAGER_PROGRAM`
- `GRAPH_APPLY_PROGRAM`

## 14. Failure Classification

### 14.1 Blocking

- Missing approved lens
- Incomplete identity resolution
- Missing evidence index

### 14.2 Non-Blocking

- Low-confidence links
- High unmapped evidence volume

## 15. Determinism, Reproducibility & Rerun Policy

- Proposal-only mutation
- Supersession-based artifacts
- Deterministic scoring
- Auto-run allowed; attorney disposition required
- Stale marking enforced

## 16. Learning & Governance

- No self-modification
- Scoring profiles versioned
- Lens version controlled
- All mapping runs reference `model_version`

## 17. Pristine Data Policy

### 17.1 Evidence Integrity

- Raw evidence immutable
- All span references hash-based
- No alteration of source material

## 18. SIPOC (Final)

### 18.1 Supplier

- Interview Agent
- Evidence ingestion
- Identity resolution

### 18.2 Input

- Approved facts
- Approved lens
- Structured evidence index

### 18.3 Process

- Alignment
- Conflict detection
- Gap detection
- Scoring
- Proposal compilation

### 18.4 Output

- Mapping artifacts
- Dashboard signal
- Audit events

### 18.5 Customer

- Attorney
- `COA_AGENT`
- Impact analysis

## 19. Acceptance Criteria

- No canonical mutation without disposition
- Negative findings mandatory
- Evidence coverage report present
- All outputs versioned
- Supersession working

## 20. Human Presentation Lens

The **MAPPING_AGENT** is a governed evidentiary alignment engine that systematically connects approved facts to supporting or contradicting evidence under a defined **Case Lens**.

It transforms document review from manual searching into structured evidentiary mapping while preserving full attorney authority.

**AI structures evidence. Humans determine legal meaning.**