"""
Case authority decision routes.

Append-only decision writes; resolver reads; Legal Library list of provisional
candidates. Decision writes enforce the ACCEPTED-over-BLOCKED safety rule and
emit a recompute event (handled by brain.recompute).
"""
import hashlib
import json
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import CaseAuthorityDecision, Case
from schemas import (
    CaseAuthorityDecisionCreate,
    CaseAuthorityDecisionResponse,
    ResolveRequest,
    ResolvedAuthorityBlock,
    ProvisionalCaciSummary,
    CaseToAuthorityRow,
)
from brain.authority_resolver import (
    resolve_authority,
    DEC_ACCEPTED,
    DEC_REJECTED,
    DEC_REPLACED,
    DEC_PENDING,
    STATUS_BLOCKED,
)
from brain.provisional_store import load_active_record, load_record_by_id, _manifest
from brain.recompute import recompute_for_decision
from brain import state_machine as sm


router = APIRouter(prefix="/case-authority", tags=["case-authority"])


async def _require_case_state(db: AsyncSession, case_id: int, allowed: set) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "case not found")
    if case.save_state not in allowed:
        raise HTTPException(
            409,
            detail={
                "detail": "case_state_not_allowed",
                "save_state": case.save_state,
                "required_states": sorted(list(allowed)),
                "message": f"This endpoint is only available in states: {sorted(list(allowed))}",
            },
        )
    return case


# ---------- helpers ----------

def _canonical_hash(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _serialize_decision(row: CaseAuthorityDecision) -> dict:
    return {
        "id": row.id,
        "decision_id": row.decision_id,
        "case_id": row.case_id,
        "caci_id": row.caci_id,
        "state": row.state,
        "pinned_record_id": row.pinned_record_id,
        "replacement": row.replacement_json,
        "decided_by_actor_type": row.decided_by_actor_type,
        "decided_by_actor_id": row.decided_by_actor_id,
        "decided_by_role": row.decided_by_role,
        "decided_at": row.decided_at,
        "rationale": row.rationale,
        "supersedes_decision_id": row.supersedes_decision_id,
        "superseded_by_decision_id": row.superseded_by_decision_id,
        "audit_hash": row.audit_hash,
        "source_event": row.source_event,
    }


# ---------- decisions ----------

@router.post("/decisions", response_model=CaseAuthorityDecisionResponse, status_code=201)
async def create_decision(
    body: CaseAuthorityDecisionCreate, db: AsyncSession = Depends(get_db)
):
    """
    Append a new case authority decision. Supersedes any prior non-superseded
    decision for (case_id, caci_id). Enforces safety rules at write time.
    """
    # Validate case exists and is in REVIEW_REQUIRED (the only state
    # in which attorney decisions may be written; per SR-11).
    await _require_case_state(db, body.case_id, {sm.REVIEW_REQUIRED})

    # Validate decision state
    if body.state not in {DEC_PENDING, DEC_ACCEPTED, DEC_REJECTED, DEC_REPLACED}:
        raise HTTPException(400, f"invalid state: {body.state}")

    # State-specific validation
    if body.state == DEC_ACCEPTED:
        if not body.pinned_record_id:
            raise HTTPException(400, "ACCEPTED requires pinned_record_id")
        pinned = load_record_by_id(body.caci_id, body.pinned_record_id)
        if pinned is None:
            raise HTTPException(400, "pinned_record_id not found in provisional store")
        if pinned.get("status") == STATUS_BLOCKED:
            raise HTTPException(
                409,
                "ERROR_ACCEPTED_OVER_BLOCKED: cannot accept a BLOCKED_UNTRUSTED record",
            )

    if body.state == DEC_REPLACED and not body.replacement:
        raise HTTPException(400, "REPLACED requires replacement payload")

    if body.state == DEC_REJECTED and not body.rationale:
        raise HTTPException(400, "REJECTED requires rationale")

    # Find prior non-superseded decision for same (case_id, caci_id)
    prior_stmt = (
        select(CaseAuthorityDecision)
        .where(CaseAuthorityDecision.case_id == body.case_id)
        .where(CaseAuthorityDecision.caci_id == body.caci_id)
        .where(CaseAuthorityDecision.superseded_by_decision_id.is_(None))
        .order_by(desc(CaseAuthorityDecision.decided_at))
        .limit(1)
    )
    prior_res = await db.execute(prior_stmt)
    prior = prior_res.scalar_one_or_none()

    decision_id = str(uuid.uuid4())
    decided_at = datetime.utcnow()

    pinned_record_id = body.pinned_record_id
    if pinned_record_id is None and body.state == DEC_PENDING:
        active = load_active_record(body.caci_id)
        pinned_record_id = (active or {}).get("record_id")

    replacement_json = body.replacement.model_dump() if body.replacement else None

    canonical = {
        "case_id": body.case_id,
        "caci_id": body.caci_id,
        "state": body.state,
        "pinned_record_id": pinned_record_id,
        "replacement": replacement_json,
        "decided_by": {
            "actor_type": body.decided_by_actor_type,
            "actor_id": body.decided_by_actor_id,
            "role": body.decided_by_role,
        },
        "decided_at": decided_at.isoformat() + "Z",
        "rationale": body.rationale,
        "supersedes_decision_id": prior.decision_id if prior else None,
    }
    audit_hash = _canonical_hash(canonical)

    new_row = CaseAuthorityDecision(
        decision_id=decision_id,
        case_id=body.case_id,
        caci_id=body.caci_id,
        state=body.state,
        pinned_record_id=pinned_record_id,
        replacement_json=replacement_json,
        decided_by_actor_type=body.decided_by_actor_type,
        decided_by_actor_id=body.decided_by_actor_id,
        decided_by_role=body.decided_by_role,
        decided_at=decided_at,
        rationale=body.rationale,
        supersedes_decision_id=prior.decision_id if prior else None,
        superseded_by_decision_id=None,
        audit_hash=audit_hash,
        source_event=body.source_event,
    )
    db.add(new_row)

    if prior:
        prior.superseded_by_decision_id = decision_id

    await db.commit()
    await db.refresh(new_row)

    # Trigger downstream recompute (COA/burden/remedy/complaint/case-to-authority).
    await recompute_for_decision(db, new_row)

    return _serialize_decision(new_row)


@router.get(
    "/decisions/case/{case_id}",
    response_model=List[CaseAuthorityDecisionResponse],
)
async def list_case_decisions(
    case_id: int,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CaseAuthorityDecision).where(CaseAuthorityDecision.case_id == case_id)
    if active_only:
        stmt = stmt.where(CaseAuthorityDecision.superseded_by_decision_id.is_(None))
    stmt = stmt.order_by(desc(CaseAuthorityDecision.decided_at))
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [_serialize_decision(r) for r in rows]


@router.get(
    "/decisions/case/{case_id}/caci/{caci_id}/history",
    response_model=List[CaseAuthorityDecisionResponse],
)
async def decision_history(
    case_id: int, caci_id: str, db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(CaseAuthorityDecision)
        .where(CaseAuthorityDecision.case_id == case_id)
        .where(CaseAuthorityDecision.caci_id == caci_id)
        .order_by(desc(CaseAuthorityDecision.decided_at))
    )
    res = await db.execute(stmt)
    return [_serialize_decision(r) for r in res.scalars().all()]


# ---------- resolver ----------

@router.post("/resolve", response_model=ResolvedAuthorityBlock)
async def resolve(body: ResolveRequest, db: AsyncSession = Depends(get_db)):
    # Resolver is gated behind post-analysis state. Live resolver calls only
    # happen inside the analysis runner and decision-write path.
    await _require_case_state(db, body.case_id, sm.POST_ANALYSIS_STATES)
    r = await resolve_authority(db, body.case_id, body.caci_id)
    return r.to_dict()


@router.get("/resolve/case/{case_id}/caci/{caci_id}", response_model=ResolvedAuthorityBlock)
async def resolve_get(case_id: int, caci_id: str, db: AsyncSession = Depends(get_db)):
    await _require_case_state(db, case_id, sm.POST_ANALYSIS_STATES)
    r = await resolve_authority(db, case_id, caci_id)
    return r.to_dict()


# ---------- Legal Library list ----------

@router.get("/library/provisional", response_model=List[ProvisionalCaciSummary])
async def list_provisional_library():
    """List all active provisional CACI records for Legal Library display."""
    manifest = _manifest()
    out: List[ProvisionalCaciSummary] = []
    for caci_id, entry in (manifest.get("records") or {}).items():
        record = load_active_record(caci_id) or {}
        out.append(ProvisionalCaciSummary(
            caci_id=caci_id,
            record_id=record.get("record_id") or entry.get("record_id") or "",
            title=(record.get("payload") or {}).get("title", caci_id),
            status=record.get("status") or entry.get("status") or "PROVISIONAL",
            confidence_overall=(record.get("confidence") or {}).get("overall") or entry.get("confidence_overall") or 0.0,
            canonical=False,
            replaceable=True,
        ))
    return out


# ---------- Case-to-authority mapping ----------

@router.get("/case/{case_id}/map", response_model=List[CaseToAuthorityRow])
async def case_authority_map(case_id: int, db: AsyncSession = Depends(get_db)):
    """
    For the case, return the resolved authority for every CACI currently known
    to the provisional store. Attorneys use this as the review surface.

    Gated: only available when case is in a post-analysis state. Resolver is
    invoked here because the attorney review UI legitimately reads live state
    while decisioning is in progress (REVIEW_REQUIRED), and this route is the
    read half of the decisioning loop.
    """
    await _require_case_state(db, case_id, sm.POST_ANALYSIS_STATES)
    manifest = _manifest()
    rows: List[CaseToAuthorityRow] = []
    for caci_id in (manifest.get("records") or {}).keys():
        r = await resolve_authority(db, case_id, caci_id)
        rows.append(CaseToAuthorityRow(caci_id=caci_id, authority=r.to_dict()))
    return rows
