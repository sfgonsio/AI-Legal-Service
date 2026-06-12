"""
Document routes: read + upload + ingest status.

Upload endpoints trigger the ingest pipeline as a BackgroundTask. They NEVER
call the authority resolver. See SR-11/SR-12 and
contract/v1/programs/program_INGEST_PIPELINE.md.
"""
from __future__ import annotations

import hashlib
import os
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Case, Document, UploadArchive, ActorMention
from schemas import (
    DocumentResponse,
    DocumentDetailResponse,
    UploadBatchResponse,
    UploadedDocumentResult,
    UploadArchiveResponse,
    IngestStatusDocument,
    IngestStatusResponse,
    UploadConfigResponse,
    CheckHashesRequest,
    CheckHashesResponse,
    HashCheckHit,
)
from brain.content_extractors import detect_file_type
from brain.ingest_pipeline import run_ingest

router = APIRouter(prefix="/documents", tags=["documents"])


# ---------------- storage layout ----------------

def _storage_root() -> Path:
    override = os.getenv("CASECORE_STORAGE_PATH")
    if override:
        root = Path(override)
    else:
        # <backend>/storage by default
        root = Path(__file__).resolve().parent.parent / "storage"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _case_upload_dir(case_id: int) -> Path:
    p = _storage_root() / "cases" / str(case_id) / "uploads"
    p.mkdir(parents=True, exist_ok=True)
    return p


# Safety limits
MAX_FILE_BYTES = 500 * 1024 * 1024          # 500 MB per file
MAX_ARCHIVE_BYTES = 500 * 1024 * 1024       # 500 MB compressed
MAX_ARCHIVE_UNCOMPRESSED = 2 * 1024 * 1024 * 1024   # 2 GB total
MAX_ARCHIVE_ENTRIES = 2000
SKIP_PATH_RULES = ("__MACOSX/", ".DS_Store", "Thumbs.db", "/.git/", "/.svn/")


def _should_skip_archive_entry(name: str) -> bool:
    if name.endswith("/"):
        return True  # directory entry
    lower = name.lower()
    for rule in SKIP_PATH_RULES:
        if rule in name or rule in lower:
            return True
    return False


async def _case_or_404(db: AsyncSession, case_id: int) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "case not found")
    return case


# ---------------- reads + config ----------------
# NOTE: specific paths MUST be registered before the generic "/{doc_id}"
# path, because FastAPI's first-match routing will otherwise send
# "/documents/upload-config" into the int-validator for doc_id and 422.

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(case_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    q = select(Document)
    if case_id is not None:
        q = q.where(Document.case_id == case_id)
    res = await db.execute(q)
    return list(res.scalars().all())


@router.get("/case/{case_id}", response_model=List[DocumentResponse])
async def get_case_documents(case_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Document).where(Document.case_id == case_id))
    return list(res.scalars().all())


# Buckets used by the UI; keys are file extensions (without the dot).
# Defined above the generic /{doc_id} route so /upload-config resolves correctly.
_EXTENSION_BUCKETS = {
    "txt": "text", "md": "text", "log": "text", "csv": "text",
    "eml": "email", "msg": "email",
    "html": "html", "htm": "html",
    "pdf": "pdf",
    "docx": "docx",
    "png": "image", "jpg": "image", "jpeg": "image",
    "gif": "image", "tif": "image", "tiff": "image",
    "zip": "archive",
}


@router.get("/upload-config", response_model=UploadConfigResponse)
async def upload_config():
    return UploadConfigResponse(
        max_file_bytes=MAX_FILE_BYTES,
        max_archive_bytes=MAX_ARCHIVE_BYTES,
        max_archive_uncompressed_bytes=MAX_ARCHIVE_UNCOMPRESSED,
        max_archive_entries=MAX_ARCHIVE_ENTRIES,
        supported_extensions=sorted(_EXTENSION_BUCKETS.keys()),
        extension_buckets=dict(_EXTENSION_BUCKETS),
        skipped_path_substrings=list(SKIP_PATH_RULES),
    )


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Document).where(Document.id == doc_id))
    doc = res.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return doc


# ---------------- uploads ----------------

async def _persist_one_upload(
    db: AsyncSession,
    case_id: int,
    file: UploadFile,
    filename: str,
    folder: str,
    relative_path: Optional[str],
    archive_id: Optional[int],
    archive_relative_path: Optional[str],
) -> Document:
    """Stream the upload body to disk (hash-addressed), create Document row."""
    # Stream into a temp file first to compute sha256 before we know the final
    # path (hash-addressed). Use a unique temp name to avoid collisions.
    tmp_path = _case_upload_dir(case_id) / f"._incoming_{uuid.uuid4().hex}"
    hasher = hashlib.sha256()
    size = 0
    CHUNK = 1024 * 1024
    try:
        with open(tmp_path, "wb") as fh:
            while True:
                chunk = await file.read(CHUNK)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    raise HTTPException(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        f"{filename} exceeds MAX_FILE_BYTES ({MAX_FILE_BYTES})",
                    )
                hasher.update(chunk)
                fh.write(chunk)
        sha = hasher.hexdigest()
        ext = Path(filename).suffix.lower()
        final_path = _case_upload_dir(case_id) / f"{sha}{ext}"
        if not final_path.exists():
            os.replace(tmp_path, final_path)
        else:
            # identical bytes already on disk; drop the temp
            tmp_path.unlink(missing_ok=True)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    doc = Document(
        case_id=case_id,
        filename=filename,
        folder=folder or None,
        file_type=detect_file_type(filename),
        text_content=None,
        char_count=0,
        byte_size=size,
        sha256_hash=sha,
        storage_path=str(final_path),
        archive_id=archive_id,
        archive_relative_path=archive_relative_path,
        ingest_phase="uploaded",
        created_at=datetime.utcnow(),
    )
    db.add(doc)
    await db.flush()
    return doc


@router.post("/upload", response_model=UploadBatchResponse, status_code=201)
async def upload_files(
    background: BackgroundTasks,
    case_id: int = Form(...),
    files: List[UploadFile] = File(...),
    filenames: Optional[List[str]] = Form(None),
    folders: Optional[List[str]] = Form(None),
    relative_paths: Optional[List[str]] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Multipart upload: one or more files, with optional parallel arrays of
    filenames / folders / relative_paths to preserve source structure.

    If filenames/folders are omitted, server falls back to the UploadFile's
    own filename (flat structure).
    """
    await _case_or_404(db, case_id)

    accepted: List[UploadedDocumentResult] = []
    errors: List[str] = []
    rejected = 0

    n = len(files)
    for i, uf in enumerate(files):
        try:
            fn = filenames[i] if filenames and i < len(filenames) and filenames[i] else uf.filename
            fld = folders[i] if folders and i < len(folders) else ""
            rel = relative_paths[i] if relative_paths and i < len(relative_paths) else None
            if rel and not fld:
                # derive folder from relative_path when caller only sent that
                p = Path(rel)
                fld = str(p.parent) if str(p.parent) != "." else ""
                fn = fn or p.name
            doc = await _persist_one_upload(
                db=db,
                case_id=case_id,
                file=uf,
                filename=fn,
                folder=fld or "",
                relative_path=rel,
                archive_id=None,
                archive_relative_path=None,
            )
            accepted.append(UploadedDocumentResult(
                document_id=doc.id,
                filename=doc.filename,
                folder=doc.folder,
                file_type=doc.file_type,
                byte_size=doc.byte_size,
                sha256_hash=doc.sha256_hash,
                archive_id=None,
                archive_relative_path=None,
                ingest_phase=doc.ingest_phase,
            ))
        except HTTPException as he:
            rejected += 1
            errors.append(f"{uf.filename}: {he.detail}")
        except Exception as e:
            rejected += 1
            errors.append(f"{uf.filename}: {type(e).__name__}: {e}")

    await db.commit()

    if accepted:
        background.add_task(run_ingest, case_id, [a.document_id for a in accepted])

    return UploadBatchResponse(
        case_id=case_id,
        accepted_count=len(accepted),
        rejected_count=rejected,
        archive_id=None,
        documents=accepted,
        errors=errors,
    )


@router.post("/upload-zip", response_model=UploadBatchResponse, status_code=201)
async def upload_zip(
    background: BackgroundTasks,
    case_id: int = Form(...),
    archive: UploadFile = File(...),
    actor_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a single .zip archive. Server extracts entries server-side,
    preserving each entry's path as archive_relative_path.

    Defensive limits: MAX_ARCHIVE_BYTES, MAX_ARCHIVE_UNCOMPRESSED,
    MAX_ARCHIVE_ENTRIES. Skips __MACOSX/, .DS_Store, .git/, .svn/.
    """
    await _case_or_404(db, case_id)

    # 1. Persist the archive itself to storage
    arc_dir = _case_upload_dir(case_id).parent / "archives"
    arc_dir.mkdir(parents=True, exist_ok=True)
    tmp_archive = arc_dir / f"._incoming_{uuid.uuid4().hex}.zip"
    hasher = hashlib.sha256()
    size = 0
    try:
        with open(tmp_archive, "wb") as fh:
            while True:
                chunk = await archive.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_ARCHIVE_BYTES:
                    raise HTTPException(413, f"archive exceeds {MAX_ARCHIVE_BYTES} bytes")
                hasher.update(chunk)
                fh.write(chunk)
    except Exception:
        if tmp_archive.exists():
            tmp_archive.unlink(missing_ok=True)
        raise

    archive_sha = hasher.hexdigest()
    final_archive = arc_dir / f"{archive_sha}.zip"
    if not final_archive.exists():
        os.replace(tmp_archive, final_archive)
    else:
        tmp_archive.unlink(missing_ok=True)

    # 2. Open the zip and enumerate entries
    if not zipfile.is_zipfile(final_archive):
        raise HTTPException(400, "not a valid zip archive")

    accepted: List[UploadedDocumentResult] = []
    errors: List[str] = []
    rejected = 0
    entry_count = 0
    uncompressed_total = 0

    arc_row = UploadArchive(
        case_id=case_id,
        original_filename=archive.filename or "archive.zip",
        sha256_hash=archive_sha,
        byte_size=size,
        entry_count=0,
        storage_path=str(final_archive),
        uploaded_at=datetime.utcnow(),
        uploaded_by_actor_id=actor_id,
    )
    db.add(arc_row)
    await db.flush()

    case_upload_dir = _case_upload_dir(case_id)

    with zipfile.ZipFile(final_archive) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ARCHIVE_ENTRIES:
            raise HTTPException(413, f"archive has {len(infos)} entries > max {MAX_ARCHIVE_ENTRIES}")
        for zi in infos:
            if _should_skip_archive_entry(zi.filename):
                continue
            entry_count += 1
            uncompressed_total += zi.file_size
            if uncompressed_total > MAX_ARCHIVE_UNCOMPRESSED:
                raise HTTPException(413, "archive uncompressed size exceeds limit (zip bomb defense)")
            try:
                data = zf.read(zi)
                ehash = hashlib.sha256(data).hexdigest()
                ext = Path(zi.filename).suffix.lower()
                final_path = case_upload_dir / f"{ehash}{ext}"
                if not final_path.exists():
                    with open(final_path, "wb") as wh:
                        wh.write(data)
                # folder/filename: split the zip path (always forward slashes,
                # regardless of host OS)
                parts = zi.filename.rsplit("/", 1)
                fn = parts[-1]
                fld = parts[0] if len(parts) == 2 else ""
                doc = Document(
                    case_id=case_id,
                    filename=fn,
                    folder=fld,
                    file_type=detect_file_type(fn),
                    text_content=None,
                    char_count=0,
                    byte_size=zi.file_size,
                    sha256_hash=ehash,
                    storage_path=str(final_path),
                    archive_id=arc_row.id,
                    archive_relative_path=zi.filename,
                    ingest_phase="uploaded",
                    created_at=datetime.utcnow(),
                )
                db.add(doc)
                await db.flush()
                accepted.append(UploadedDocumentResult(
                    document_id=doc.id,
                    filename=doc.filename,
                    folder=doc.folder,
                    file_type=doc.file_type,
                    byte_size=doc.byte_size,
                    sha256_hash=doc.sha256_hash,
                    archive_id=arc_row.id,
                    archive_relative_path=doc.archive_relative_path,
                    ingest_phase=doc.ingest_phase,
                ))
            except Exception as e:
                rejected += 1
                errors.append(f"{zi.filename}: {type(e).__name__}: {e}")

    arc_row.entry_count = entry_count
    await db.commit()

    if accepted:
        background.add_task(run_ingest, case_id, [a.document_id for a in accepted])

    return UploadBatchResponse(
        case_id=case_id,
        accepted_count=len(accepted),
        rejected_count=rejected,
        archive_id=arc_row.id,
        documents=accepted,
        errors=errors,
    )


# ---------------- ingest status ----------------

@router.get("/case/{case_id}/ingest-status", response_model=IngestStatusResponse)
async def ingest_status(case_id: int, db: AsyncSession = Depends(get_db)):
    await _case_or_404(db, case_id)

    res = await db.execute(select(Document).where(Document.case_id == case_id))
    docs = list(res.scalars().all())

    # mention counts per document
    mc_res = await db.execute(
        select(ActorMention.document_id, func.count(ActorMention.id))
        .where(ActorMention.document_id.in_([d.id for d in docs]) if docs else False)
        .group_by(ActorMention.document_id)
    )
    mention_counts = {row[0]: row[1] for row in mc_res.fetchall()}

    phase_counts: dict = {}
    success = 0
    fail = 0
    in_flight = 0
    out_docs: List[IngestStatusDocument] = []
    TERMINAL_SUCCESS = {"ingest_complete"}
    TERMINAL_NEUTRAL = {"extract_skipped"}
    TERMINAL_FAIL = {"ingest_failed"}
    for d in docs:
        phase_counts[d.ingest_phase] = phase_counts.get(d.ingest_phase, 0) + 1
        if d.ingest_phase in TERMINAL_SUCCESS:
            success += 1
        elif d.ingest_phase in TERMINAL_FAIL:
            fail += 1
        elif d.ingest_phase not in TERMINAL_NEUTRAL:
            in_flight += 1
        out_docs.append(IngestStatusDocument(
            id=d.id,
            filename=d.filename,
            folder=d.folder,
            file_type=d.file_type,
            ingest_phase=d.ingest_phase,
            ingest_started_at=d.ingest_started_at,
            ingest_finished_at=d.ingest_finished_at,
            error_detail=d.ingest_error_detail,
            actor_mention_count=mention_counts.get(d.id, 0),
            extraction_status=d.extraction_status or "NOT_ATTEMPTED",
            extraction_method=d.extraction_method,
            extraction_confidence=d.extraction_confidence or 0.0,
            is_scanned_pdf=bool(d.is_scanned_pdf),
        ))

    return IngestStatusResponse(
        case_id=case_id,
        phase_counts=phase_counts,
        success_count=success,
        failure_count=fail,
        in_flight_count=in_flight,
        documents=out_docs,
    )


@router.get("/case/{case_id}/archives", response_model=List[UploadArchiveResponse])
async def list_archives(case_id: int, db: AsyncSession = Depends(get_db)):
    await _case_or_404(db, case_id)
    res = await db.execute(
        select(UploadArchive).where(UploadArchive.case_id == case_id)
    )
    return list(res.scalars().all())


# ---------------- duplicate detection ----------------

@router.post("/case/{case_id}/check-hashes", response_model=CheckHashesResponse)
async def check_hashes(
    case_id: int,
    body: CheckHashesRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Given a list of sha256 hashes, return which ones already correspond to
    existing documents in this case. Client computes hashes with
    SubtleCrypto before uploading to warn the user about duplicates.
    """
    await _case_or_404(db, case_id)
    cleaned = [h.strip().lower() for h in (body.sha256_list or []) if h]
    if not cleaned:
        return CheckHashesResponse(case_id=case_id, duplicates=[])
    res = await db.execute(
        select(Document)
        .where(Document.case_id == case_id)
        .where(Document.sha256_hash.in_(cleaned))
    )
    hits = []
    for d in res.scalars().all():
        hits.append(HashCheckHit(
            sha256_hash=d.sha256_hash,
            document_id=d.id,
            filename=d.filename,
            folder=d.folder,
            ingest_phase=d.ingest_phase,
        ))
    return CheckHashesResponse(case_id=case_id, duplicates=hits)


# ---------------- delete ----------------

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    """
    Remove a Document row. If no other Document in any case still references
    the same sha256 bytes, remove the file from storage as well. Archive files
    are never auto-deleted (they are tracked by UploadArchive independently).
    """
    res = await db.execute(select(Document).where(Document.id == doc_id))
    doc = res.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    storage_path = doc.storage_path
    sha = doc.sha256_hash

    await db.delete(doc)
    await db.flush()

    # If no other Document row references the same sha256, delete the backing file.
    if sha:
        remaining = await db.execute(
            select(Document).where(Document.sha256_hash == sha).limit(1)
        )
        if remaining.scalar_one_or_none() is None and storage_path:
            try:
                from pathlib import Path as _P
                p = _P(storage_path)
                if p.is_file():
                    p.unlink()
            except Exception:
                # Non-fatal; row is already gone. Storage GC is advisory.
                pass

    await db.commit()
    return None
