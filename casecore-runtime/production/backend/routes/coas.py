"""
Cause of Action routes.

COA responses carry a resolved authority block populated from the snapshot
columns on the COA row. The Brain authority resolver is NEVER invoked from
this module — resolution only happens inside brain.analysis_runner or on
decision writes. This enforces the ingest-vs-analysis separation.

Endpoints that expose authority are gated on case.save_state.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models import COA, Case
from schemas import COAResponse, COADetailResponse
from brain import state_machine as sm

router = APIRouter(prefix="/coas", tags=["coas"])


def _snapshot_authority(coa: COA) -> dict:
    """Build the ResolvedAuthorityBlock from COA snapshot columns only.

    If the case has never been analyzed, snapshot columns are null and the
    block reports NONE / pre-analysis. We never call the resolver here.
    """
    eg = coa.authority_effective_grounding or "NONE"
    decision_id = coa.authority_decision_id
    pinned = coa.authority_pinned_record_id
    return {
        "certified": {"present": False, "authority_id": None, "record_ref": None},
        "provisional_candidate": {
            "caci_id": coa.caci_ref,
            "record_id": pinned,
            "confidence": None,
            "status": None,
        },
        "case_decision": {
            "state": "ACCEPTED" if eg == "GROUNDED" else
                     "REPLACED" if eg == "GROUNDED_VIA_REPLACEMENT" else
                     "REJECTED" if eg == "NONE" and decision_id else
                     "PENDING_REVIEW",
            "decision_id": decision_id,
            "replacement_authority_id": None,
        },
        "effective_grounding": eg,
        "display_badge": {
            "GROUNDED": "attorney-accepted (provisional)",
            "GROUNDED_VIA_REPLACEMENT": "replaced",
            "PROPOSED": "provisional-candidate",
            "NONE": "no-authority",
        }.get(eg, "pre-analysis"),
        "decision_id": decision_id,
        "pinned_record_id": pinned,
        "requires_attorney_review": eg in ("PROPOSED", "NONE"),
    }


def _serialize(coa: COA, include_authority: bool) -> dict:
    base = {
        "id": coa.id,
        "case_id": coa.case_id,
        "name": coa.name,
        "caci_ref": coa.caci_ref,
        "strength": coa.strength,
        "evidence_count": coa.evidence_count,
        "coverage_pct": coa.coverage_pct,
        "status": coa.status,
        "created_at": coa.created_at,
        "authority": _snapshot_authority(coa) if include_authority else None,
    }
    return base


async def _require_post_analysis(db: AsyncSession, case_id: int) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    if case.save_state not in sm.POST_ANALYSIS_STATES:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "detail": "case_not_analyzed",
                "save_state": case.save_state,
                "required_states": sorted(list(sm.POST_ANALYSIS_STATES)),
                "message": (
                    "COA authority is available only after Submit for Legal Analysis. "
                    "Use POST /cases/{id}/submit-for-analysis to begin."
                ),
            },
        )
    return case


@router.get("/", response_model=List[COAResponse])
async def list_coas(case_id: int = None, db: AsyncSession = Depends(get_db)):
    query = select(COA)
    if case_id is not None:
        await _require_post_analysis(db, case_id)
        query = query.where(COA.case_id == case_id)
        include_auth = True
    else:
        # cross-case list — never include authority (different cases may be in
        # different states); callers should use /coas/case/{id} instead.
        include_auth = False
    result = await db.execute(query)
    coas = result.scalars().all()
    return [_serialize(c, include_auth) for c in coas]


@router.get("/{coa_id}", response_model=COADetailResponse)
async def get_coa(coa_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(COA).where(COA.id == coa_id))
    coa = result.scalar_one_or_none()
    if not coa:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "COA not found")
    await _require_post_analysis(db, coa.case_id)
    data = _serialize(coa, include_authority=True)
    data["burden_elements"] = []  # resolver-gated; burden builder loads separately
    return data


@router.get("/case/{case_id}", response_model=List[COAResponse])
async def get_case_coas(case_id: int, db: AsyncSession = Depends(get_db)):
    await _require_post_analysis(db, case_id)
    result = await db.execute(select(COA).where(COA.case_id == case_id))
    coas = result.scalars().all()
    return [_serialize(c, include_authority=True) for c in coas]
