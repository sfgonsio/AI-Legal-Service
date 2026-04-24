"""
Timeline builder — per-case extraction orchestrator.

Reads:
  - all Interview rows for the case (narrative + joined Q&A)
  - all Document rows for the case (normalized text_content)

Writes:
  - TimelineEvent rows (new uuid per event). On rebuild (default), deletes all
    prior TimelineEvent rows for the case first so sourcing is coherent.

Does NOT touch: authority resolver, COA engine, burden/remedy/complaint.
Does NOT modify the ingest pipeline. Triggered on demand via
POST /timeline/{case_id}/build.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models import (
    Actor, Case, Document, Interview,
    TimelineEvent, TimelineEventLegalMapping,
)
from .actor_extractor import canonicalize
from .timeline_extractor import ExtractedEvent, extract_events
from .timeline_legal_mapper import analyze_event


async def _load_actor_map(db: AsyncSession, case_id: int) -> Dict[str, int]:
    """canonical_name -> actor_id for this case."""
    res = await db.execute(select(Actor).where(Actor.case_id == case_id))
    return {a.canonical_name: a.id for a in res.scalars().all()}


def _link_names_to_actors(names: Iterable[str], actor_map: Dict[str, int]) -> List[int]:
    """Map each name to an actor_id using the same canonicalization the
    extractor uses — no new actor rows created here (we do NOT duplicate
    actors; the actor roster is built by ingest + interview paths)."""
    out: List[int] = []
    seen = set()
    for nm in names:
        canon = canonicalize(nm)
        if not canon:
            continue
        # Exact canonical match first
        if canon in actor_map:
            aid = actor_map[canon]
            if aid not in seen:
                out.append(aid)
                seen.add(aid)
            continue
        # Substring containment: attorney names are often nicknamed in docs.
        # Pick a unique match if exactly one, else skip (avoid false positives).
        candidates = [aid for c, aid in actor_map.items()
                      if c != canon and (canon in c or c in canon)]
        if len(candidates) == 1:
            aid = candidates[0]
            if aid not in seen:
                out.append(aid)
                seen.add(aid)
    return out


def _interview_text(iv: Interview, questions) -> str:
    if iv.mode == "FREEFORM_NARRATIVE":
        return iv.narrative_text or ""
    parts: List[str] = []
    for q in sorted(questions or [], key=lambda x: x.order_index):
        if q.answer_text:
            parts.append(f"Q: {q.prompt}\nA: {q.answer_text}")
    return "\n\n".join(parts)


async def build_for_case(case_id: int, replace: bool = True) -> Dict[str, int]:
    """
    Rebuild the timeline for a case. Returns counters for the builder response.

    - replace=True (default): delete all existing TimelineEvent rows for the
      case, then extract fresh events. The right call when evidence changed.
    - replace=False: append-only; duplicates are possible. Kept as an option
      for append workflows (not used by the default /build route).
    """
    t0 = time.perf_counter()
    created = 0
    removed = 0
    docs_scanned = 0
    ivs_scanned = 0

    async with AsyncSessionLocal() as db:
        case = (await db.execute(select(Case).where(Case.id == case_id))).scalar_one_or_none()
        if case is None:
            return {
                "case_id": case_id, "events_created": 0, "events_removed": 0,
                "documents_scanned": 0, "interviews_scanned": 0, "duration_ms": 0,
            }

        if replace:
            # Count then delete
            existing = (await db.execute(
                select(TimelineEvent.id).where(TimelineEvent.case_id == case_id)
            )).scalars().all()
            removed = len(existing)
            await db.execute(delete(TimelineEvent).where(TimelineEvent.case_id == case_id))

        actor_map = await _load_actor_map(db, case_id)

        # --- Interviews ---
        from sqlalchemy.orm import selectinload
        iv_res = await db.execute(
            select(Interview)
            .where(Interview.case_id == case_id)
            .options(selectinload(Interview.questions))
        )
        for iv in iv_res.scalars().all():
            ivs_scanned += 1
            text = _interview_text(iv, iv.questions)
            if not text:
                continue
            for ex in extract_events(text):
                await _persist(db, case_id, ex, actor_map,
                               source="INTERVIEW",
                               source_interview_id=iv.id,
                               source_document_id=None)
                created += 1

        # --- Documents ---
        doc_res = await db.execute(
            select(Document).where(Document.case_id == case_id)
        )
        for doc in doc_res.scalars().all():
            docs_scanned += 1
            text = doc.text_content or ""
            if not text:
                continue
            for ex in extract_events(text):
                await _persist(db, case_id, ex, actor_map,
                               source="INGEST",
                               source_interview_id=None,
                               source_document_id=doc.id)
                created += 1

        await db.commit()

    duration_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "case_id": case_id,
        "events_created": created,
        "events_removed": removed,
        "documents_scanned": docs_scanned,
        "interviews_scanned": ivs_scanned,
        "duration_ms": duration_ms,
    }


async def _persist(
    db: AsyncSession,
    case_id: int,
    ex: ExtractedEvent,
    actor_map: Dict[str, int],
    *,
    source: str,
    source_interview_id: Optional[int],
    source_document_id: Optional[int],
) -> None:
    actor_ids = _link_names_to_actors(ex.mentioned_names, actor_map)

    # Heuristic legal layer — candidate mappings + strategy flags. This is
    # pre-analysis and MUST NOT touch the authority resolver.
    hints = analyze_event(ex)

    ev = TimelineEvent(
        event_id=str(uuid.uuid4()),
        case_id=case_id,
        timestamp=ex.timestamp,
        raw_date_text=ex.raw_date_text,
        date_precision=ex.date_precision,
        summary=ex.summary,
        event_type=ex.event_type,
        source=source,
        source_document_id=source_document_id,
        source_interview_id=source_interview_id,
        text_offset_start=ex.offset_start,
        text_offset_end=ex.offset_end,
        snippet=ex.snippet,
        actor_ids=actor_ids,
        confidence=ex.confidence,
        claim_relation=hints.claim_relation,
        deposition_target=hints.strategy.deposition_target,
        interrogatory_target=hints.strategy.interrogatory_target,
        document_request_target=hints.strategy.document_request_target,
        strategy_rationale=hints.strategy.rationale or None,
        created_at=datetime.utcnow(),
    )
    db.add(ev)
    await db.flush()

    # Attach back-pointing evidence refs so the attorney can drill down.
    ev_ref = {"event_id": ev.event_id}
    if source_document_id is not None:
        ev_ref["source_document_id"] = source_document_id
    if source_interview_id is not None:
        ev_ref["source_interview_id"] = source_interview_id

    for m in hints.mappings:
        db.add(TimelineEventLegalMapping(
            event_id=ev.id,
            legal_element_type=m.legal_element_type,
            element_reference=m.element_reference,
            element_label=m.element_label,
            confidence=m.confidence,
            rationale=m.rationale,
            supporting_evidence_refs=[ev_ref],
            created_at=datetime.utcnow(),
        ))
