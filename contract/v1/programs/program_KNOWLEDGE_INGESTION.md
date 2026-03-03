# Program Contract: KNOWLEDGE_INGESTION
**Version:** v1  
**Layer:** Brain (Post-Spine Baseline v1.0-spine-stable)  
**Type:** Deterministic Program (Non-Agent)  
**Status:** Brain v1  

---

# 1. Purpose

The KNOWLEDGE_INGESTION program is responsible for:

- Ingesting external legal sources
- Normalizing content into structured knowledge objects
- Assigning deterministic identifiers
- Fingerprinting ingested content
- Initializing trust lifecycle state
- Logging audit events

This program is deterministic and must preserve replay integrity.

---

# 2. Design Principles

1. No live web calls during reasoning workflows.
2. All ingestion runs must be version-scoped.
3. All ingested content must be hash-fingerprinted.
4. All knowledge objects must begin as `candidate`.
5. Ingestion does not promote knowledge.
6. Replay must reproduce identical knowledge state.

---

# 3. Supported Source Types (v1)

## 3.1 authority_text sources
- CA Evidence Code
- CA Jury Instructions
- Statutory code libraries
- Court procedural rules

## 3.2 structured research uploads
- Attorney-uploaded white papers
- Practice guides
- Court rule summaries

## 3.3 case analysis artifacts (future)
- Structured case summaries
- Extracted holdings

Live scraping is prohibited in v1.

---

# 4. Ingest Run Model

Each execution creates:

- ingest_run_id (UUID)
- ingest_timestamp
- source_bundle_identifier
- source_version
- content_hash

All knowledge objects created during the run are tagged with ingest_run_id.

---

# 5. Deterministic Workflow

The ingestion pipeline must follow this sequence:

1. Load source bundle (local or approved dataset)
2. Normalize raw content
3. Extract structured elements
4. Assign deterministic object IDs
5. Generate content hash (SHA256)
6. Persist knowledge object
7. Initialize trust_level = candidate
8. Log audit event

No conditional branching based on external state.

---

# 6. Knowledge Object Creation Rules

For each object type:

## authority_text
- authority_id = deterministic hash(citation + jurisdiction)
- content_hash = SHA256(normalized text)
- trust_level = candidate

## burden_map
- element linkage must reference authority_id
- object hash must include linked authority hashes

## heuristic_rule
- heuristic_id must be deterministic hash(description)
- supporting_authority_ids required

## practice_guide
- version must be explicit
- author metadata required

---

# 7. Hashing Requirements

All hashes must:

- Use SHA256
- Be lower-case hex
- Be calculated on normalized content only
- Exclude runtime metadata fields

Hash drift detection is required during replay.

---

# 8. Audit Ledger Requirements

Each ingest run must log:

Event Type: knowledge_ingest_run

Required Audit Fields:
- ingest_run_id
- source_identifier
- object_count
- run_timestamp
- content_hash_bundle
- initiated_by
- run_status

Individual object creation events must also log:

Event Type: knowledge_object_created
- knowledge_object_id
- ingest_run_id
- object_type
- trust_level

---

# 9. Replay Compatibility

Replay enforcement requires:

- Same ingest_run_id
- Same source bundle version
- Same normalized content
- Same deterministic ID assignment

If content_hash mismatch occurs, replay must fail.

---

# 10. Trust Initialization

All knowledge objects begin as:
