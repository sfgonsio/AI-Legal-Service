# program_FACT_NORMALIZATION
(Authoritative Program Contract — v1 | Normalized 19-Section Contract)

---

## 1. Purpose

The FACT_NORMALIZATION program converts decomposed evidence artifacts into atomic, structured EvidenceFact records with immutable evidence-span citations.

Its role is to transform raw extracted signals into normalized, reproducible fact objects suitable for:

- Composite clustering
- Graph construction
- COA evaluation
- Deterministic query answering

It performs structural normalization only. It does not perform legal interpretation.

---

## 2. Architectural Position

Operates after:

- PROCESSING (Documents + Chunks)
- Evidence ingestion indexing complete
- Identity resolution available (if required by policy)

Produces canonical artifacts consumed by:

- program_COMPOSITE_ENGINE
- MAPPING_AGENT
- program_COA_ENGINE
- Query Answering services

All writes occur through the Write Broker (Section 7 compliant).

---

## 3. Execution Modes

### 3.1 Reasoning Mode

Not Applicable (Program).

Reasoning Mode is required only for Agents.

FACT_NORMALIZATION performs deterministic structural transformation only.

### 3.2 Deterministic Mode

The program SHALL:

- Normalize date/time fields (ISO 8601, UTC where possible)
- Normalize monetary values (currency + precision)
- Normalize quantity fields
- Normalize actor references using RESOLVED_ENTITY_INDEX
- Normalize object references (product, document reference, etc.)
- Attach ≥1 immutable evidence span citation per fact
- Emit reproducible artifacts
- Emit provenance metadata

Given identical inputs and ruleset version, outputs MUST be identical.

---

## 4. Triggers & Entry Conditions

### Trigger Event

EVIDENCE_INGESTION_COMPLETE

### Entry Conditions

- DOCUMENT_HASH_INDEX exists
- TEXT_CHUNKS index exists
- EVIDENCE_OBJECTS index exists
- Identity resolution artifacts exist (if enabled by policy)
- NORMALIZATION_RULESET version resolved

### Rerun Triggers

- NEW_EVIDENCE_ADDED
- IDENTITY_RESOLUTION_UPDATED
- NORMALIZATION_RULESET_UPDATED
- Contract version updated

---

## 5. Preconditions (Governance)

No human approval required to execute.

However:

- Promotion of normalized facts to “Approved” status (if implemented) must follow governance lanes.
- All persistence writes must include lane_id and provenance stamping.

---

## 6. Responsibilities

The program SHALL:

1. Generate stable EvidenceFact objects
2. Assign fact_id (idempotent, reproducible)
3. Standardize all structured fields
4. Attach evidence citations:
   - doc_id
   - chunk_id
   - start_offset
   - end_offset
5. Classify preliminary fact_type (Payment, Communication, Shipment, Filing, etc.)
6. Emit:
   - EVIDENCE_FACTS.json
   - FACT_NORMALIZATION_REPORT.json
   - FACT_PROVENANCE_LOG.json

---

## 7. Non-Goals (Explicit Exclusions)

FACT_NORMALIZATION SHALL NOT:

- Create composite events
- Perform multi-document synthesis
- Evaluate legal sufficiency
- Perform COA element mapping
- Infer legal conclusions
- Modify raw evidence artifacts
- Override identity resolution policy

---

## 8. Inputs (Canonical Only)

- EVIDENCE_OBJECTS.json
- TEXT_CHUNKS.jsonl
- DOCUMENT_HASH_INDEX.json
- RESOLVED_ENTITY_INDEX.json (if applicable)
- THREAD_GROUPINGS.json (optional)
- NORMALIZATION_RULESET.json (versioned)

Inputs must be hash-verifiable.

---

## 9. Outputs (Versioned Artifacts)

- EVIDENCE_FACTS.json
- FACT_NORMALIZATION_REPORT.json
- FACT_PROVENANCE_LOG.json

Each output MUST record:

- contract_version
- policy_version
- ruleset_version
- input_hashes
- run_id
- case_id
- timestamp_utc

Outputs are supersession-based. Prior versions retained.

---

## 10. Blocking Authority

Blocks downstream execution of:

- program_COMPOSITE_ENGINE
- MAPPING_AGENT (fact-level operations)
- program_COA_ENGINE
- Query answering requiring EvidenceFacts

Until:

- EVIDENCE_FACTS.json exists
- No blocking failures reported
- Provenance log complete

---

## 11. Human Interaction Points

None required for execution.

Optional UI exposure may include:

- Coverage metrics
- Low-confidence entity matches
- Unparseable fields
- Fact volume statistics

Human review does not alter deterministic execution behavior.

---

## 12. Interacting Agents / Programs

Upstream:

- PROCESSING program
- Evidence Ingestion subsystem
- Identity Resolution subsystem

Downstream:

- program_COMPOSITE_ENGINE
- MAPPING_AGENT
- program_COA_ENGINE
- Retrieval / Query service

All interactions subject to lane enforcement.

---

## 13. Failure Classification

### Blocking Failures

- Missing required input artifacts
- Schema violations
- Hash mismatch
- Ruleset version unresolved
- Write Broker rejection

### Non-Blocking Failures

- Low-confidence entity match
- Missing date in subset of facts
- Unclassified fact type

Non-blocking failures must be reported in FACT_NORMALIZATION_REPORT.

---

## 14. Determinism, Reproducibility & Rerun Policy

- Deterministic transformation required
- Idempotent fact_id generation
- Same inputs + same ruleset = identical outputs
- All outputs version-locked
- Rerun required upon upstream hash change

---

## 15. Learning & Governance

- No autonomous rule mutation
- NORMALIZATION_RULESET changes require contract governance
- Optional ML/LLM assistive extraction tools must be version-logged
- Model versions must be recorded for reproducibility

---

## 16. Pristine Data Policy

- Raw evidence immutable
- Evidence spans reference immutable chunk hashes
- No raw document mutation permitted
- All writes mediated via Write Broker
- Full audit ledger entry required for execution

---

## 17. SIPOC

Supplier:
- PROCESSING
- Evidence ingestion
- Identity resolution

Input:
- Structured evidence artifacts
- Versioned normalization rules

Process:
- Normalize fields
- Resolve entities
- Create EvidenceFacts
- Attach citations
- Emit reports/logs

Output:
- EvidenceFacts
- Reports
- Provenance logs

Customer:
- program_COMPOSITE_ENGINE
- MAPPING_AGENT
- program_COA_ENGINE
- Attorney query answering

---

## 18. Acceptance Criteria

The program is compliant when:

- Every EvidenceFact has ≥1 evidence citation
- Dates standardized (ISO 8601 or null with reason)
- Monetary values normalized
- fact_id reproducible across reruns
- Artifacts versioned and hash-locked
- FACT_NORMALIZATION_REPORT generated
- No raw evidence altered

---

## 19. Human Presentation Lens

FACT_NORMALIZATION converts large-scale unstructured evidence into structured, citation-backed atomic facts.

It enables scalable litigation analysis by making discrete events addressable and verifiable without rereading millions of lines of text.

AI structures facts.  
Humans determine meaning.