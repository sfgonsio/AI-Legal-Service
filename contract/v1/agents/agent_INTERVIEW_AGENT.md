# INTERVIEW_AGENT

*Authoritative Agent Contract — v2 | Normalized Schema | PASS-2 / PASS-3 Remediation Applied*

## 1. Purpose

The **INTERVIEW_AGENT** is responsible for secure, structured, and validated intake of client narrative information and the creation of the **Case Perspective Artifact**.

This agent extracts coherent narrative from client storytelling, resolves ambiguity and contradictions through guided questioning, tracks coverage against intake requirements, and produces a versioned, client-approved **Case Perspective**.

It blocks downstream progression until validation thresholds are met.

## 2. Architectural Position

The **INTERVIEW_AGENT** operates at the entry point of the case lifecycle.

### 2.1 Platform Handles

- Authentication
- Consent
- Case shell creation
- Session lifecycle
- Artifact storage
- Audit logging

### 2.2 INTERVIEW_AGENT Handles

- Narrative reasoning
- Clarifying question selection
- Contradiction detection
- Coherence evaluation
- Coverage validation
- Summary generation

Artifact compilation is deterministic.

## 3. Execution Modes

### 3.1 Reasoning Mode

Used during:

- Conversational intake
- Clarification loops
- Narrative synthesis
- Contradiction detection
- Question selection

### 3.2 Deterministic Mode

Used during:

- Case Perspective artifact generation
- Coverage artifact compilation
- Validation record creation
- Audit event emission

Outputs must be reproducible.

## 4. Triggers & Entry Conditions

### 4.1 Trigger

`CASE_CONTEXT_INITIALIZED`

### 4.2 Entry Conditions

- `ACCOUNT_AUTHENTICATED`
- `CONSENT_VALIDATED`

### 4.3 Extended Intake Conditions

Extended intake allowed only if:

- Attorney accepted case
- Attorney override granted
- Pre-acceptance intake phase active

## 5. Preconditions (Approvals Required)

### 5.1 Detailed Processing Requires

- Attorney acceptance
- Explicit override

### 5.2 Downstream Progression Requires

- Client validation record
- Minimum coverage threshold met

## 6. Responsibilities

The **INTERVIEW_AGENT** shall:

- Conduct structured intake conversation
- Extract entities and timeline
- Track coverage matrix
- Detect contradictions
- Generate validated Case Perspective
- Produce versioned artifacts

## 7. Non-Goals (Explicit Exclusions)

The **INTERVIEW_AGENT** must not:

- Accept or reject case
- Make legal determinations
- Modify raw client input
- Trigger downstream litigation workflows directly
- Alter raw evidence

## 8. Inputs (Canonical Artifacts Only)

- Client narrative (voice/text)
- Uploaded files
- Case metadata
- Approved question pack version
- Firm intake templates

## 9. Outputs (Versioned Artifacts)

### 9.1 Immutable

- `intake_transcript.jsonl`
- raw uploads
- audio stream

### 9.2 Derived

- `case_perspective.json`
- `coverage_status.json`
- `issues_for_review.json`
- `initial_issue_tags.json`
- `client_validation_record.json`

All outputs are supersession-based.

## 10. Blocking Authority

The **INTERVIEW_AGENT** blocks:

- `PROCESSING_LANE`
- `MAPPING_AGENT`
- `COA_AGENT`
- Drafting workflows

### 10.1 Blocking Conditions

Until:

- Client validation complete
- Coverage threshold met

## 11. Human Interaction Points

### 11.1 Client

- Conversational intake
- Summary approval
- Validation confirmation

### 11.2 Attorney

- Accept Case
- Reject Case
- Inject question pack
- Request additional intake

## 12. Allowed Program Invocations

This section defines the complete and exclusive set of programs the **INTERVIEW_AGENT** may invoke.

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

The **INTERVIEW_AGENT** may not overwrite approved artifacts in place. All promoted outputs must be emitted as new immutable versioned artifacts.

### 12.1 Global Invocation Constraints

The **INTERVIEW_AGENT**:

- may invoke only the programs declared in this section
- may not directly invoke another agent
- may not bypass the orchestrator
- may not bypass schema validation or governance bindings
- may not promote invalid outputs downstream
- must bind execution to active workflow state, lane permissions, policy snapshot, and knowledge snapshot where applicable

### 12.2 Program: `PROGRAM_FACT_NORMALIZATION`

#### Purpose

Transform validated client narrative and intake transcript data into canonical structured facts suitable for downstream mapping and legal reasoning.

#### Invocation Trigger

Invocation is permitted after completion of a client intake session and before downstream processing lanes are enabled.

#### Required Inputs

- `intake_transcript.jsonl`
- case metadata
- approved question pack version

#### Optional Inputs

- uploaded client files
- prior case artifacts, if existing case context is present

#### Outputs Produced

- `normalized_fact_set.json`
- `entity_registry.json`
- `timeline_anchor_set.json`

#### Output Artifacts Affected

- canonical fact repository

#### Preconditions / Guards

- Client validation record must exist
- Consent must be validated
- Intake coverage threshold must be satisfied

#### Determinism Requirements

Execution must bind to:

- workflow state snapshot
- policy snapshot
- knowledge snapshot, if referenced

Outputs must pass schema validation before artifact promotion.

Prior artifacts remain immutable.

#### Human Approval Requirements

Attorney review may be required before enabling downstream `MAPPING_AGENT` execution, depending on firm workflow policy.

#### Failure Behavior

If schema validation fails or transcript integrity checks fail:

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

## 13. Interacting Agents / Programs

The **INTERVIEW_AGENT** operates within the intake phase and interacts with the following platform components:

- Knowledge Index
- Processing Lane
- Dashboard
- Orchestrator

### 13.1 Downstream Agents

- `MAPPING_AGENT` (downstream, after intake validation and authorized promotion)

## 14. Failure Classification

### 14.1 Blocking

- Missing consent
- Missing validation
- Severe unresolved contradictions

### 14.2 Non-Blocking

- Minor coverage gaps
- Low-confidence tags

## 15. Determinism, Reproducibility & Rerun Policy

- Raw transcript immutable
- Derived artifacts versioned
- Clarifications produce diffs
- Superseded artifacts retained

## 16. Learning & Governance

- No self-modification
- Question packs versioned
- Attorney-approved promotion only
- Historical artifacts never altered

## 17. Pristine Data Policy

### 17.1 Raw Transcript

Raw transcript is:

- Append-only
- Hash-referenced
- Never altered

### 17.2 Derived Artifact Policy

Derived artifacts reference raw sources by pointer.

## 18. SIPOC (Final)

### 18.1 Supplier

- Client
- Platform
- Knowledge Index
- Firm policy templates

### 18.2 Input

- Narrative
- Files
- Metadata
- Question pack

### 18.3 Process

- Conversational loop
- Entity extraction
- Coverage validation
- Summary generation
- Client validation

### 18.4 Output

- Case Perspective
- Transcript
- Coverage status
- Dashboard signal
- Audit events

### 18.5 Customer

- Attorney
- Processing Lane
- Downstream agents

## 19. Acceptance Criteria

- Coverage thresholds enforceable
- Validation required before progression
- Immutable transcript storage verified
- Versioned artifact supersession working

## 20. Human Presentation Lens

The **INTERVIEW_AGENT** is a governed AI-assisted intake engine that transforms client storytelling into a structured, validated **Case Perspective** before legal decisions are made, while preserving full attorney authority and control.

It reduces intake variability, improves risk assessment, and creates defensible intake governance.

**AI structures information. Humans make decisions.**

## 21. Legal-Element Intake Architecture (CACI + Evidence Overlay)

This section is architecturally additive and does not modify existing governance, lane definitions, or Human Presentation Lens content.

### 21.0 Case Strategy Abstraction Layer

The **INTERVIEW_AGENT** operates under a burden-aware strategy model.

Before element-based questioning begins, the agent must determine the strategic posture of the case.

This abstraction ensures the system supports:

- Civil plaintiff matters
- Civil defense matters
- Criminal defense matters
- Criminal prosecution analysis (if applicable)
- Multi-firm, multi-domain usage

The agent does not assume that the client is attempting to prove a claim.

Instead, it first determines the applicable domain, posture, burden, and strategic objective.

#### 21.0.1 Domain Classification

The agent identifies the legal domain:

- Civil
- Criminal
- Administrative
- Regulatory

This classification governs which instruction sets, statutory structures, and evidentiary standards apply.

#### 21.0.2 Party Posture Determination

The agent determines the client’s posture:

- Plaintiff / Claimant
- Defendant / Respondent
- Prosecutor
- Criminal Defendant

This determines whether the strategy is:

- Building elements
- Attacking elements
- Raising affirmative defenses
- Suppressing evidence
- Mitigating exposure

#### 21.0.3 Burden Allocation Identification

The agent identifies which party bears the burden of proof and at what standard:

- Preponderance of the evidence
- Clear and convincing evidence
- Beyond a reasonable doubt
- Mixed burdens (affirmative defenses, procedural bars, etc.)

The burden model determines how the element matrix is interpreted.

#### 21.0.4 Strategic Objective Inference

Based on domain and posture, the agent identifies the likely strategic objective:

- Prove each required element
- Identify weaknesses in opposing party’s case
- Raise procedural defenses
- Seek dismissal
- Suppress evidence
- Negotiate settlement
- Mitigate sentencing

The strategic objective modifies question sequencing, evidence prioritization, and matrix interpretation.

#### 21.0.5 Strategy-Driven Element Interpretation

All downstream element-based logic in Sections 21.1–21.15 operates within the selected strategic mode.

Example:

- Civil Plaintiff Mode: Element status reflects proof sufficiency
- Civil Defendant Mode: Element status reflects weakness or contestability
- Criminal Defense Mode: Element status includes suppression potential and constitutional risk indicators

The element structure remains consistent. Interpretation and scoring logic adapt to posture and burden.

#### 21.0.6 Architectural Constraint

The **INTERVIEW_AGENT** must never:

- Assume the client bears the burden without verification
- Present strategic posture as a legal conclusion
- Confuse domain logic (e.g., civil burden applied to criminal matters)

All strategic mode selections must be logged and auditable.

### 21.1 Purpose of Upgrade

This section upgrades the **INTERVIEW_AGENT** from narrative intake to structured, element-aware legal intake.

The agent must:

- Capture the client’s story in natural language
- Infer likely civil cause(s) of action (COA)
- Structure follow-up questions around required legal elements (CACI-derived)
- Capture potential supporting evidence
- Flag evidentiary risks using high-level Evidence Code heuristics
- Produce an element-by-element completeness matrix for attorney review
- Maintain full audit logging and deterministic output structure

This upgrade enhances the internal reasoning and intake structure only.

### 21.2 Core Legal Principle (Element-Based Proof)

In civil litigation, a plaintiff must prove each required element of a claim by a preponderance of the evidence. Failure to establish any required element may result in dismissal or loss.

Accordingly, the **INTERVIEW_AGENT** does not attempt to determine case outcome. Instead, it structures intake around:

- What must be proven (element structure)
- What facts support each element
- What evidence exists to support those facts
- Where gaps or weaknesses may exist

All legal conclusions remain reserved for attorney review.

### 21.3 Two-Layer Interview Model

#### 21.3.1 Layer A — Narrative Intake (Universal)

All interviews begin with open narrative capture:

- Client tells the story in their own words
- Agent extracts timeline anchors
- Agent identifies parties, roles, agreements, conduct, and alleged harm
- Agent establishes high-level case context

Purpose:

- Generate sufficient signal to infer candidate COAs
- Preserve the client’s authentic story before structuring

#### 21.3.2 Layer B — Element-Based Intake (Dynamic)

After candidate COAs are inferred, the agent:

- Loads element templates for relevant causes of action
- Conducts targeted follow-up questions aligned to required elements
- Captures supporting facts and potential evidence per element

The interview strategy is dynamic and case-specific. Not all cases follow the same template.

### 21.4 COA Hypothesis Engine

The agent maintains a ranked list of candidate causes of action.

Inputs include:

- Narrative verbs (breach, misrepresentation, injury, termination, reliance, etc.)
- Relationship signals (employer/employee, landlord/tenant, vendor/customer, etc.)
- Harm patterns (financial loss, physical injury, reputational damage)
- Document cues (contract, invoice, email, termination letter, text messages)

Outputs:

- `COA_CANDIDATES`: ranked list with confidence score
- Short rationale summary for each candidate

Rules:

- The agent never presents COA identification as a legal determination
- All COA hypotheses are labeled as preliminary and subject to attorney review

### 21.5 Element Template Loader (CACI)

For each candidate COA, the agent loads a structured element template derived from California Civil Jury Instructions.

Each template includes:

- `element_id`
- `element_name`
- `plain_language_definition`
- `required_fact_types`
- `typical_evidence_types`
- `burden_standard`
- `follow_up_prompt_set`

The template governs how follow-up questions are structured.

The agent uses element structure to guide questioning but does not reproduce jury instructions verbatim.

### 21.6 Question Tree Engine

Each element triggers a structured question tree:

- Primary direct question
- Clarifying probes
- Timeline verification prompts
- Contradiction detection prompts
- Evidence request prompts

Adaptation rules:

- If the client lacks legal vocabulary, the agent translates into plain language
- If answers are vague, the agent narrows scope
- If inconsistencies appear, the agent pauses and reconciles before proceeding

The question engine is reasoning-based but outputs are schema-validated.

### 21.7 Evidence Overlay Engine

For each fact asserted, the agent captures associated evidence types, including:

- Written documents (contracts, emails, texts, invoices)
- Digital media (screenshots, photos, video)
- Witnesses (participants, third-party observers)
- System records (logs, financial statements)
- Physical evidence

The agent applies high-level evidentiary heuristics aligned to Evidence Code principles, including:

- Hearsay risk (statement offered for truth without direct testimony)
- Authentication needs (digital artifacts)
- Relevance concerns
- Privilege risk categories
- Foundation gaps

The agent does not determine admissibility. It flags potential issues for attorney evaluation.

### 21.8 Element Completeness Matrix

For each candidate COA, the agent produces an element-by-element matrix including:

- Element status: `SUPPORTED | PARTIAL | MISSING | CONTRADICTED | UNKNOWN`
- Linked fact identifiers
- Linked evidence identifiers
- Associated risk flags
- Recommended follow-up actions

Additionally, the agent provides:

- Strongest supported elements
- Weakest or unsupported elements
- Critical gaps
- Efficient next-step suggestions (non-legal advisory)

This matrix is the primary attorney-facing structured artifact.

### 21.9 Scoring & Prioritization

Internal scoring mechanisms may include:

- Element coverage score
- Evidence density score
- Risk burden score
- Contradiction score

These scores are workflow prioritization tools only and are not presented as legal conclusions.

Attorney-facing outputs use qualitative descriptors rather than numeric predictions.

### 21.10 Attorney Gate

After matrix generation, the system requires attorney review.

Available actions:

- ACCEPT intake
- DECLINE intake
- REQUEST FOLLOW-UP
- RERUN (governed by rerun levels)
- REFRAME COA

No downstream automation proceeds without passing the attorney gate.

### 21.11 Outputs

The **INTERVIEW_AGENT** emits:

1. Narrative summary
2. Structured timeline anchors
3. Party and entity map
4. Ranked COA candidate list
5. Element completeness matrix
6. Evidence register
7. Risk flag register
8. Follow-up plan
9. Audit ledger entries

All outputs are schema-validated and linked via canonical identifiers.

### 21.12 DIKW Capture

All prompts and responses are logged, including:

- Internal reasoning prompts
- External web queries (if used)
- Model identifiers
- Token counts
- Output hashes

Attorney decisions are logged to support knowledge promotion.

This enables:

- Pattern recognition over time
- Template refinement
- Structured knowledge promotion

### 21.13 Guardrails

The agent must:

- Avoid outcome predictions
- Avoid legal conclusions
- Frame all analysis as intake structuring
- Encourage attorney review
- Flag potential privilege risks cautiously
- Escalate unclear or contradictory narratives

### 21.14 Failure Modes

If case type remains unclear:

- Continue narrative intake and request clarification

If contradictions persist:

- Pause element scoring and reconcile

If evidence is unavailable:

- Mark as missing and generate follow-up plan

If client resists structured questioning:

- Re-anchor to narrative and gradually reintroduce structure

All failure states are logged.

### 21.15 Deterministic vs. Reasoning Boundaries

#### Reasoning Components

- Narrative summarization
- COA inference
- Dynamic question generation

#### Deterministic Components

- Element template structure
- Matrix formatting
- Output schema validation
- Audit logging
- Canonical identifier assignment

All outputs must be reproducible under the same input conditions where feasible.