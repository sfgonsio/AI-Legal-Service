# agent_RESEARCH_AGENT
**Contract Version:** v1  
**Agent Role:** Student Researcher (Discovery + Authority Capture)  
**Layer:** Brain (Post-Spine Baseline v1.0-spine-stable)  
**Status:** Draft – Brain v1  
**Owner:** Platform SSOT  
**Determinism:** Research activity is non-deterministic; captured artifacts must be deterministic once stored (see §16)

---

## 1) Mission
Operate as a “student” that can roam (within approved boundaries) to discover legal materials (authority, secondary sources, white papers, case summaries), then return structured findings to the “teacher” (attorney) for accept/reject/modify and promotion into trusted knowledge.

---

## 2) Non-Goals
- Does not auto-promote knowledge to trusted.
- Does not silently alter system heuristics/playbooks.
- Does not treat newly found materials as authoritative by default.
- Does not file or finalize legal work product without attorney approval.

---

## 3) Primary Users
- Attorney (teacher / reviewer / approver)
- Litigation support (research coordinator)
- Strategy lead (secondary)

---

## 4) Inputs (Authoritative)
### 4.1 Research Assignment (teacher-provided)
A structured assignment must be provided per run:
- issue_statement (what we are trying to prove/disprove)
- jurisdiction (e.g., CA; federal)
- doc_types requested (e.g., cases, statutes, jury instructions, white papers)
- phase context (discovery, pretrial, trial)
- desired outputs (e.g., “5 cases that undermine element X”)
- constraints (date ranges, court levels, binding vs persuasive preference)

### 4.2 Curriculum (Approved Sources Policy)
- `contract/v1/policy/approved_sources.yaml`
- trusted-only toggle (default: true for authority consumption; research discovery uses policy tiers)

### 4.3 Case Context (optional)
If invoked from OPPOSITION_AGENT or a case workflow:
- COA map + element gaps
- evidence map/facts (to map relevance)

---

## 5) Outputs (Structured)
RESEARCH_AGENT produces a **Research Findings Packet** (candidate-only):

### 5.1 research_findings_packet.json (canonical)
Each finding MUST include:
- finding_id (deterministic from source + citation when possible)
- query_trace (search terms / prompts)
- retrieval_metadata (timestamp, method, source tier)
- source_locator (URL / doc id / citation)
- snapshot_reference (hash or stored artifact id after capture)
- excerpt (short, compliant) OR paraphrase + pinpoint
- normalized_summary (what it says)
- relevance_mapping (coa_id, element_id, issue_tags)
- confidence (and why)
- counterpoint / limitations (non-binding, outdated, jurisdiction mismatch, etc.)
- recommendation: promote | review | discard

### 5.2 teacher_review_queue_item (optional)
A convenience index for UI review:
- grouped findings by issue / COA element
- “promote candidates” shortlist

**All outputs are `candidate` by default.**

---

## 6) Success Criteria
- Produces findings that are:
  - source-linked
  - relevance-mapped to case issues
  - structured for attorney review
- Makes no unsupported authoritative claims.
- Minimizes noise; flags weak sources clearly.

---

## 7) Guardrails & Policy
### 7.1 Curriculum Enforcement
RESEARCH_AGENT may only access sources consistent with `approved_sources.yaml`:
- allowlist domains
- tier rules
- escalation requirements

### 7.2 Citation & Traceability Required
Any “learning” must have:
- source locator
- retrieval metadata
- excerpt/paraphrase with pinpoint
- relevance mapping

No citation → no promotion path.

### 7.3 Candidate-Only Boundary
All discovered materials remain `candidate` until attorney review.

---

## 8) Operating Modes
### 8.1 Guided Assignment Mode (default)
- Teacher provides explicit questions and constraints.
- Agent returns findings packet.

### 8.2 Gap-Driven Mode (case-integrated)
- Agent is provided COA element gaps.
- Agent searches for authorities that:
  - support
  - undermine
  - limit
  those elements.

### 8.3 Source-Tier Mode
- Tier 1 only (official authority)
- Tier 1–2 (authority + reputable secondary)
- Tier 1–3 (broad, with warnings)

---

## 9) Core Reasoning Steps (Student Workflow)
1. Parse assignment + constraints.
2. Load curriculum policy and enforce tiers/domains.
3. Generate search plan (queries + coverage targets).
4. Retrieve candidate sources and record query_trace.
5. Extract minimal excerpt or paraphrase with pinpoint.
6. Produce normalized summaries and map to issues/COA elements.
7. Flag limitations and counterpoints.
8. Emit research_findings_packet.json.

---

## 10) Tools (Through Tool Gateway Only)
RESEARCH_AGENT may only call tools explicitly permitted by lanes/tool registry.
Typical tool categories:
- research.search (domain/tier constrained)
- retrieval.fetch_document (approved sources only)
- extract.parse_pdf/text (local parsing)
- capture.request (hands off to program_RESEARCH_CAPTURE)
- export.bundle_writer

No direct network calls outside the gateway.

---

## 11) Teacher Review & Feedback Loop
RESEARCH_AGENT must support the teacher actions:
- Accept → promote candidate to reviewed/trusted via promotion gate
- Reject → mark as discarded with reason
- Modify → teacher edits summary, citation, mapping, or limitations

Teacher feedback is stored as:
- teacher_notes
- correction flags
- final classification

---

## 12) Audit Ledger Events (Must Log)
- research_agent_run_started
- research_agent_query_executed (query_trace + tier)
- research_agent_source_discovered (locator + tier)
- research_agent_packet_emitted (artifact ids)
- research_agent_escalation_requested (if tier/domain escalation)

---

## 13) Failure Modes & Safe Degradation
If sources are blocked by policy:
- produce a packet with “blocked” items + escalation requests.

If retrieval fails:
- log failure + provide alternate query suggestions.

If case context missing:
- still return findings; mapping becomes issue_tags only.

---

## 14) Output Files (Canonical Locations)
- artifacts/research/research_findings_packet.json
- artifacts/research/research_findings_summary.md (human-readable)

All artifacts must include:
- run_id
- timestamp
- policy_snapshot_id (hash of approved_sources.yaml)
- (optional) knowledge_snapshot_id if trusted knowledge referenced

---

## 15) Relationship to Knowledge Contract v1
RESEARCH_AGENT generates **candidate knowledge** only.
Promotion is governed by Knowledge Contract v1 and attorney approval.

---

## 16) Determinism & Replay Requirements
Research discovery is non-deterministic by nature.

However:
- Once a source is captured (program_RESEARCH_CAPTURE),
  the captured artifact + hashes become deterministic.
- Replay equivalence should validate:
  - the same captured artifacts were used
  - the same policy snapshot was enforced
  - the same trusted knowledge snapshot was referenced (if any)

---

## 17) Acceptance Tests (Brain v1)
Minimum acceptance:
- Given a research assignment, outputs ≥ 5 findings with:
  - locator + tier
  - summary + limitations
  - relevance mapping
  - recommendation
- 100% findings have query_trace metadata
- 0% findings are treated as trusted without promotion

---

## 18) Open Questions (Tracked)
- Do we allow “prompt discovery” beyond whitelisted domains under an escalation workflow?
- What is the firm’s preferred case-law provider (Lexis/Westlaw/library portal)?
- Do we maintain “attorney style guides” per firm/practice group?

---

## 19) Human Presentation Lens (Attorney-Friendly Narrative)
RESEARCH_AGENT is your junior associate who:
- searches within a controlled reading list,
- returns structured case law/authority findings,
- shows the work (sources + caveats),
- and asks you to approve what becomes “real knowledge” for future runs.

The system learns only what you approve.