# program_INGEST_PIPELINE
(Authoritative Program Contract — v1 | Save-Path Ingest)

---

## 1. Purpose

Run on every save/upload. Bounded to: persist raw files, hash, extract text/content, normalize, index, and populate Actors. Nothing else. Legal analysis triggers only on `POST /cases/{id}/submit-for-analysis`.

## 2. Scope

- Sole consumer of raw uploads.
- Sole writer of `Document.ingest_phase`, `IngestEvent` rows, `Actor` and `ActorMention` rows.
- NEVER invokes `brain.authority_resolver`, `brain.recompute`, COA/burden/remedy/complaint code.
- SR-11 and SR-12 enforce these boundaries.

## 3. Phases (strict order)

1. `uploaded` — raw bytes persisted to hash-addressed storage path.
2. `hashed` — sha256 of bytes recorded.
3. `extracting` → `extracted` — text extracted per content_extractors dispatch.
4. `normalized` — whitespace/encoding normalized, char_count updated.
5. `indexed` — top-K term frequencies computed.
6. `actor_extraction_running` → `actors_extracted` — rule-based extractor; Actor + ActorMention rows created/updated.
7. `ingest_complete` — terminal success.

Non-terminal branches:
- `extract_skipped` — unsupported content type OR no bytes and no pre-seeded text.
- `ingest_failed` — fatal error; `ingest_error_detail` populated.

## 4. Storage

- Root: `casecore-runtime/production/backend/storage/` (override via `CASECORE_STORAGE_PATH`).
- Per-case: `cases/{case_id}/uploads/<sha256><ext>` (hash-addressed); `cases/{case_id}/archives/<sha256>.zip` for archives.
- Identical bytes re-uploaded to the same case deduplicate on disk.

## 5. Structure preservation

- `Document.filename` — original file name.
- `Document.folder` — original relative folder (or derived from relative_path).
- `Document.archive_id` + `archive_relative_path` — archive membership + path inside the zip.
- `UploadArchive` row retains original archive filename, sha256, size, entry_count.

## 6. Actor extraction

Per-document, after indexing. Runs `brain.actor_extractor.extract_actors` on normalized text. Resolves each candidate against existing case actors:
- Exact canonical match → RESOLVED (existing actor's `mention_count` incremented).
- Single fuzzy match (substring containment) → RESOLVED.
- Multiple fuzzy matches → AMBIGUOUS.
- No match → CANDIDATE (new actor row).

Case-creation seeds RESOLVED actors from `Case.plaintiff`, `Case.defendant`, `Case.court`.

Every match writes an `ActorMention` row with snippet + offset_start/end + confidence.

## 7. Triggers

Runs as a FastAPI BackgroundTask from:
- `POST /documents/upload`
- `POST /documents/upload-zip`

Does NOT run on analysis submit. Does NOT run on Case PATCH / save-draft metadata updates (those don't produce new content).

## 8. Limits (v1)

- 500 MB per file.
- 500 MB compressed archive.
- 2 GB uncompressed archive total.
- 2000 entries per archive.
- Skips `__MACOSX/`, `.DS_Store`, `Thumbs.db`, `.git/`, `.svn/`.

## 9. Non-goals

- No COA mapping.
- No burden, remedy, or complaint work.
- No authority resolution.
- No OCR (images marked `extract_skipped`).
- No full-text search (v1 writes a small top-K index only).
