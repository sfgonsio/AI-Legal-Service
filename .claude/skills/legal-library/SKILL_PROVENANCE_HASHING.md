# SKILL_PROVENANCE_HASHING

## Use when

- Any raw source text, extracted text, or normalized authority artifact is captured or transformed and a stable, reproducible identifier is required.

## Do NOT use when

- The artifact has already been hashed and the prior hash is still valid (input bytes unchanged).
- Hashing case-evidence content (this skill is scoped to authority artifacts only).

## Inputs

- An artifact (raw bytes, extracted text, or normalized JSON)
- An artifact label (e.g., `raw_capture`, `extracted_text`, `normalized_json`)

## Procedure

1. Read the artifact as bytes.
2. Compute SHA-256 over the bytes.
3. Record the hash as `sha256:<hex>` along with byte length and artifact label.
4. Persist the hash in the artifact's metadata.

## Outputs

`HASH_RECORD` — per artifact: artifact label, SHA-256 hash, byte length, hash computed at (ISO 8601, UTC).

## Validation rules

- Hashes must be reproducible: re-computing on the same artifact must yield the same hash.
- Hash must cover the artifact as captured — not a re-serialized version.
- Hash must include byte length to defeat trivial truncation attacks on metadata records.

## Failure modes

- Artifact unreadable → record `HASH_FAILED_UNREADABLE`; do not record a placeholder hash.
- Artifact is a stream that cannot be re-read → require the caller to provide a finalized bytes buffer.

## Test fixture expectations

- Fixture: deterministic input produces a known hash on every run.
- Fixture: empty artifact produces the SHA-256 of the empty string.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be invoked for live persistence of hash records into production authority artifacts until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
