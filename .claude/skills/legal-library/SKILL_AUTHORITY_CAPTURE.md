# SKILL_AUTHORITY_CAPTURE

## Use when

- A `SOURCE_VERIFICATION_REPORT` returned `accept` and the official text must be captured verbatim.

## Do NOT use when

- Source has not been verified.
- Capture would require interpretation, summarization, or paraphrase of the source.

## Inputs

- An `accept` row from `SOURCE_VERIFICATION_REPORT`
- The source's pathway URL or file path

## Procedure

1. Fetch the official source text byte-for-byte where possible.
2. Preserve the source format (HTML/PDF/XML/JSON/TXT) alongside any extracted plain text.
3. Record `source_accessed_at` (ISO 8601, UTC).
4. Compute a provenance hash via `SKILL_PROVENANCE_HASHING` over both the raw artifact and the extracted text.
5. Bundle the capture as `RAW_AUTHORITY_CAPTURE_PACKET`.

## Outputs

`RAW_AUTHORITY_CAPTURE_PACKET` — per authority item: source pointer, raw artifact pointer, extracted text, format, accessed_at, raw hash, extracted-text hash.

## Validation rules

- Extracted text must be a faithful representation of the source. No editorial cleanup.
- Hashes must be reproducible from the captured artifacts.
- Capture must include both the raw artifact and the extracted text — never one without the other.

## Failure modes

- Source unreachable at capture time → record `CAPTURE_FAILED_UNREACHABLE`; route to `SKILL_REJECTION_QUARANTINE`.
- Format extraction loses semantically significant structure (e.g., dropped numbered subsections) → record `EXTRACTION_INCOMPLETE`; route to user.

## Test fixture expectations

- Fixture: HTML source with footnotes — extracted text preserves footnote markers and contents.
- Fixture: PDF source — text extraction matches a known reference transcription.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be invoked for live capture or persistence until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. Test-fixture exercises only until the gate clears.
