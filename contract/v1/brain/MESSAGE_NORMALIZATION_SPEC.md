# Message Normalization Specification v1.0

**Critical System Contract**  
All raw messages MUST pass normalization before Brain consumption.

---

## 1. PURPOSE

Define a deterministic, auditable pipeline that transforms raw communication inputs (email, SMS, chat, uploads) into structured, context-aware, and legally reliable objects for downstream Brain processing.

The normalization layer ensures:
- Accurate speaker attribution
- Preservation of third-party references
- Separation of metadata vs content
- Multi-message and multi-file context integrity
- Explicit uncertainty handling
- Full traceability

---

## 2. CONTEXT LEVELS (CRITICAL)

The system MUST operate across three levels:

### Message-Level Context
- Sender
- Recipients
- Body content
- Quoted / forwarded content
- Third-party references

### Thread-Level Context
- Message ordering
- Reply chains
- Conversation continuity
- Participant relationships

### Corpus-Level Context
- Multiple files
- Multiple threads
- Cross-thread actor relationships
- Contradictions and corroboration
- Timeline construction across sources

---

## 3. RAW INPUT TYPES

- raw_email
- raw_sms
- raw_chat
- raw_forwarded_chain
- raw_quoted_message

(All raw inputs MUST be preserved and never mutated.)

---

## 4. NORMALIZATION PIPELINE

### Stage 1 — Raw Ingestion
- Identify source type
- Preserve raw content
- Assign ingestion metadata

### Stage 2 — Header Parsing
- Extract sender (From)
- Extract recipients (To, CC, BCC)
- Extract timestamps
- Extract thread identifiers

### Stage 3 — Body Extraction
- Convert to clean text
- Preserve structure
- Normalize encoding

### Stage 4 — Signature Removal
- Strip signatures
- Preserve separately
- NEVER treat as content

### Stage 5 — Footer Removal
- Strip system-generated content

### Stage 6 — Quote Detection
- Extract quoted_blocks
- Preserve original speaker

### Stage 7 — Forward Detection
- Extract forwarded_blocks
- Preserve original sender chain

### Stage 8 — Thread Reconstruction
- Build parent-child relationships
- Order chronologically
- Assign thread_id

### Stage 9 — Speaker Attribution
- Assign speaker_candidate
- Distinguish sender vs quoted vs forwarded speaker

### Stage 10 — Third-Person Extraction
- Identify referenced actors
- Maintain separation from sender/recipient

### Stage 11 — Pronoun Resolution
- Resolve ONLY if confidence >= 0.7
- Otherwise mark unresolved

### Stage 12 — Statement Segmentation
- Break into normalized_statement objects

### Stage 13 — Fact Extraction (CRITICAL)
Transform statements into fact candidates

```json
{
  "fact_candidate": {
    "fact_id": "string",
    "derived_from_statement_ids": [],
    "fact_text": "string",
    "actor_ids": [],
    "event_time_candidate": "ISO8601",
    "fact_type": "observed|reported|inferred",
    "confidence": "float"
  }
}