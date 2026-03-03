# Program Contract: RESEARCH_CAPTURE
**Version:** v1  
**Layer:** Brain (Post-Spine Baseline v1.0-spine-stable)  
**Type:** Deterministic Program (Non-Agent)  
**Status:** Brain v1  

---

# 1. Purpose
RESEARCH_CAPTURE deterministically converts discovered sources into stored, hashed, provenance-complete candidate knowledge artifacts suitable for attorney review and governed promotion.

This is the bridge from “roaming research” to “defensible knowledge objects.”

---

# 2. Design Principles
1. Deterministic execution for a given input payload.
2. Captures immutable snapshots (or immutable references + hashes).
3. Produces candidate-only knowledge objects (no promotion).
4. Enforces provenance completeness.
5. Logs audit events for every captured item.
6. Enables replay by pinning hashes and snapshot references.

---

# 3. Inputs
RESEARCH_CAPTURE consumes a capture request payload from RESEARCH_AGENT (or other agents), containing a list of discovered sources.

Each source request MUST include:
- source_locator (URL / doc id / citation string)
- source_tier (from approved_sources.yaml)
- retrieval_metadata (timestamp, method)
- query_trace (prompt/search terms)
- optional: raw_content (if already fetched through gateway)
- optional: extracted_text (if parsed through gateway)

RESEARCH_CAPTURE must also receive:
- policy_snapshot_id (hash of approved_sources.yaml used)
- run_id (originating run)
- initiated_by (actor id: agent/human)

---

# 4. Outputs
For each captured source:
- stored artifact record (artifact_id)
- content_hash (SHA256 of normalized content)
- snapshot_reference (local store path or immutable reference)
- candidate knowledge object record with provenance fields

Additionally:
- capture_manifest.json summarizing all captured items and hashes

Canonical output locations:
- artifacts/research/capture_manifest.json
- artifacts/research/captured/<artifact_id>.<ext>

---

# 5. Deterministic Workflow
For each source item:
1. Validate required fields present.
2. Validate tier + domain compliance (using policy_snapshot_id).
3. Fetch content if not provided (through gateway fetch tool only).
4. Normalize content (stable normalization rules).
5. Compute SHA256 content_hash (lower-case hex).
6. Store snapshot (or immutable reference) + record snapshot_reference.
7. Create candidate knowledge object with trust_level=candidate.
8. Emit audit events for capture success/failure.

No external state may change the output except input payload content.

---

# 6. Normalization Rules (Stable)
Normalization must be consistent across runs:
- normalize line endings to LF
- trim leading/trailing whitespace
- collapse excessive whitespace (configurable)
- preserve meaningful punctuation
- preserve citation strings

Content hash must be computed on normalized content only (excluding metadata).

---

# 7. Provenance Requirements
Each candidate knowledge object MUST include:
- source_identifier (locator)
- original_citation (if available)
- retrieval_timestamp
- query_trace
- policy_snapshot_id
- ingest_run_id (capture_run_id)
- content_hash
- jurisdiction (if inferred or provided)
- effective_date (if known; else null)
- trust_level = candidate

Missing provenance → capture fails.

---

# 8. Audit Ledger Events (Must Log)
Per run:
- research_capture_run_started
- research_capture_policy_bound (policy_snapshot_id)
- research_capture_item_captured (artifact_id, content_hash, locator, tier)
- research_capture_item_failed (locator, reason)
- research_capture_run_completed (counts, hashes)

---

# 9. Safety & Compliance Controls
- Enforce approved_sources.yaml domain/tier constraints.
- If a domain is not permitted:
  - mark as blocked
  - require escalation workflow (outside v1 scope, but record event)
- Store only compliant excerpts where required; prefer storing full documents only if permitted by policy and licensing.

---

# 10. Replay Compatibility
Replay equivalence requires:
- same capture request payload
- same policy_snapshot_id
- same normalization rules version
- same content_hash outputs

If any mismatch occurs, replay must fail or mark non-equivalence explicitly.

---

# 11. Error Handling
Capture must fail (and log) if:
- content cannot be fetched or provided
- required provenance is missing
- normalization or hashing fails
- storage write fails
- policy tier/domain violation without escalation approval

Partial success is allowed per-item, but must:
- produce a complete capture_manifest.json with successes and failures.

---

# 12. Relationship to Knowledge Contract v1
RESEARCH_CAPTURE produces only candidate knowledge objects.
Promotion remains governed by Knowledge Contract v1 and attorney review.

---

# 13. Versioning
This contract is Program Contract v1.
Future versions must preserve:
- deterministic hashing
- provenance completeness
- trust separation
- audit logging completeness