# program_PROCESSING
(Authoritative Program Contract — v1 | Normalized 19-Section Contract)

---

## 1. Purpose

The PROCESSING program ingests raw case uploads and deterministically produces canonical, indexed artifacts:

- Documents (normalized metadata + hashes)
- Chunks (stable text spans with offsets)
- Extraction-ready structures (attachments, threads, basic modalities)
- Provenance required for downstream citation

PROCESSING is the foundation for all downstream work. If chunk IDs, offsets, and hashes are unstable, EvidenceFacts, composites, mapping, and COA coverage cannot be reliable.

---

## 2. Architectural Position

Operates immediately after:
- File upload / intake acceptance (case-scoped)

Produces canonical artifacts consumed by:
- program_FACT_NORMALIZATION
- program_TAGGING
- program_COMPOSITE_ENGINE
- MAPPING_AGENT
- program_COA_ENGINE
- Retrieval / Query Answering

All persistence writes MUST be mediated through the Write Broker and logged to the Audit Ledger.

---

## 3. Execution Modes

### 3.1 Reasoning Mode

Not Applicable (Program).

Reasoning Mode is required only for Agents.

### 3.2 Deterministic Mode

The program SHALL produce identical outputs given identical inputs and identical parsing configuration:

- Document hashing must be stable (SHA256)
- Document IDs must be stable (idempotent mapping)
- Chunk IDs must be stable (idempotent mapping)
- Chunk offsets must be stable relative to the stored normalized text
- Parsing configuration must be versioned and recorded

PROCESSING SHALL NOT infer meaning. It only structures content.

---

## 4. Triggers & Entry Conditions

### Trigger Events
- NEW_UPLOAD_ACCEPTED
- UPLOAD_BATCH_FINALIZED (optional)
- PARSER_RULESET_UPDATED (rerun)
- OCR_POLICY_UPDATED (rerun)
- NORMALIZATION_RULESET_UPDATED (rerun)

### Entry Conditions
- Case context exists (case_id)
- Upload objects exist (raw files available)
- Parser configuration resolved (versioned)
- Tool Gateway access permitted for any external parsers (if used)

---

## 5. Preconditions (Governance)

No human approval required for deterministic processing.

If policy requires attorney review before downstream reruns after late uploads, that gating occurs in workflow control (Layer B) and not inside PROCESSING.

---

## 6. Responsibilities

The program SHALL:

1. Register each upload as a Document
2. Compute immutable hashes for:
   - raw bytes (raw_hash)
   - normalized text representation (text_hash) when applicable
3. Normalize metadata:
   - filename, extension, mime type
   - source channel (email, sms, social, scan, pleading, etc.) when known
   - timestamps (received, sent, created) when available
   - custodian/participant fields when available
4. Extract text content deterministically:
   - for text-native files: parse directly
   - for scanned images/PDFs: OCR only if enabled by policy
5. Produce stable chunking:
   - chunk text spans with start/end offsets
   - keep chunk sizes within configured bounds
   - preserve ordering
6. Preserve linkage structures:
   - document ↔ attachments
   - email thread headers (subject, from/to, message-id) where available
   - SMS conversation grouping where available
7. Emit canonical indexes and reports

---

## 7. Non-Goals (Explicit Exclusions)

PROCESSING SHALL NOT:
- Normalize facts (handled by program_FACT_NORMALIZATION)
- Tag meaning or topics (handled by program_TAGGING)
- Cluster multi-document events (handled by program_COMPOSITE_ENGINE)
- Create story-to-evidence links (handled by MAPPING_AGENT)
- Perform legal interpretation (handled by COA_ENGINE / COA_REASONER)
- Modify raw evidence files
- Create “summaries” as substitutes for structured outputs

---

## 8. Inputs (Canonical Only)

Required:
- RAW_UPLOADS (file bytes + minimal intake metadata)
- CASE_CONFIG (case_id, policy toggles)
- PARSER_RULESET.json (versioned)

Optional:
- EMAIL_EXPORT metadata (e.g., PST/MBOX indexes)
- SMS export metadata
- Social export metadata
- Prior run indexes (for idempotency checks)

All inputs must be hash-verifiable or captured in audit.

---

## 9. Outputs (Versioned Artifacts)

Canonical outputs (minimum set):

- DOCUMENTS.json
- DOCUMENT_HASH_INDEX.json
- TEXT_CHUNKS.jsonl
- EVIDENCE_OBJECTS.json
- PROCESSING_REPORT.json
- PROCESSING_PROVENANCE_LOG.json

Required fields (minimum):

### DOCUMENTS.json entries
- doc_id (stable)
- case_id
- filename, mime, size_bytes
- raw_hash_sha256
- ingestion_timestamp_utc
- source_channel (if known)
- parent_doc_id (if attachment)
- thread_id (if known)

### TEXT_CHUNKS.jsonl entries
- chunk_id (stable)
- doc_id
- ordinal (stable ordering)
- start_offset, end_offset (relative to normalized_text)
- text (normalized)
- text_hash_sha256 (optional but recommended)

All outputs MUST include provenance headers:
- contract_version
- policy_version
- parser_ruleset_version
- input_hashes
- run_id
- timestamp_utc

Outputs are supersession-based; prior versions retained.

---

## 10. Blocking Authority

Blocks all downstream stages that require structured text and stable citations:

- program_FACT_NORMALIZATION
- program_TAGGING
- program_COMPOSITE_ENGINE
- MAPPING_AGENT
- program_COA_ENGINE
- Retrieval / Query Answering

Until required artifacts exist and schema validation passes.

---

## 11. Human Interaction Points

None required for execution.

Optional UI may provide:
- upload status dashboard
- parse/OCR exceptions queue
- “unreadable file” reporting
- rerun request controls (governed)

---

## 12. Interacting Agents / Programs

Downstream:
- program_FACT_NORMALIZATION (requires chunks + hashes)
- program_TAGGING (requires docs/chunks)
- program_COMPOSITE_ENGINE (requires EvidenceFacts later)
- MAPPING_AGENT (requires structured evidence and citations)
- program_COA_ENGINE (requires EvidenceFacts later)

Upstream:
- Intake UI / upload subsystem
- Orchestrator (Layer B)

---

## 13. Failure Classification

Blocking failures:
- Missing raw files
- Parser failure without fallback
- Schema violations in outputs
- Hash generation failure
- Write Broker rejection

Non-blocking failures:
- OCR skipped by policy
- Partial text extraction
- Missing metadata fields
- Unsupported file types (recorded)

All failures must be recorded in PROCESSING_REPORT.

---

## 14. Determinism, Reproducibility & Rerun Policy

- Deterministic outputs required
- Parser ruleset must be versioned
- Chunking algorithm and parameters must be versioned
- Same inputs + same ruleset = identical outputs

Rerun required upon:
- new uploads
- parser ruleset changes
- OCR policy changes
- normalization changes impacting text content or chunking

---

## 15. Learning & Governance

- No self-modification
- No adaptive chunking that changes without version bump
- Parser improvements require governed changes and rerun semantics
- Any ML/OCR model versions must be logged

---

## 16. Pristine Data Policy

- Raw uploads are immutable and retained
- Derived text is stored separately and versioned
- All writes mediated via Write Broker
- Audit ledger records:
  - ingestion events
  - parse events
  - output writes
  - failures/exceptions

---

## 17. SIPOC

Supplier:
- Client uploads
- Attorney/paralegal uploads
- Intake subsystem

Input:
- raw files + minimal metadata
- versioned parser rules

Process:
- register documents
- hash
- parse/OCR (policy controlled)
- normalize text
- chunk with offsets
- emit indexes/reports

Output:
- documents + chunks + hashes + provenance

Customer:
- downstream programs/agents
- attorney query answering
- audit/compliance

---

## 18. Acceptance Criteria

PROCESSING is compliant when:
- Every document has raw_hash_sha256
- doc_id and chunk_id are stable across reruns with identical inputs
- Every chunk has doc_id + ordinal + offsets
- Offsets correspond to stored normalized text exactly
- Required artifacts are emitted and versioned
- Report + provenance log exist
- No raw evidence is mutated

---

## 19. Human Presentation Lens

PROCESSING turns chaotic uploads into stable, citeable building blocks.

It enables the rest of the system to work with confidence because every downstream claim can point back to exact evidence locations with immutable provenance.

Stable chunks make truth traceable.