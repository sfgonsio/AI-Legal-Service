# Agent Contract Template v1 — SSOT (Contract v1)

**Status:** Template (canonical)  
**Applies To:** All reasoning agents in Contract v1  
**Contract Supremacy:** This text is SSOT and supersedes all visuals.  
**Version:** v1  
**Last Updated:** YYYY-MM-DD  
**Owner:** Product / Architecture  
**Reviewers:** Legal (Attorney), Engineering, Ops  
**Hash-Locked:** Yes (tracked in `contract_manifest.yaml`)

---

## 1. Purpose

### 1.1 Agent Name
**{AGENT_NAME}**

### 1.2 Mission Statement
One paragraph: what the agent does, and what “done” looks like.

### 1.3 Non-Goals (Explicitly Out of Scope)
Bullet list of what this agent will not do (prevents scope creep).

---

## 2. Operating Constraints

### 2.1 Determinism Rule
- This agent is **non-deterministic** by nature (reasoning).  
- Any output that must be reproducible or legally defensible **must be produced by a deterministic program** or stored as a versioned artifact with provenance.

### 2.2 Tool Access Rule (Gateway Only)
- The agent **MUST NOT** call external tools directly.  
- The agent may only request tools via the **Tool Gateway** using approved tool IDs in the tool registry.  
- All tool requests and responses are logged to the audit ledger with input/output fingerprints.

### 2.3 Evidence-Only Rule
- All factual claims must be traceable to:
  - Evidence Vault objects (Doc_UID / Chunk_UID / Exhibit_UID), and/or
  - Approved authoritative knowledge objects (see §11) with citations and version IDs.
- No “common knowledge” legal claims without a source object.

---

## 3. Inputs

### 3.1 Required Inputs (Contract)
List required inputs with types and source:
- `case_id` (string)
- `jurisdiction` (enum)
- `evidence_scope` (object: filters)
- `prior_outputs` (object: references to earlier artifacts)

### 3.2 Optional Inputs
- `attorney_instructions` (string)
- `timebox_minutes` (int)
- `risk_tolerance` (enum)

### 3.3 Input Validation Rules
What must be present, what must be rejected, what triggers a human checkpoint.

---

## 4. Outputs

### 4.1 Primary Output Artifacts
Define the **named** artifacts the agent produces (references only; actual storage performed by deterministic program):
- `{AGENT_NAME}_findings.md`
- `{AGENT_NAME}_recommendations.json`
- `{AGENT_NAME}_issues.csv` (optional)

### 4.2 Output Schema (Minimum Fields)
Define a minimal JSON schema shape (high-level, not formal JSON Schema), e.g.:
- `summary`
- `items[]`
  - `claim`
  - `confidence`
  - `supporting_evidence[]` → `{Doc_UID, Chunk_UID, quote_span, relevance_note}`
  - `assumptions[]`
  - `open_questions[]`

### 4.3 Quality Bar
- Must include explicit **assumptions**
- Must include explicit **unknowns**
- Must include explicit **next actions**
- Must include **evidence links** for each material claim

---

## 5. Core Responsibilities

Bullet list of what the agent must do every run, in order of importance.

Example pattern:
1. Read case context and constraints
2. Pull relevant evidence references
3. Produce structured findings with provenance
4. Identify gaps and propose next steps
5. Flag human approvals needed

---

## 6. Workflows and State Transitions

### 6.1 Entry Criteria
What must be true before this agent is invoked.

### 6.2 Steps (Happy Path)
Numbered sequence of the agent’s internal steps.

### 6.3 Exit Criteria
What constitutes completion.

### 6.4 Failure Modes
- Missing evidence
- Conflicting facts
- Unapproved tool requested
- Low confidence / insufficient support
Each must map to an action: retry, escalate, or human checkpoint.

---

## 7. Attorney Checkpoints

Define where human review is required:
- **Approval Gate A:** {what is being approved}
- **Approval Gate B:** {what is being approved}

Include:
- what the attorney sees
- what they approve/reject
- what gets logged

---

## 8. Audit and Provenance Requirements

### 8.1 Required Provenance Keys
Every material item must reference:
- `case_id`
- `Doc_UID` and/or `Chunk_UID` (and exhibit identifiers if used)
- `source_type` (evidence | authoritative_knowledge | attorney_directive)
- `timestamp`
- `agent_version`
- `contract_version`

### 8.2 Audit Events (Minimum Set)
List the audit events this agent must emit (names should align with `audit_events` lanes):
- `agent_run_started`
- `tool_request_submitted`
- `tool_response_received`
- `agent_output_drafted`
- `attorney_review_requested` (if applicable)
- `agent_run_completed`
- `agent_run_failed` (if applicable)

---

## 9. Tool Requests

### 9.1 Allowed Tools (By Tool ID)
List tool IDs from tool registry this agent can request, with reasons.
- `tool.search_legal_library` (example)
- `tool.retrieve_doc` (example)

### 9.2 Disallowed Tools
Explicit list (prevents drift).

### 9.3 Tool Request Format
Describe the expected tool request envelope fields:
- `tool_id`
- `purpose`
- `inputs`
- `case_id`
- `requester` = `{AGENT_NAME}`
- `correlation_id`

---

## 10. Rerun Governance

### 10.1 Rerun Levels
Declare what rerun levels the agent is permitted to trigger and what requires attorney approval.

Example:
- **R0–R2:** Agent rephrase / reorganize only (no new tools)
- **R3–R4:** New tool calls within approved set (auto-logged)
- **R5+:** Requires attorney approval (expands scope, new sources, new strategy)

### 10.2 Drift Controls
- No modifications to canonical schemas
- No modifications to authoritative knowledge objects without approval + version bump
- Any deviation must be logged and flagged

---

## 11. Authoritative Knowledge Objects (Future-Proof Hook)

This section exists now so Stage 15 can snap in cleanly.

### 11.1 What Counts as Authoritative
Examples:
- Jury instructions library objects
- Evidence code objects
- Court rules objects
- Approved case law/precedent objects (with citation + retrieval metadata)

### 11.2 Storage + Versioning Contract
- Each knowledge object has an ID, version, jurisdiction, and citations.
- Objects are created/updated only through a governed pipeline with attorney approval.
- The agent may **reference** objects; it may not create/update them directly.

---

## 12. Human Presentation Lens (Required)

This is the “attorney-facing explanation layer.” No jargon.

### 12.1 What This Agent Does (Plain English)
2–5 bullets.

### 12.2 What This Agent Does *Not* Do
2–5 bullets.

### 12.3 Inputs It Needs From You
- What you provide (e.g., documents, case posture, objectives)

### 12.4 What You Get Back
- What artifacts are produced and how to use them.

### 12.5 Trust & Safety / Defensibility
- Where claims come from (evidence + citations)
- What gets logged
- What requires attorney approval

### 12.6 Example Run (Mini Walkthrough)
5–10 lines showing:
Input → tool request (if any) → outputs → attorney checkpoint.

---

## 13. Acceptance Tests (Golden Workflow Hooks)

### 13.1 Golden Inputs
Reference sample payload(s) in harness folder.

### 13.2 Expected Outputs (Qualitative + Structural)
- Must produce required fields
- Must link evidence for material claims
- Must emit audit events

### 13.3 Regression Criteria
What constitutes failure in CI / harness runs.

---

## 14. Change Log
- v1: Initial canonical template