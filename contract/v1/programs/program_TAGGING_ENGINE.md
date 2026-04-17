# program_TAGGING
(Authoritative Program Contract — v1 | Normalized 19-Section Contract)

---

## 1. Purpose

The TAGGING program applies **authoritative, deterministic** tags from controlled vocabularies to case artifacts (documents, chunks, EvidenceFacts, EventCandidates, and graph edges where applicable).

Tags are an indexing and filtering layer used to improve retrieval, triage, and governance. Tags are **not proof** and do not create legal meaning.

---

## 2. Architectural Position

Operates after:
- PROCESSING (Documents + Chunks)
- program_FACT_NORMALIZATION (EvidenceFacts available)

May operate before or after:
- program_COMPOSITE_ENGINE (depending on workflow)
- MAPPING_AGENT (depending on workflow)

Produces canonical tagging artifacts consumed by:
- Retrieval / Query Answering
- program_COMPOSITE_ENGINE (as features/filters)
- MAPPING_AGENT (as navigation and recall aid)
- program_COA_ENGINE (as filters and coverage rollups)

All writes occur through the Write Broker (Section 7 compliant).

---

## 3. Execution Modes

### 3.1 Reasoning Mode

Not Applicable (Program).

Reasoning Mode is required only for Agents.

### 3.2 Deterministic Mode

The program SHALL:
- Apply tags using only controlled vocabularies (contract-managed)
- Use deterministic rule sets (pattern, metadata rules, structural rules)
- Record provenance and rule identifiers for every tag assignment
- Produce reproducible results given identical inputs and ruleset versions

The program SHALL NOT infer meaning beyond what rules explicitly encode.

---

## 4. Triggers & Entry Conditions

### Trigger Events
- FACT_NORMALIZATION_COMPLETE
- NEW_EVIDENCE_ADDED
- TAG_RULESET_UPDATED
- TAXONOMY_UPDATED (tags/entities/coa vocab changes)

### Entry Conditions
- Controlled vocabulary artifacts available (tags/entities taxonomies as applicable)
- TAG_RULESET resolved and versioned
- Required upstream artifacts available per scope (docs/chunks/facts)

---

## 5. Preconditions (Governance)

No human approval required to execute deterministic tagging.

If attorney/firm policy requires review before tags become “authoritative,” the review step is **separate** and occurs in governance lanes. This program can still produce authoritative tags as defined by contract; UI/workflow may gate downstream usage.

---

## 6. Responsibilities

The program SHALL:
1. Apply document-level tags (DocType, SourceType, Channel, Custodian, etc.)
2. Apply chunk-level tags (thread context, local topic markers where rule-defined)
3. Apply EvidenceFact tags (fact_type, entity presence, amount/date presence)
4. Apply EventCandidate tags (event_type, entity presence, cohesion features)
5. Record provenance for each tag:
   - tag_id
   - target_type + target_id
   - rule_id + ruleset_version
   - evidence reference (when applicable)
6. Emit coverage metrics and error summaries

---

## 7. Non-Goals (Explicit Exclusions)

TAGGING SHALL NOT:
- Create new facts or events
- Create composite events (handled by program_COMPOSITE_ENGINE)
- Perform narrative synthesis
- Perform legal interpretation or COA evaluation
- Overwrite raw evidence or normalize content (handled upstream)
- Apply tags that are not present in controlled vocabularies
- Treat tags as evidentiary proof

---

## 8. Inputs (Canonical Only)

- DOCUMENTS index (from PROCESSING)
- TEXT_CHUNKS index (from PROCESSING)
- EVIDENCE_FACTS.json (from program_FACT_NORMALIZATION)
- EVENT_CANDIDATES.json (from program_COMPOSITE_ENGINE, optional)
- Controlled vocabularies:
  - taxonomies/tags (authoritative)
  - taxonomies/entities (authoritative)
- TAG_RULESET.json (versioned)

Optional (non-authoritative) input:
- TAG_CANDIDATES.json (from optional candidate suggester; see Section 12)

---

## 9. Outputs (Versioned Artifacts)

Authoritative outputs:
- TAG_ASSIGNMENTS.json
- TAGGING_REPORT.json
- TAGGING_PROVENANCE_LOG.json

Where TAG_ASSIGNMENTS entries include:
- target_type (document|chunk|fact|event_candidate|edge)
- target_id
- tag_id
- rule_id
- ruleset_version
- timestamp_utc
- case_id, run_id
- provenance fields required by Section 7

Outputs are supersession-based; prior versions retained.

---

## 10. Blocking Authority

Blocks downstream operations that require authoritative tags when configured by workflow:

- Query Answering (tag-filtered retrieval)
- program_COA_ENGINE (tag-filtered coverage reports)
- program_COMPOSITE_ENGINE (if it requires tag features)

This program does not block MAPPING_AGENT unless MAPPING is configured to require tag assignments as prerequisites.

---

## 11. Human Interaction Points

None required for execution.

Optional UI features (out of scope for this program) may provide:
- Tag browsing and filtering
- Tag assignment review (if policy requires)
- Rule tuning proposals (governed change process)

---

## 12. Interacting Agents / Programs

Upstream:
- PROCESSING
- program_FACT_NORMALIZATION
- program_COMPOSITE_ENGINE (optional input scope)

Downstream:
- Retrieval / Query Answering
- program_COMPOSITE_ENGINE (if tags are used as features)
- MAPPING_AGENT
- program_COA_ENGINE

Optional (separate, non-required):
- program_TAG_CANDIDATE_SUGGESTER (produces TAG_CANDIDATES.json)

Boundary rule (authoritative):
- TAG_CANDIDATES.json MUST NOT be treated as authoritative tags
- TAG_CANDIDATES may be surfaced for review/triage only
- Only TAG_ASSIGNMENTS.json is authoritative output of tagging

---

## 13. Failure Classification

Blocking failures:
- Missing controlled vocabulary artifacts
- Missing TAG_RULESET
- Schema violations in required inputs
- Write Broker rejection

Non-blocking failures:
- Rule match ambiguity (logged)
- High “untagged” volume (reported)
- Optional TAG_CANDIDATES missing/unavailable

---

## 14. Determinism, Reproducibility & Rerun Policy

- Deterministic output required
- Same inputs + same ruleset version = identical tag assignments
- Idempotent assignment identifiers (if used) must be stable across reruns
- Rerun required upon:
  - upstream artifact hash changes
  - TAG_RULESET changes
  - controlled vocabulary changes

---

## 15. Learning & Governance

- No self-modification
- TAG_RULESET changes require governed PR approval
- Controlled vocabulary changes require attorney-approved governance (per COA/taxonomy policy)
- Optional candidate suggestions (if enabled) must be logged with model/version but cannot write authoritative tags

---

## 16. Pristine Data Policy

- No mutation of raw evidence
- No edits to document text or chunk content
- All writes mediated via Write Broker
- Every run emits audit ledger events (execution + writes)

---

## 17. SIPOC

Supplier:
- PROCESSING
- program_FACT_NORMALIZATION
- (optional) program_COMPOSITE_ENGINE

Input:
- docs/chunks indexes
- EvidenceFacts
- controlled vocabularies
- deterministic tag ruleset

Process:
- rule evaluation
- assignment creation
- provenance stamping
- reporting

Output:
- TAG_ASSIGNMENTS
- TAGGING_REPORT
- provenance log

Customer:
- Query Answering / Retrieval
- program_COMPOSITE_ENGINE (optional)
- MAPPING_AGENT
- program_COA_ENGINE
- attorney/staff UI

---

## 18. Acceptance Criteria

The program is compliant when:
- All tags applied are members of controlled vocabularies
- Every tag assignment includes rule_id + ruleset_version
- Outputs are versioned and hash-locked via manifest
- Tagging is deterministic across reruns with identical inputs
- TAGGING_REPORT includes coverage metrics and error summaries
- Tags are not treated as evidence or proof in any downstream contract

---

## 19. Human Presentation Lens

TAGGING makes large case evidence navigable.

It helps attorneys and staff filter, cluster, and retrieve relevant materials quickly while preserving evidentiary integrity.

Tags guide attention.
Evidence proves facts.
Humans decide meaning.