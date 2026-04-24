# program_OCR_OPTIMIZATION_PLAN
(v1 — Forward plan, honest about what is and isn't done today)

---

## Status today

OCR is **NOT IMPLEMENTED**. The ingest pipeline detects scanned-only PDFs and image files and marks them with an explicit status so nothing silently succeeds:

- `extraction_status = OCR_REQUIRED` — scanned PDF or image; file is stored, text is not extracted.
- `extraction_status = OCR_NOT_AVAILABLE` — reserved for future use; equivalent to OCR_REQUIRED for now.
- `extraction_status = EXTRACTION_FAILED` — extractor ran but produced no usable text.
- `extraction_status = UNSUPPORTED_TYPE` — extension has no extractor path.
- `extraction_status = TEXT_EXTRACTION_COMPLETE` — text extracted successfully.

The Document row also carries `is_scanned_pdf`, `extraction_method` (e.g. `pypdf`), and `extraction_confidence` (0.0–1.0). The UI surfaces these honestly.

## Forward plan

### Preferred engine

Use **Tesseract** via `pytesseract` for v2:
- Pure open-source, well-understood accuracy on typed docs (>90%).
- No external API cost / PII exposure.
- Can run in-process in a FastAPI BackgroundTask.
- Known weaknesses: handwriting, low-DPI scans. Those remain OCR_REQUIRED.

Graduation path (future): AWS Textract / Google Document AI for cases where the client opts in to cloud OCR.

### Where OCR output is stored

- Raw OCR text written to `storage/cases/{case_id}/ocr/<sha256>.txt` (separate from extracted-from-PDF text).
- Document row fields updated:
  - `extraction_status = TEXT_EXTRACTION_COMPLETE`
  - `extraction_method = tesseract-5.x`
  - `extraction_confidence = <mean per-word conf>` (tesseract reports this)
  - `text_content` populated from OCR output (unchanged ingest flow from stage 4 onward).
- An `OcrRun` table (parallel to `IngestEvent`) captures each OCR attempt: `document_id`, `engine`, `engine_version`, `confidence`, `page_count`, `duration_ms`, `error_detail`.

### Confidence scoring

- Tesseract's `image_to_data` returns per-word confidence. Aggregate:
  - `per_page_confidence = mean(word_conf)` across words on the page.
  - `doc_confidence = mean(per_page_confidence)` weighted by page char count.
- Thresholds:
  - `>= 0.85` → TEXT_EXTRACTION_COMPLETE (full use downstream).
  - `0.60–0.85` → TEXT_EXTRACTION_COMPLETE with `requires_attorney_review: true` flag.
  - `< 0.60` → OCR_REQUIRED stays set; attorney may manually re-run with higher DPI or different engine.

### Retry / reprocess flow

- `POST /documents/{id}/ocr` kicks a new OcrRun; supersedes prior. No overwrite — previous OCR text retained under `storage/.../ocr/<sha256>__<run_id>.txt`.
- Attorney UI action: "Re-run OCR" button on docs with OCR_REQUIRED or low-confidence extraction.
- Actor extraction pipeline re-runs on the updated text. Existing actor rows are enriched (mention_count bumped) rather than duplicated (existing dedup invariant).

### UI indicators (already partially live)

Per IngestStatusList ([IngestStatusList.jsx](casecore-runtime/production/frontend/src/components/IngestStatusList.jsx)):
- Text extracted (pypdf · confidence 78%)
- OCR required — this file appears to be scanned. Text extraction not available yet; stored for reference.
- OCR not yet supported for this file type — stored for reference.
- Extraction failed: &lt;reason&gt;. Remove and re-upload to retry.
- Unsupported file type — stored but not processed.

Once Tesseract is wired, `OCR_REQUIRED` rows gain a "Run OCR" button that transitions them into a new phase:
`ocr_running → ocr_complete → (then proceed with normalize → index → actor_extraction)`.

### Future replacement path

- Keep `extraction_method` as a string so swapping engines (tesseract → textract → etc.) requires no schema change.
- `OcrRun` retains engine+version so historical attribution is preserved after an engine upgrade.
- Confidence thresholds live in a single constants module so tuning is one-line.

### What will NOT be attempted in v2

- Handwriting recognition.
- Multi-column layout preservation.
- Table-structure extraction.
- Language detection beyond English.

These become V3 if users need them.

---

## Summary: the honest current position

- We explicitly detect when OCR is needed and we never lie about extraction success.
- We have an optimization plan and a stubbed API surface.
- We do not have an OCR engine installed or wired yet. A future PR adds `pytesseract`, `OcrRun`, `POST /documents/{id}/ocr`, and the "Re-run OCR" UI button.
