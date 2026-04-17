# program_COA_ENGINE
(Authoritative Program Contract — v1 | Normalized 19-Section Contract)

---

## 1. Purpose

The COA_ENGINE program evaluates **legal sufficiency coverage** for controlled Causes of Action (COA) by measuring whether each COA element is supported by structured case artifacts.

It produces a deterministic **Element Coverage Matrix** that links:
- COA elements
- supporting EvidenceFacts
- supporting EventCandidates (if available)
- evidence citations (via the referenced facts)

COA_ENGINE is structural and evidentiary. It does not provide legal advice or narrative persuasion.

---

## 2. Architectural Position

Operates after:
- PROCESSING (Documents + Chunks)
- program_FACT_NORMALIZATION (EvidenceFacts available)

Optionally uses:
- program_COMPOSITE_ENGINE outputs (EventCandidates)
- program_TAGGING outputs (filters/features)
- MAPPING_AGENT outputs (graph edges / story alignment) as supporting signals

Produces artifacts consumed by:
- Attorney review and planning workflows
- Query Answering (COA element retrieval)
- Optional COA_REASONER agent (narrative layer)
- Discovery planning tools (interrogatories, RFPs, deposition outlines)

All writes occur via Write Broker (Section 7 compliant).

---

## 3. Execution Modes

### 3.1 Reasoning Mode

Not Applicable (Program).

Reasoning Mode is required only for Agents.

### 3.2 Deterministic Mode

The program SHALL:
- Load the case’s authoritative COA taxonomy and element definitions
- Evaluate coverage of each element using deterministic rules and thresholds
- Link each element to supporting fact_ids and event_candidate_ids
- Flag gaps, conflicts, and ambiguities
- Emit reproducible outputs given identical inputs, taxonomies, and ruleset versions

The program SHALL NOT invent evidence or fabricate support.

---

## 4. Triggers & Entry Conditions

### Trigger Events
- FACT_NORMALIZATION_COMPLETE
- COMPOSITE_COMPLETE (optional)
- TAGGING_COMPLETE (optional)
- COA_TAXONOMY_UPDATED
- COA_RULESET_UPDATED
- NEW_EVIDENCE_ADDED
- MAPPING_UPDATED (optional)

### Entry Conditions
Required:
- COA taxonomy exists for the case (controlled vocabulary + element model)
- EVIDENCE_FACTS.json exists
- COA_RULESET.json exists (versioned)

Optional:
- EVENT_CANDIDATES.json
- TAG_ASSIGNMENTS.json
- GRAPH_EDGES.json / mapping outputs

---

## 5. Preconditions (Governance)

COA taxonomy is attorney-governed and case-scoped:
- Attorneys own and approve COA set and element definitions
- All taxonomy versions must be traceable and version-locked

No human approval is required to execute COA_ENGINE once inputs exist.

---

## 6. Responsibilities

The program SHALL:
1. Load COA taxonomy (COAs + element definitions + required conditions)
2. Evaluate each element against:
   - EvidenceFacts (direct support)
   - EventCandidates (contextual support when configured)
   - optional tag/mapping signals (filters/features only)
3. Assign an element coverage status:
   - Supported
   - Partially Supported
   - Unsupported
   - Conflicted
4. Produce an **Element Coverage Matrix** linking:
   - element_id
   - status
   - supporting_fact_ids
   - supporting_event_candidate_ids (optional)
   - confidence score
   - conflict flags + reason codes
5. Produce gap reports and coverage summaries at COA and case level

---

## 7. Non-Goals (Explicit Exclusions)

COA_ENGINE SHALL NOT:
- Provide legal advice
- Generate persuasive narrative arguments
- Draft pleadings or motions
- Decide “who wins”
- Create new facts or events
- Override attorney-defined COA elements
- Treat tags as proof (tags are filters only)

Narrative synthesis belongs to an optional COA_REASONER agent.

---

## 8. Inputs (Canonical Only)

Required:
- COA_TAXONOMY.json (case-scoped, attorney-governed)
- COA_RULESET.json (versioned; deterministic)
- EVIDENCE_FACTS.json
- DOCUMENT_HASH_INDEX.json

Optional:
- EVENT_CANDIDATES.json
- TAG_ASSIGNMENTS.json
- GRAPH_EDGES.json (mapping output)
- ENTITY_RESOLUTION indexes

All inputs must be hash-verifiable.

---

## 9. Outputs (Versioned Artifacts)

Authoritative outputs:
- COA_ELEMENT_COVERAGE_MATRIX.json
- COA_COVERAGE_REPORT.json
- COA_PROVENANCE_LOG.json

Matrix entries MUST include:
- coa_id
- element_id
- status (supported|partial|unsupported|conflicted)
- supporting_fact_ids
- supporting_event_candidate_ids (optional)
- confidence (0–1)
- reason_codes (deterministic labels)
- conflict_flags
- provenance fields (case_id, run_id, contract_version, taxonomy_version, ruleset_version, timestamp_utc)

Outputs are supersession-based; prior versions retained.

---

## 10. Blocking Authority

Blocks downstream COA-dependent workflows when configured:
- attorney “COA coverage” dashboards
- discovery planning automation relying on element gaps
- query answering modes that target element-level support

Does not block basic evidence retrieval.

---

## 11. Human Interaction Points

None required for execution.

Attorney/staff UI may provide:
- coverage dashboards
- element gap drilldowns
- conflict inspection
- “what evidence supports this element?” navigation via citations

---

## 12. Interacting Agents / Programs

Upstream:
- PROCESSING
- program_FACT_NORMALIZATION
- (optional) program_TAGGING
- (optional) program_COMPOSITE_ENGINE
- (optional) MAPPING_AGENT outputs

Downstream:
- attorney review workflows
- Query Answering / Retrieval
- optional COA_REASONER agent (narrative explanation layer)
- discovery planning tools

---

## 13. Failure Classification

Blocking failures:
- Missing COA taxonomy or invalid schema
- Missing EvidenceFacts
- Missing COA_RULESET
- Hash mismatch / drift
- Write Broker rejection

Non-blocking failures:
- Low-confidence support associations
- Conflicts detected but not resolvable deterministically
- Optional inputs missing (events, tags, mapping)

Non-blocking issues must be recorded in COA_COVERAGE_REPORT.

---

## 14. Determinism, Reproducibility & Rerun Policy

- Deterministic evaluation required
- Rule application must be fully versioned (COA_RULESET)
- Same inputs + same taxonomy + same ruleset = identical matrix outputs
- Rerun required upon:
  - EvidenceFacts change
  - COA taxonomy change
  - COA_RULESET change
  - EventCandidates change (if used)

---

## 15. Learning & Governance

- No self-modification
- COA taxonomy changes require attorney approval
- COA_RULESET changes require governed PR approval
- Optional ML/LLM support (if ever added) must remain non-authoritative and cannot set element status

---

## 16. Pristine Data Policy

- No mutation of raw evidence
- No mutation of EvidenceFacts
- All writes mediated via Write Broker
- Audit ledger events required for execution + writes

---

## 17. SIPOC

Supplier:
- Attorney-governed COA taxonomy
- program_FACT_NORMALIZATION
- (optional) program_COMPOSITE_ENGINE
- (optional) MAPPING_AGENT outputs

Input:
- COA definitions + deterministic rules
- EvidenceFacts (+ optional EventCandidates)

Process:
- element evaluation
- evidence linking
- conflict detection
- matrix/report creation

Output:
- Element Coverage Matrix
- Coverage report + provenance log

Customer:
- attorneys/staff
- query answering
- discovery planning
- optional COA_REASONER agent

---

## 18. Acceptance Criteria

The program is compliant when:
- Every element status is supported by explicit supporting_fact_ids and/or event_candidate_ids
- No element is marked supported without evidence citations via facts
- Outputs reproducible across reruns with identical inputs/taxonomy/ruleset
- Artifacts versioned and hash-locked via manifest
- Coverage report includes gap and conflict summaries
- Tags are used only as filters/features, not as proof

---

## 19. Human Presentation Lens

COA_ENGINE converts complex evidence into a structured view of legal sufficiency.

It helps attorneys see, element-by-element, what is supported, what is missing, and where conflicts exist—without replacing legal judgment.

The system measures coverage.
Humans decide strategy.
Evidence remains the authority.