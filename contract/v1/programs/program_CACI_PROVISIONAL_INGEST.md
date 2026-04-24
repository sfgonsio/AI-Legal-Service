# program_CACI_PROVISIONAL_INGEST
(Authoritative Program Contract — v1 | Provisional Authority Layer)

---

## 1. Purpose

Ingest CACI instruction PDFs into a **provisional, replaceable** authority store. Produces records that Brain may use as **candidate** authority only — never as canonical certified authority.

## 2. Architectural Position

Sits upstream of:
- `program_CASE_AUTHORITY_DECISION`
- Brain authority resolver (`contract/v1/brain/case_authority_resolution.md`)
- `program_AUTHORITY_BINDING` (which consumes resolver output, not provisional records directly)

Never substitutes for certified-source ingestion.

## 3. Inputs

- Raw PDF file (bytes). MUST be hashed with sha256.
- Optional OCR engine name + version.

## 4. Outputs

- `authority_packs/ca_caci_provisional/raw_pdf/<sha256>.pdf` (write-once)
- `authority_packs/ca_caci_provisional/ocr/<sha256>.txt` (regenerable)
- `authority_packs/ca_caci_provisional/records/<caci_id>.yaml` (active record)
- Updated `authority_packs/ca_caci_provisional/manifest.yaml`

All records must validate against `contract/v1/schemas/authority/caci_provisional_record.schema.json`.

## 5. Pipeline

1. **Hash** — compute sha256(PDF). If file exists at that path, STOP (immutable).
2. **Store PDF** — write to `raw_pdf/<sha256>.pdf`.
3. **OCR** — run OCR engine; write `ocr/<sha256>.txt`. Emit `ocr_char_conf`.
4. **Structure parse** — detect instruction number, title, elements. Emit `structure_parse_conf`.
5. **Element extraction** — per element, detect text boundaries + proof type markers. Emit `element_field_conf[element_id]`.
6. **Aggregate** — `overall = min_required(ocr, structure, min(element_field_conf.values()))`.
7. **Decide**:
   - `overall >= threshold (0.90)` AND every `element_field_conf >= 0.90` → `status: PROVISIONAL`, `decision: ACCEPT`.
   - otherwise → `status: BLOCKED_UNTRUSTED`, `decision: BLOCK`.
8. **Supersession check** — if a record for this `caci_id` already exists, call `program_CACI_SUPERSESSION`.
9. **Write** — emit record YAML; update `manifest.yaml`.

## 6. Invariants

- `trust.canonical` is always `false`.
- `trust.replaceable` is always `true`.
- `provenance.certified` is always `false`.
- Raw PDF path must never be modified once written.
- BLOCKED_UNTRUSTED records are still persisted for audit — manifest marks them accordingly.

## 7. Non-Goals

- No certification, no promotion to canonical.
- No direct consumption by downstream mappers — all consumption goes through Brain resolver.
- No editing of existing records; updates are supersession events.

## 8. Failure Modes

- OCR engine failure → record written with `decision: BLOCK` and `status: BLOCKED_UNTRUSTED`.
- Structure parse failure → same.
- Hash collision with differing bytes (cryptographically implausible) → hard fail.

## 9. Audit

Every run appends an entry to `authority_packs/ca_caci_provisional/audit.log` (JSONL): `{run_id, pdf_sha256, caci_id, decision, confidence.overall, timestamp}`.

## 10. Versioning

Any change to the confidence aggregation formula or threshold is a contract change and requires governed review.
