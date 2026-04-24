"""
Ingest pipeline — the ONLY path that runs on save/upload.

Stages (strict order):
  uploaded -> hashed -> extracting -> extracted -> normalized
           -> indexed -> actor_extraction_running -> actors_extracted
           -> ingest_complete

Failure modes:
  ingest_failed (with error_detail) — fatal error
  extract_skipped                    — unsupported type (not a failure)

SR-12: this module MUST NOT import any analytical / resolver modules (see the
contract rules doc). The import audit (dev_sr12_audit.py) enforces this at
test time.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models import (
    Actor,
    ActorMention,
    Case,
    Document,
    IngestEvent,
)
from .actor_extractor import (
    ExtractedActor,
    canonicalize,
    extract_actors,
    resolve_against_existing,
)
from .content_extractors import (
    ExtractorUnsupported,
    ExtractionResult,
    build_index,
    detect_file_type,
    extract_text,
    normalize,
)

log = logging.getLogger("ingest")


# ------------- phase constants -------------

PH_UPLOADED = "uploaded"
PH_HASHED = "hashed"
PH_EXTRACTING = "extracting"
PH_EXTRACTED = "extracted"
PH_NORMALIZED = "normalized"
PH_INDEXED = "indexed"
PH_ACTOR_RUNNING = "actor_extraction_running"
PH_ACTORS_EXTRACTED = "actors_extracted"
PH_COMPLETE = "ingest_complete"
PH_SKIPPED = "extract_skipped"
PH_FAILED = "ingest_failed"


async def _set_phase(
    db: AsyncSession, doc: Document, to_phase: str, error: Optional[str] = None
) -> None:
    frm = doc.ingest_phase
    doc.ingest_phase = to_phase
    if error:
        doc.ingest_error_detail = error
    db.add(IngestEvent(
        document_id=doc.id,
        case_id=doc.case_id,
        from_phase=frm,
        to_phase=to_phase,
        error_detail=error,
        at=datetime.utcnow(),
    ))


async def seed_case_actors(db: AsyncSession, case: Case) -> None:
    """
    Ensure Case.plaintiff / defendant / court exist as RESOLVED actors with the
    right role_hint. If a matching canonical row already exists (e.g. created
    by interview extraction), enrich it in place — the
    (case_id, canonical_name) unique constraint requires it.
    """
    seeds = [
        (case.plaintiff, "PERSON", "plaintiff"),
        (case.defendant, "PERSON", "defendant"),
        (case.court, "ORGANIZATION", "court"),
    ]
    for name, entity_type, role_hint in seeds:
        if not name:
            continue
        canon = canonicalize(name)
        if not canon:
            continue
        existing = await db.execute(
            select(Actor).where(Actor.case_id == case.id).where(Actor.canonical_name == canon)
        )
        existing_row = existing.scalar_one_or_none()
        if existing_row is not None:
            if existing_row.resolution_state != "RESOLVED":
                existing_row.resolution_state = "RESOLVED"
            if not existing_row.role_hint:
                existing_row.role_hint = role_hint
            if existing_row.entity_type != entity_type:
                existing_row.entity_type = entity_type
            existing_row.updated_at = datetime.utcnow()
            continue
        db.add(Actor(
            case_id=case.id,
            display_name=name,
            canonical_name=canon,
            entity_type=entity_type,
            resolution_state="RESOLVED",
            role_hint=role_hint,
            mention_count=0,
            source="SEED",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ))
    await db.flush()


async def _load_existing_actor_map(db: AsyncSession, case_id: int) -> dict:
    res = await db.execute(select(Actor).where(Actor.case_id == case_id))
    return {a.canonical_name: a.id for a in res.scalars().all()}


def hash_file(storage_path: str) -> str:
    h = hashlib.sha256()
    with open(storage_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


async def _process_one(db: AsyncSession, doc: Document) -> None:
    """Run all ingest stages for a single Document."""
    doc.ingest_started_at = datetime.utcnow()

    # Stage 1: uploaded -> hashed
    if not doc.sha256_hash and doc.storage_path and Path(doc.storage_path).is_file():
        doc.sha256_hash = hash_file(doc.storage_path)
    await _set_phase(db, doc, PH_HASHED)

    # Stage 2: file_type detection (if missing) + extracting
    if not doc.file_type:
        doc.file_type = detect_file_type(doc.filename)
    await _set_phase(db, doc, PH_EXTRACTING)

    # Stage 3: extract
    extraction: Optional[ExtractionResult] = None
    if doc.storage_path and Path(doc.storage_path).is_file():
        try:
            extraction = extract_text(doc.storage_path, doc.file_type)
        except ExtractorUnsupported as e:
            # Images land here: OCR is not implemented. Record that explicitly.
            doc.extraction_status = (
                "OCR_REQUIRED" if doc.file_type == "image" else "UNSUPPORTED_TYPE"
            )
            doc.extraction_method = None
            doc.extraction_confidence = 0.0
            await _set_phase(db, doc, PH_SKIPPED, error=str(e))
            doc.ingest_finished_at = datetime.utcnow()
            return
        except Exception as e:
            doc.extraction_status = "EXTRACTION_FAILED"
            doc.extraction_confidence = 0.0
            await _set_phase(db, doc, PH_FAILED, error=f"{type(e).__name__}: {e}")
            doc.ingest_finished_at = datetime.utcnow()
            return
    else:
        # No file on disk but text_content may already be seeded; fall through.
        if doc.text_content:
            extraction = ExtractionResult(
                text=doc.text_content,
                char_count=len(doc.text_content),
                engine="preseeded",
                status="TEXT_EXTRACTION_COMPLETE",
                confidence=0.7,
            )
        else:
            doc.extraction_status = "UNSUPPORTED_TYPE"
            doc.extraction_confidence = 0.0
            await _set_phase(db, doc, PH_SKIPPED, error="no storage_path and no text_content")
            doc.ingest_finished_at = datetime.utcnow()
            return

    # Persist extraction reliability fields
    doc.extraction_method = extraction.engine
    doc.extraction_confidence = extraction.confidence
    doc.is_scanned_pdf = extraction.is_scanned_pdf
    doc.extraction_status = extraction.status

    # Scanned-only PDF: do not claim success; mark OCR_REQUIRED and stop here.
    if extraction.status == "OCR_REQUIRED":
        await _set_phase(
            db, doc, PH_SKIPPED,
            error=f"OCR_REQUIRED: {extraction.notes or 'scanned PDF detected'}",
        )
        doc.ingest_finished_at = datetime.utcnow()
        return
    if extraction.status == "EXTRACTION_FAILED":
        await _set_phase(
            db, doc, PH_FAILED,
            error=extraction.notes or "extractor produced no text",
        )
        doc.ingest_finished_at = datetime.utcnow()
        return

    doc.text_content = extraction.text
    doc.char_count = extraction.char_count
    await _set_phase(db, doc, PH_EXTRACTED)

    # Stage 4: normalize
    normalized = normalize(doc.text_content)
    doc.text_content = normalized
    doc.char_count = len(normalized)
    await _set_phase(db, doc, PH_NORMALIZED)

    # Stage 5: index (write small index onto ingest events for audit)
    idx = build_index(normalized)
    db.add(IngestEvent(
        document_id=doc.id,
        case_id=doc.case_id,
        from_phase=PH_NORMALIZED,
        to_phase="indexed_detail",
        error_detail=None,
        at=datetime.utcnow(),
    ))
    await _set_phase(db, doc, PH_INDEXED)

    # Stage 6: actor extraction
    await _set_phase(db, doc, PH_ACTOR_RUNNING)
    extracted = extract_actors(normalized)
    if extracted:
        existing = await _load_existing_actor_map(db, doc.case_id)
        resolved = resolve_against_existing(extracted, existing)
        for ex, existing_id, state in resolved:
            await _persist_extracted_actor(db, doc, ex, existing_id, state)

    await _set_phase(db, doc, PH_ACTORS_EXTRACTED)
    # Final extraction status check: refuse to mark ingest_complete with zero chars.
    if (doc.char_count or 0) == 0:
        doc.extraction_status = "EXTRACTION_FAILED"
        await _set_phase(
            db, doc, PH_FAILED,
            error="normalized text is empty after extraction — refusing to mark complete",
        )
        doc.ingest_finished_at = datetime.utcnow()
        return
    await _set_phase(db, doc, PH_COMPLETE)
    doc.ingest_finished_at = datetime.utcnow()


async def _persist_extracted_actor(
    db: AsyncSession,
    doc: Document,
    ex: ExtractedActor,
    existing_actor_id: Optional[int],
    state: str,
) -> None:
    """Create Actor (if new) or increment mention_count; always write ActorMention."""
    actor_id = existing_actor_id
    if actor_id is None:
        new_actor = Actor(
            case_id=doc.case_id,
            display_name=ex.display_name,
            canonical_name=ex.canonical,
            entity_type=ex.entity_type,
            resolution_state=state,  # CANDIDATE or AMBIGUOUS
            role_hint=None,
            mention_count=1,
            first_seen_document_id=doc.id,
            last_seen_document_id=doc.id,
            source="INGEST",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_actor)
        await db.flush()
        actor_id = new_actor.id
    else:
        res = await db.execute(select(Actor).where(Actor.id == actor_id))
        actor = res.scalar_one_or_none()
        if actor is not None:
            actor.mention_count = (actor.mention_count or 0) + 1
            actor.last_seen_document_id = doc.id
            actor.updated_at = datetime.utcnow()
            # Never downgrade a RESOLVED actor to CANDIDATE.

    db.add(ActorMention(
        actor_id=actor_id,
        document_id=doc.id,
        snippet=ex.snippet,
        offset_start=ex.offset_start,
        offset_end=ex.offset_end,
        confidence=ex.confidence,
        created_at=datetime.utcnow(),
    ))


async def run_ingest(case_id: int, document_ids: List[int]) -> None:
    """
    Background task entry. Opens its own session; the HTTP handler has already
    returned by the time this runs.
    """
    async with AsyncSessionLocal() as db:
        case = (await db.execute(select(Case).where(Case.id == case_id))).scalar_one_or_none()
        if case is None:
            return
        await seed_case_actors(db, case)
        await db.commit()

        for doc_id in document_ids:
            async with AsyncSessionLocal() as idb:
                res = await idb.execute(select(Document).where(Document.id == doc_id))
                doc = res.scalar_one_or_none()
                if doc is None:
                    continue
                try:
                    await _process_one(idb, doc)
                    await idb.commit()
                except Exception as exc:
                    await idb.rollback()
                    log.exception("ingest failed for doc_id=%s", doc_id)
                    async with AsyncSessionLocal() as fdb:
                        res2 = await fdb.execute(select(Document).where(Document.id == doc_id))
                        d2 = res2.scalar_one_or_none()
                        if d2 is not None:
                            d2.ingest_phase = PH_FAILED
                            d2.ingest_error_detail = f"{type(exc).__name__}: {exc}"
                            d2.ingest_finished_at = datetime.utcnow()
                            fdb.add(IngestEvent(
                                document_id=doc_id,
                                case_id=case_id,
                                from_phase="unknown",
                                to_phase=PH_FAILED,
                                error_detail=d2.ingest_error_detail,
                                at=datetime.utcnow(),
                            ))
                            await fdb.commit()
