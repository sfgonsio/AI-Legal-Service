"""
Timeline routes.

GET  /timeline/{case_id}            — ordered events grouped by date
POST /timeline/{case_id}/build      — (re)build from interview + docs on demand

Never invokes the authority resolver. Never triggers legal analysis.
"""
from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Actor, Case, TimelineEvent
from schemas import (
    TimelineActorRef,
    TimelineBuildRequest,
    TimelineBuildResponse,
    TimelineDateGroup,
    TimelineEventLegalMappingResponse,
    TimelineEventResponse,
    TimelineResponse,
    TimelineStrategyFlags,
)
from brain.timeline_builder import build_for_case


router = APIRouter(prefix="/timeline", tags=["timeline"])


async def _case_or_404(db: AsyncSession, case_id: int) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if case is None:
        raise HTTPException(404, "case not found")
    return case


def _group_key(ev: TimelineEvent) -> str:
    if ev.timestamp is None:
        return "UNKNOWN"
    if ev.date_precision == "DAY":
        return ev.timestamp.strftime("%Y-%m-%d")
    if ev.date_precision == "MONTH":
        return ev.timestamp.strftime("%Y-%m")
    if ev.date_precision == "YEAR":
        return ev.timestamp.strftime("%Y")
    return "UNKNOWN"


def _group_label(key: str, precision: str) -> str:
    if key == "UNKNOWN":
        return "Undated"
    try:
        if precision == "DAY":
            return datetime.strptime(key, "%Y-%m-%d").strftime("%B %d, %Y")
        if precision == "MONTH":
            return datetime.strptime(key, "%Y-%m").strftime("%B %Y")
        if precision == "YEAR":
            return key
    except ValueError:
        pass
    return key


def _sort_key(ev: TimelineEvent) -> tuple:
    # Sort by (has_timestamp desc, timestamp asc, created asc). UNKNOWN goes last.
    if ev.timestamp is None:
        return (1, datetime.max, ev.id)
    return (0, ev.timestamp, ev.id)


@router.get("/{case_id}", response_model=TimelineResponse)
async def get_timeline(
    case_id: int,
    source: Optional[str] = None,
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    await _case_or_404(db, case_id)

    q = (
        select(TimelineEvent)
        .where(TimelineEvent.case_id == case_id)
        .options(selectinload(TimelineEvent.legal_mappings))
    )
    if source:
        q = q.where(TimelineEvent.source == source.upper())
    if event_type:
        q = q.where(TimelineEvent.event_type == event_type.upper())

    res = await db.execute(q)
    events: List[TimelineEvent] = list(res.scalars().all())
    events.sort(key=_sort_key)

    # Resolve actor names for display (one query, not per-event).
    actor_ids = set()
    for ev in events:
        for aid in (ev.actor_ids or []):
            actor_ids.add(aid)
    actor_rows: Dict[int, Actor] = {}
    if actor_ids:
        a_res = await db.execute(select(Actor).where(Actor.id.in_(list(actor_ids))))
        for a in a_res.scalars().all():
            actor_rows[a.id] = a

    # Build groups preserving sort order
    grouped: "OrderedDict[str, List[TimelineEvent]]" = OrderedDict()
    precision_map: Dict[str, str] = {}
    for ev in events:
        k = _group_key(ev)
        grouped.setdefault(k, []).append(ev)
        # Highest precision wins per group (DAY > MONTH > YEAR > UNKNOWN)
        prev = precision_map.get(k, "UNKNOWN")
        rank = {"DAY": 3, "MONTH": 2, "YEAR": 1, "UNKNOWN": 0}
        if rank[ev.date_precision] >= rank[prev]:
            precision_map[k] = ev.date_precision

    out_groups: List[TimelineDateGroup] = []
    for k, evs in grouped.items():
        precision = precision_map.get(k, "UNKNOWN")
        evs_out: List[TimelineEventResponse] = []
        for ev in evs:
            refs = []
            for aid in (ev.actor_ids or []):
                a = actor_rows.get(aid)
                if a:
                    refs.append(TimelineActorRef(
                        id=a.id, display_name=a.display_name, role_hint=a.role_hint
                    ))
            mappings = [
                TimelineEventLegalMappingResponse(
                    legal_element_type=m.legal_element_type,
                    element_reference=m.element_reference,
                    element_label=m.element_label,
                    confidence=m.confidence,
                    rationale=m.rationale,
                    supporting_evidence_refs=list(m.supporting_evidence_refs or []),
                )
                for m in sorted(
                    ev.legal_mappings or [],
                    key=lambda x: (-x.confidence, x.legal_element_type),
                )
            ]
            evs_out.append(TimelineEventResponse(
                event_id=ev.event_id,
                case_id=ev.case_id,
                timestamp=ev.timestamp,
                raw_date_text=ev.raw_date_text,
                date_precision=ev.date_precision,
                summary=ev.summary,
                event_type=ev.event_type,
                source=ev.source,
                source_document_id=ev.source_document_id,
                source_interview_id=ev.source_interview_id,
                text_offset_start=ev.text_offset_start,
                text_offset_end=ev.text_offset_end,
                snippet=ev.snippet,
                actor_ids=list(ev.actor_ids or []),
                actors=refs,
                confidence=ev.confidence,
                claim_relation=ev.claim_relation or "NEUTRAL",
                strategy=TimelineStrategyFlags(
                    deposition_target=bool(ev.deposition_target),
                    interrogatory_target=bool(ev.interrogatory_target),
                    document_request_target=bool(ev.document_request_target),
                ),
                strategy_rationale=ev.strategy_rationale,
                legal_mappings=mappings,
            ))
        out_groups.append(TimelineDateGroup(
            key=k, label=_group_label(k, precision),
            precision=precision, events=evs_out,
        ))

    counts_by_source: Dict[str, int] = {}
    counts_by_type: Dict[str, int] = {}
    known = 0; unknown = 0
    last_built: Optional[datetime] = None
    for ev in events:
        counts_by_source[ev.source] = counts_by_source.get(ev.source, 0) + 1
        counts_by_type[ev.event_type] = counts_by_type.get(ev.event_type, 0) + 1
        if ev.timestamp is not None:
            known += 1
        else:
            unknown += 1
        if last_built is None or (ev.created_at and ev.created_at > last_built):
            last_built = ev.created_at

    return TimelineResponse(
        case_id=case_id,
        total=len(events),
        counts_by_source=counts_by_source,
        counts_by_type=counts_by_type,
        known_count=known,
        unknown_count=unknown,
        groups=out_groups,
        last_built_at=last_built,
    )


@router.post("/{case_id}/build", response_model=TimelineBuildResponse, status_code=202)
async def build_timeline(
    case_id: int,
    body: TimelineBuildRequest = TimelineBuildRequest(),
    db: AsyncSession = Depends(get_db),
):
    """
    Rebuild timeline events for a case from its current interview + document
    content. Synchronous build — returns when complete. Counts in the response
    are the exact counts written.
    """
    await _case_or_404(db, case_id)
    result = await build_for_case(case_id, replace=body.replace)
    return TimelineBuildResponse(**result)
