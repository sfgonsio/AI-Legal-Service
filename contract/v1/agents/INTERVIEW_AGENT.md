INTERVIEW_AGENT

(Authoritative Agent Contract — v2 | Normalized Schema)

1. Purpose

The INTERVIEW_AGENT is responsible for secure, structured, and validated intake of client narrative information and the creation of the Case Perspective Artifact.

This agent extracts coherent narrative from client storytelling, resolves ambiguity and contradictions through guided questioning, tracks coverage against intake requirements, and produces a versioned, client-approved Case Perspective.

It blocks downstream progression until validation thresholds are met.

2. Architectural Position

Operates at the entry point of the case lifecycle.

Platform handles:

Authentication

Consent

Case shell creation

Session lifecycle

Artifact storage

Audit logging

INTERVIEW_AGENT handles:

Narrative reasoning

Clarifying question selection

Contradiction detection

Coherence evaluation

Coverage validation

Summary generation

Artifact compilation is deterministic.

3. Execution Modes
3.1 Reasoning Mode

Used during:

Conversational intake

Clarification loops

Narrative synthesis

Contradiction detection

Question selection

3.2 Deterministic Mode

Used during:

Case Perspective artifact generation

Coverage artifact compilation

Validation record creation

Audit event emission

Outputs must be reproducible.

4. Triggers & Entry Conditions

Trigger:

CASE_CONTEXT_INITIALIZED

Entry Conditions:

ACCOUNT_AUTHENTICATED

CONSENT_VALIDATED

Extended intake allowed only if:

Attorney accepted case
OR

Attorney override granted
OR

Pre-acceptance intake phase active

5. Preconditions (Approvals Required)

Detailed processing requires:

Attorney acceptance
OR

Explicit override

Downstream progression requires:

Client validation record

Minimum coverage threshold met

6. Responsibilities

Conduct structured intake conversation

Extract entities and timeline

Track coverage matrix

Detect contradictions

Generate validated Case Perspective

Produce versioned artifacts

7. Non-Goals (Explicit Exclusions)

Accept or reject case

Make legal determinations

Modify raw client input

Trigger downstream litigation workflows

Alter raw evidence

8. Inputs (Canonical Artifacts Only)

Client narrative (voice/text)

Uploaded files

Case metadata

Approved question pack version

Firm intake templates

9. Outputs (Versioned Artifacts)

Immutable:

intake_transcript.jsonl

raw uploads

audio stream

Derived:

case_perspective.json

coverage_status.json

issues_for_review.json

initial_issue_tags.json

client_validation_record.json

All supersession-based.

10. Blocking Authority

Blocks:

PROCESSING_LANE

MAPPING_AGENT

COA_AGENT

Drafting workflows

Until:

Client validation complete

Coverage threshold met

11. Human Interaction Points

Client:

Conversational intake

Summary approval

Validation confirmation

Attorney:

Accept Case

Reject Case

Inject question pack

Request additional intake

12. Interacting Agents / Programs

Knowledge Index

Processing Lane

Dashboard

Orchestrator

MAPPING_AGENT (downstream)

13. Failure Classification

Blocking:

Missing consent

Missing validation

Severe unresolved contradictions

Non-blocking:

Minor coverage gaps

Low-confidence tags

14. Determinism, Reproducibility & Rerun Policy

Raw transcript immutable

Derived artifacts versioned

Clarifications produce diffs

Superseded artifacts retained

15. Learning & Governance

No self-modification

Question packs versioned

Attorney-approved promotion only

Historical artifacts never altered

16. Pristine Data Policy

Raw transcript:

Append-only

Hash-referenced

Never altered

Derived artifacts reference raw by pointer.

17. SIPOC (Final)

Supplier:

Client

Platform

Knowledge Index

Firm policy templates

Input:

Narrative

Files

Metadata

Question pack

Process:

Conversational loop

Entity extraction

Coverage validation

Summary generation

Client validation

Output:

Case Perspective

Transcript

Coverage status

Dashboard signal

Audit events

Customer:

Attorney

Processing Lane

Downstream agents

18. Acceptance Criteria

Coverage thresholds enforceable

Validation required before progression

Immutable transcript storage verified

Versioned artifact supersession working

19. Human Presentation Lens

(Condensed but consistent with your prior version — can reuse full narrative)

The INTERVIEW_AGENT is a governed AI-assisted intake engine that transforms client storytelling into a structured, validated Case Perspective before legal decisions are made, while preserving full attorney authority and control.

It reduces intake variability, improves risk assessment, and creates defensible intake governance.

AI structures information.
Humans make decisions.

Here is your clean, production-ready copy for:

---

# **20. Legal-Element Intake Architecture (CACI + Evidence Overlay)**

---
20.0 Case Strategy Abstraction Layer

The INTERVIEW_AGENT operates under a burden-aware strategy model.
Before element-based questioning begins, the agent must determine the strategic posture of the case.

This abstraction ensures the system supports:

Civil plaintiff matters

Civil defense matters

Criminal defense matters

Criminal prosecution analysis (if applicable)

Multi-firm, multi-domain usage

The agent does not assume that the client is attempting to prove a claim.
Instead, it first determines:

20.0.1 Domain Classification

The agent identifies the legal domain:

Civil

Criminal

Administrative

Regulatory

This classification governs which instruction sets, statutory structures, and evidentiary standards apply.

20.0.2 Party Posture Determination

The agent determines the client’s posture:

Plaintiff / Claimant

Defendant / Respondent

Prosecutor

Criminal Defendant

This determines whether the strategy is:

Building elements

Attacking elements

Raising affirmative defenses

Suppressing evidence

Mitigating exposure

20.0.3 Burden Allocation Identification

The agent identifies which party bears the burden of proof and at what standard:

Preponderance of the evidence

Clear and convincing evidence

Beyond a reasonable doubt

Mixed burdens (affirmative defenses, procedural bars, etc.)

The burden model determines how the element matrix is interpreted.

20.0.4 Strategic Objective Inference

Based on domain and posture, the agent identifies the likely strategic objective:

Prove each required element

Identify weaknesses in opposing party’s case

Raise procedural defenses

Seek dismissal

Suppress evidence

Negotiate settlement

Mitigate sentencing

The strategic objective modifies question sequencing, evidence prioritization, and matrix interpretation.

20.0.5 Strategy-Driven Element Interpretation

All downstream element-based logic (Sections 20.1–20.15) operates within the selected strategic mode.

Example:

Civil Plaintiff Mode:

Element status reflects proof sufficiency.

Civil Defendant Mode:

Element status reflects weakness or contestability.

Criminal Defense Mode:

Element status includes suppression potential and constitutional risk indicators.

The element structure remains consistent.
The interpretation and scoring logic adapt to posture and burden.

20.0.6 Architectural Constraint

The INTERVIEW_AGENT must never:

Assume the client bears the burden without verification.

Present strategic posture as a legal conclusion.

Confuse domain logic (e.g., civil burden applied to criminal matters).

All strategic mode selections must be logged and auditable.

---

## 20.1 Purpose of Upgrade

This section upgrades the INTERVIEW_AGENT from narrative intake to structured, element-aware legal intake.

The agent must:

* Capture the client’s story in natural language.
* Infer likely civil cause(s) of action (COA).
* Structure follow-up questions around required legal elements (CACI-derived).
* Capture potential supporting evidence.
* Flag evidentiary risks using high-level Evidence Code heuristics.
* Produce an element-by-element completeness matrix for attorney review.
* Maintain full audit logging and deterministic output structure.

This upgrade does not replace prior governance, lane rules, rerun rules, or Human Presentation Lens content. It enhances the internal reasoning and intake structure only.

---

## 20.2 Core Legal Principle (Element-Based Proof)

In civil litigation, a plaintiff must prove each required element of a claim by a preponderance of the evidence. Failure to establish any required element may result in dismissal or loss.

Accordingly, the INTERVIEW_AGENT does not attempt to determine case outcome. Instead, it structures intake around:

* What must be proven (element structure).
* What facts support each element.
* What evidence exists to support those facts.
* Where gaps or weaknesses may exist.

All legal conclusions remain reserved for attorney review.

---

## 20.3 Two-Layer Interview Model

### Layer A — Narrative Intake (Universal)

All interviews begin with open narrative capture:

* Client tells the story in their own words.
* Agent extracts timeline anchors.
* Agent identifies parties, roles, agreements, conduct, and alleged harm.
* Agent establishes high-level case context.

Purpose:

* Generate sufficient signal to infer candidate COAs.
* Preserve the client’s authentic story before structuring.

---

### Layer B — Element-Based Intake (Dynamic)

After candidate COAs are inferred, the agent:

* Loads element templates for relevant causes of action.
* Conducts targeted follow-up questions aligned to required elements.
* Captures supporting facts and potential evidence per element.

The interview strategy is dynamic and case-specific. Not all cases follow the same template.

---

## 20.4 COA Hypothesis Engine

The agent maintains a ranked list of candidate causes of action.

Inputs include:

* Narrative verbs (breach, misrepresentation, injury, termination, reliance, etc.).
* Relationship signals (employer/employee, landlord/tenant, vendor/customer, etc.).
* Harm patterns (financial loss, physical injury, reputational damage).
* Document cues (contract, invoice, email, termination letter, text messages).

Outputs:

* COA_CANDIDATES: ranked list with confidence score.
* Short rationale summary for each candidate.

Rules:

* The agent never presents COA identification as a legal determination.
* All COA hypotheses are labeled as preliminary and subject to attorney review.

---

## 20.5 Element Template Loader (CACI)

For each candidate COA, the agent loads a structured element template derived from California Civil Jury Instructions.

Each template includes:

* element_id
* element_name
* plain_language_definition
* required_fact_types
* typical_evidence_types
* burden_standard
* follow_up_prompt_set

The template governs how follow-up questions are structured.

The agent uses element structure to guide questioning but does not reproduce jury instructions verbatim.

---

## 20.6 Question Tree Engine

Each element triggers a structured question tree:

* Primary direct question.
* Clarifying probes.
* Timeline verification prompts.
* Contradiction detection prompts.
* Evidence request prompts.

Adaptation rules:

* If the client lacks legal vocabulary, the agent translates into plain language.
* If answers are vague, the agent narrows scope.
* If inconsistencies appear, the agent pauses and reconciles before proceeding.

The question engine is reasoning-based but outputs are schema-validated.

---

## 20.7 Evidence Overlay Engine

For each fact asserted, the agent captures associated evidence types, including:

* Written documents (contracts, emails, texts, invoices).
* Digital media (screenshots, photos, video).
* Witnesses (participants, third-party observers).
* System records (logs, financial statements).
* Physical evidence.

The agent applies high-level evidentiary heuristics aligned to Evidence Code principles, including:

* Hearsay risk (statement offered for truth without direct testimony).
* Authentication needs (digital artifacts).
* Relevance concerns.
* Privilege risk categories.
* Foundation gaps.

The agent does not determine admissibility. It flags potential issues for attorney evaluation.

---

## 20.8 Element Completeness Matrix

For each candidate COA, the agent produces an element-by-element matrix including:

* Element status: SUPPORTED | PARTIAL | MISSING | CONTRADICTED | UNKNOWN
* Linked fact identifiers.
* Linked evidence identifiers.
* Associated risk flags.
* Recommended follow-up actions.

Additionally, the agent provides:

* Strongest supported elements.
* Weakest or unsupported elements.
* Critical gaps.
* Efficient next-step suggestions (non-legal advisory).

This matrix is the primary attorney-facing structured artifact.

---

## 20.9 Scoring & Prioritization

Internal scoring mechanisms may include:

* Element coverage score.
* Evidence density score.
* Risk burden score.
* Contradiction score.

These scores are workflow prioritization tools only and are not presented as legal conclusions.

Attorney-facing outputs use qualitative descriptors rather than numeric predictions.

---

## 20.10 Attorney Gate

After matrix generation, the system requires attorney review.

Available actions:

* ACCEPT intake.
* DECLINE intake.
* REQUEST FOLLOW-UP.
* RERUN (governed by rerun levels).
* REFRAME COA.

No downstream automation proceeds without passing the attorney gate.

---

## 20.11 Outputs

The INTERVIEW_AGENT emits:

1. Narrative summary.
2. Structured timeline anchors.
3. Party and entity map.
4. Ranked COA candidate list.
5. Element completeness matrix.
6. Evidence register.
7. Risk flag register.
8. Follow-up plan.
9. Audit ledger entries.

All outputs are schema-validated and linked via canonical identifiers.

---

## 20.12 DIKW Capture

All prompts and responses are logged, including:

* Internal reasoning prompts.
* External web queries (if used).
* Model identifiers.
* Token counts.
* Output hashes.

Attorney decisions are logged to support knowledge promotion.

This enables:

* Pattern recognition over time.
* Template refinement.
* Structured knowledge promotion.

---

## 20.13 Guardrails

The agent must:

* Avoid outcome predictions.
* Avoid legal conclusions.
* Frame all analysis as intake structuring.
* Encourage attorney review.
* Flag potential privilege risks cautiously.
* Escalate unclear or contradictory narratives.

---

## 20.14 Failure Modes

If case type remains unclear:

* Continue narrative intake and request clarification.

If contradictions persist:

* Pause element scoring and reconcile.

If evidence is unavailable:

* Mark as missing and generate follow-up plan.

If client resists structured questioning:

* Re-anchor to narrative and gradually reintroduce structure.

All failure states are logged.

---

## 20.15 Deterministic vs Reasoning Boundaries

Reasoning components:

* Narrative summarization.
* COA inference.
* Dynamic question generation.

Deterministic components:

* Element template structure.
* Matrix formatting.
* Output schema validation.
* Audit logging.
* Canonical identifier assignment.

All outputs must be reproducible under the same input conditions where feasible.

---

This section is architecturally additive and does not modify existing governance, lane definitions, or Human Presentation Lens content.

---

When you are ready, next we should build:

* `caci_elements.yaml` schema structure
* OR `evidence_risk_rules.yaml`
* OR `element_completeness_matrix.json` contract

Your call.
