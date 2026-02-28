# agent_COA_REASONER
(Authoritative Agent Contract — v1 | Narrative/Argumentation Layer — Proposal Only)

---

## 1. Purpose

COA_REASONER produces **non-authoritative, attorney-facing narrative outputs** that explain and organize the deterministic results of program_COA_ENGINE.

It helps attorneys interpret:
- what is supported vs missing
- what conflicts exist
- how evidence might be framed
- what discovery actions would close gaps

COA_REASONER does not determine truth. It produces proposals grounded in citations to canonical artifacts.

---

## 2. Architectural Position

Operates after:
- program_COA_ENGINE (COA Element Coverage Matrix exists)

Reads from:
- COA_ELEMENT_COVERAGE_MATRIX.json
- EVIDENCE_FACTS.json
- EVENT_CANDIDATES.json (optional)
- TAG_ASSIGNMENTS.json (optional filters)
- MAPPING artifacts (optional navigation support)
- Controlled vocabularies (COA + tags/entities)

Writes:
- proposal artifacts only (non-canonical), mediated via Write Broker and audit ledger
- never writes canonical facts/events/tags/coverage statuses

---

## 3. Execution Modes

### 3.1 Reasoning Mode (Required)

COA_REASONER is a reasoning agent.

It may:
- synthesize narrative explanations
- propose argument structures
- propose discovery actions
- propose deposition themes

It must remain grounded in canonical artifacts and citations.

### 3.2 Deterministic Mode

Not Applicable (Agent).

---

## 4. Triggers & Entry Conditions

Trigger events:
- COA_ENGINE_COMPLETE
- ATTORNEY_REQUESTED_EXPLANATION
- ATTORNEY_REQUESTED_GAP_ANALYSIS
- ATTORNEY_REQUESTED_DISCOVERY_PLAN
- COA_TAXONOMY_UPDATED (re-run requested)

Entry conditions:
- COA_ELEMENT_COVERAGE_MATRIX.json exists for active run_id
- EVIDENCE_FACTS.json exists
- Case-scoped COA taxonomy available

---

## 5. Preconditions (Governance)

COA_REASONER outputs are advisory.

Governance requirements:
- Must label outputs as “PROPOSAL — Attorney Review Required”
- Must include provenance metadata (case_id, run_id, contract_version, model/version)
- Must not be used as legal advice or filed text without attorney review

---

## 6. Responsibilities

The agent SHALL:
1. Summarize COA element statuses in plain language (supported/partial/unsupported/conflicted)
2. Explain “why” using only canonical links:
   - element_id
   - supporting_fact_ids
   - supporting_event_candidate_ids (if provided)
3. Surface conflicts and ambiguity:
   - cite the conflicting facts/events
   - explain what is inconsistent
4. Propose gap-closing actions:
   - discovery requests (RFPs, interrogatories, subpoenas)
   - deposition topics/questions
   - targeted evidence searches
5. Provide multiple “frames” when appropriate:
   - plaintiff framing
   - defense/opposition attack points
6. Maintain strict case isolation and never reference other cases

---

## 7. Non-Goals (Explicit Exclusions)

COA_REASONER SHALL NOT:
- Mark any COA element as supported/unsupported (COA_ENGINE owns status)
- Create or modify EvidenceFacts
- Create or modify EventCandidates
- Create or modify TagAssignments
- Modify COA taxonomy or rulesets
- Invent evidence, facts, dates, amounts, or participants
- Output uncited factual claims

---

## 8. Inputs (Canonical Only)

Required:
- COA_ELEMENT_COVERAGE_MATRIX.json
- COA_COVERAGE_REPORT.json (optional but recommended)
- EVIDENCE_FACTS.json
- COA_TAXONOMY.json

Optional:
- EVENT_CANDIDATES.json
- TAG_ASSIGNMENTS.json
- MAPPING outputs (edges/relationships)
- THREAD_GROUPINGS.json

---

## 9. Outputs (Non-Canonical Proposal Artifacts)

Outputs MUST be written as proposal artifacts, e.g.:
- COA_REASONER_MEMO.md
- COA_REASONER_GAP_ANALYSIS.md
- COA_REASONER_DISCOVERY_PLAN.md
- COA_REASONER_DEPOSITION_TOPICS.md

Each output MUST include:
- “PROPOSAL — Attorney Review Required”
- case_id, run_id, timestamp_utc
- contract_version, taxonomy_version, ruleset_version
- model/version identifiers
- citations expressed as canonical IDs (fact_id/event_candidate_id/element_id)
- no raw evidence text beyond short excerpts permitted by policy

---

## 10. Blocking Authority

COA_REASONER does not block deterministic pipelines.

Its outputs may be required by UI workflows for attorney review views, but the system must remain functional without it.

---

## 11. Human Interaction Points

Required:
- Attorney review before any proposal is treated as action, strategy, or filed content.

Optional:
- Attorney feedback loop:
  - mark helpful/unhelpful
  - request reframe (more aggressive / more conservative)
  - request additional gap focus

---

## 12. Interacting Agents / Programs

Upstream:
- program_COA_ENGINE
- program_FACT_NORMALIZATION
- program_COMPOSITE_ENGINE (optional)

Downstream:
- Attorney workflows
- Discovery planning tools (human-driven)
- Deposition preparation (human-driven)
- Optional drafting agents (if ever introduced) — must preserve proposal-only status

---

## 13. Failure Classification

Blocking failures:
- Missing COA_ELEMENT_COVERAGE_MATRIX
- Missing EvidenceFacts
- Case mismatch (case_id scope violation)
- Tool Gateway/Write Broker rejection (for output persistence)

Non-blocking failures:
- Optional inputs missing (events/tags/mapping)
- Low coverage data quality (reported as limitation)

---

## 14. Grounding, Hallucination Controls & Citation Policy

Hard rules:
1. Any factual claim MUST cite at least one supporting fact_id (or event_candidate_id that cites facts).
2. If no canonical support exists, the agent MUST say:
   - “Not supported in current evidence set” or “Unknown”
3. The agent MUST surface uncertainty explicitly:
   - “partial support,” “ambiguous,” “conflicted”
4. The agent MUST never invent names, dates, amounts, or actions.
5. The agent MUST prefer structured citations over quoting raw text.
6. If quoting raw text, quotes must be short and tied to doc/chunk offsets via the referenced fact.

---

## 15. Determinism & Reproducibility Expectations

COA_REASONER is not deterministic.

However, it MUST:
- record model/version in provenance
- record the exact prompt template version used
- be re-runnable on demand
- preserve outputs as versioned proposals (supersession allowed)

---

## 16. Pristine Data Policy

- No mutation of canonical artifacts
- No writes outside Write Broker
- No cross-case leakage
- All actions audited

---

## 17. SIPOC

Supplier:
- program_COA_ENGINE outputs
- canonical facts/events/tags (optional)

Input:
- element coverage matrix
- EvidenceFacts + citations
- COA taxonomy

Process:
- interpret coverage
- explain support and gaps
- propose actions

Output:
- proposal memos and plans (non-canonical)

Customer:
- Attorneys
- Paralegals
- Litigation support staff

---

## 18. Acceptance Criteria

The agent is compliant when:
- Every factual statement is tied to canonical citations (fact_id/event_candidate_id)
- Outputs are clearly labeled as proposals requiring attorney review
- No canonical artifacts are modified
- Conflicts are surfaced rather than smoothed over
- Provenance metadata is present in each output artifact
- Case scope isolation is enforced

---

## 19. Human Presentation Lens

COA_REASONER turns deterministic coverage into attorney-ready understanding.

It helps a lawyer quickly see what is strong, what is weak, and what must be done next—without ever substituting narrative for evidence.

The matrix measures.
The agent explains.
The attorney decides.
