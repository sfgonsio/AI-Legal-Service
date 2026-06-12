# CA CACI — Provisional Authority Store

## Purpose

Holds **provisional, replaceable** CACI records. These are candidates only — they are never globally canonical certified authority. Brain may propose from them but may not ground case output on them without a case-scoped attorney decision.

## Layout

```
ca_caci_provisional/
  manifest.yaml          # index of active records (one per caci_id)
  records/               # active provisional records (YAML)
  superseded/            # prior versions (read-only after supersession)
  raw_pdf/               # immutable raw PDFs, content-addressed by sha256
  ocr/                   # derivative OCR text (regenerable)
```

## Rules

- Raw PDFs are **write-once**. Filename is the sha256 of the PDF bytes.
- OCR text is derivative only. Regenerating OCR produces a **new record**, not an edit.
- Records are append-only. Updates create a new `record_id` and set `supersedes` to the prior record.
- A record falls to `BLOCKED_UNTRUSTED` when confidence < 0.90 (per confidence model).
- All records carry `trust.canonical: false` and `trust.replaceable: true`.
- Schema: `contract/v1/schemas/authority/caci_provisional_record.schema.json`.

## Not canonical

These records are not admitted into case use automatically. Admission is per-case and per-CACI, via the case authority decision model (PENDING_REVIEW → ACCEPTED | REJECTED | REPLACED).
