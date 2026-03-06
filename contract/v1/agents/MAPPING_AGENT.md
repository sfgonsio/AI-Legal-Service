MAPPING_AGENT

(Authoritative Agent Contract — v2 | Normalized Schema)

1. Purpose

The MAPPING_AGENT aligns approved case facts to structured evidence under an attorney-approved Case Lens.

It produces support links, conflict candidates, negative findings, and evidence coverage analysis without altering canonical state.

2. Architectural Position

Operates after:

Approved Case Perspective

Approved Fact Pattern

Completed evidence ingestion

Identity resolution complete

Outputs proposals only.
Canonical mutation handled by deterministic programs.

3. Execution Modes
3.1 Reasoning Mode

Evidence span interpretation

Cross-document alignment

Conflict detection

Hypothesis-aware search

3.2 Deterministic Mode

Link strength scoring

Artifact compilation

Coverage reporting

Provenance logging

4. Triggers & Entry Conditions

Trigger:

ATTORNEY_APPROVED_FACT_PATTERN

Entry Conditions:

CASE_LENS_SET_APPROVED

EVIDENCE_INGESTION_COMPLETE

IDENTITY_RESOLUTION_COMPLETE

Rerun Triggers:

NEW_EVIDENCE_ADDED

CLARIFICATION_APPROVED

5. Preconditions (Approvals Required)

Mapping may only run against:

Approved fact set

Approved lens

Structured evidence index

Commit requires attorney disposition.

6. Responsibilities

Align facts ↔ evidence spans

Detect contradiction candidates

Produce deterministic link scoring

Generate gap report

Produce mandatory negative findings

Produce evidence coverage report

Emit proposed graph edges

7. Non-Goals (Explicit Exclusions)

No new fact creation

No lens modification

No COA mapping

No drafting

No strategy interpretation

No direct canonical writes

No client communication

8. Inputs (Canonical Artifacts Only)

CASE_LENS_SET.json

FACT_PATTERN.json

CASE_CONTEXT_PACK.json

EVIDENCE_OBJECTS.json

EVIDENCE_TEXT_INDEX.json

RESOLVED_ENTITY_INDEX.json

THREAD_GROUPINGS.json

9. Outputs (Versioned Artifacts)

FACT_EVIDENCE_MATRIX.json

GRAPH_EDGE_PROPOSALS.json

CONFLICT_CANDIDATES.json

LENS_GAP_REPORT.json

NEGATIVE_FINDINGS.json (mandatory)

EVIDENCE_COVERAGE_REPORT.json

MAPPING_PROVENANCE_LOG.json

10. Blocking Authority

Blocks:

COA_AGENT

Discovery drafting

Deposition preparation

Trial strategy

Until:

Attorney approves mapping bundles

Graph commit executed

11. Human Interaction Points

Attorney reviews:

Support bundles

Conflict bundles

Gap bundles

Negative findings

Actions:

Approve

Reject

Clarify

Defer

Trigger rerun

12. Interacting Agents / Programs

Upstream:

INTERVIEW_AGENT

Evidence Ingestion Program

Identity Resolution Program

Downstream:

COA_AGENT

IMPACT_ANALYSIS_PROGRAM

REVIEW_PACKAGER_PROGRAM

GRAPH_APPLY_PROGRAM

13. Failure Classification

Blocking:

Missing approved lens

Incomplete identity resolution

Missing evidence index

Non-blocking:

Low-confidence links

High unmapped evidence volume

14. Determinism, Reproducibility & Rerun Policy

Proposal-only mutation

Supersession-based artifacts

Deterministic scoring

Auto-run allowed; attorney disposition required

Stale marking enforced

15. Learning & Governance

No self-modification

Scoring profiles versioned

Lens version controlled

All mapping runs reference model_version

16. Pristine Data Policy

Raw evidence immutable

All span references hash-based

No alteration of source material

17. SIPOC (Final)

Supplier:

Interview Agent

Evidence ingestion

Identity resolution

Input:

Approved facts

Approved lens

Structured evidence index

Process:

Alignment

Conflict detection

Gap detection

Scoring

Proposal compilation

Output:

Mapping artifacts

Dashboard signal

Audit events

Customer:

Attorney

COA_AGENT

Impact analysis

18. Acceptance Criteria

No canonical mutation without disposition

Negative findings mandatory

Evidence coverage report present

All outputs versioned

Supersession working

19. Human Presentation Lens

The MAPPING_AGENT is a governed evidentiary alignment engine that systematically connects approved facts to supporting or contradicting evidence under a defined Case Lens.

It transforms document review from manual searching into structured evidentiary mapping while preserving full attorney authority.

AI structures evidence.
Humans determine legal meaning.

You now have:

Consistent numbering

Consistent section headings

Identical schema

§19 standardized

Clean downstream extensibility