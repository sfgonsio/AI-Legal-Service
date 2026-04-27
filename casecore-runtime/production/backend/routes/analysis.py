"""
Analysis result endpoint.

GET /cases/{case_id}/analysis   — full analysis blob from the latest COMPLETED
                                   AnalysisRun. Gated: only available when the
                                   case is in a post-analysis state.

The analysis blob is produced by brain.analysis_runner._execute during
Submit for Legal Analysis. It contains:
  stats, coas, burdens, remedies, complaint, evidence_map, provenance.

Phase 1 Evidence Reference Endpoints:
GET /cases/{case_id}/evidence-references — Retrieve evidence references (with filtering)
POST /cases/{case_id}/evidence-references/backfill-actor-mentions — Backfill from ActorMention
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import AnalysisRun, Case, EvidenceReference
from schemas import (
    EvidenceReferenceResponse,
    BackfillActorMentionsRequest,
    BackfillActorMentionsResponse,
)
from brain import state_machine as sm
from brain.evidence_service import (
    backfill_evidence_references_from_actor_mentions,
    get_evidence_references as get_evidence_references_service,
)


router = APIRouter(prefix="/cases", tags=["analysis"])


async def _require_case_state(db: AsyncSession, case_id: int, allowed: set) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if case is None:
        raise HTTPException(404, "case not found")
    if case.save_state not in allowed:
        raise HTTPException(
            409,
            detail={
                "detail": "case_state_not_allowed",
                "save_state": case.save_state,
                "required_states": sorted(list(allowed)),
                "message": (
                    f"Analysis is only available after Submit for Legal Analysis. "
                    f"Current state: {case.save_state}. Required: {sorted(list(allowed))}."
                ),
            },
        )
    return case


@router.get("/{case_id}/analysis")
async def get_analysis(case_id: int, db: AsyncSession = Depends(get_db)):
    """Return the latest COMPLETED analysis run's result blob."""
    await _require_case_state(db, case_id, sm.POST_ANALYSIS_STATES)
    stmt = (
        select(AnalysisRun)
        .where(AnalysisRun.case_id == case_id)
        .where(AnalysisRun.state == "COMPLETED")
        .order_by(desc(AnalysisRun.triggered_at))
        .limit(1)
    )
    res = await db.execute(stmt)
    run: Optional[AnalysisRun] = res.scalar_one_or_none()
    if run is None:
        raise HTTPException(
            409,
            detail={
                "detail": "no_completed_analysis",
                "message": "No completed AnalysisRun exists for this case yet. "
                           "Submit for Legal Analysis, then retry.",
            },
        )
    return {
        "case_id": case_id,
        "run": {
            "run_id": run.run_id,
            "state": run.state,
            "triggered_at": run.triggered_at.isoformat() if run.triggered_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "coa_count": run.coa_count,
            "review_required_count": run.review_required_count,
            "triggered_by_actor_id": run.triggered_by_actor_id,
        },
        "result": run.result_json or {},
    }


# ============ Phase 1 Evidence Reference Endpoints ============


@router.get("/{case_id}/evidence-references", response_model=dict)
async def get_evidence_references(
    case_id: int,
    fact_type: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    binding_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve EvidenceReference records for a case with optional filtering.

    Query params:
    - fact_type: actor_mention | event | claim | finding
    - source_type: document | interview_session | deposition | email
    - binding_type: direct_evidence | supporting | circumstantial | contradiction
    - limit: default 100, max 1000
    - offset: default 0

    Returns: {case_id, total, limit, offset, evidence_references: [...]}
    """
    # Verify case exists
    stmt = select(Case).where(Case.id == case_id)
    res = await db.execute(stmt)
    if res.scalar_one_or_none() is None:
        raise HTTPException(404, "case not found")

    result = await get_evidence_references_service(
        db,
        case_id=case_id,
        fact_type=fact_type,
        source_type=source_type,
        binding_type=binding_type,
        limit=limit,
        offset=offset,
    )
    return result


@router.post("/{case_id}/evidence-references/backfill-actor-mentions", response_model=BackfillActorMentionsResponse)
async def backfill_actor_mentions(
    case_id: int,
    request: BackfillActorMentionsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Backfill EvidenceReference table from existing ActorMention records.

    Idempotent: For each actor_mention, checks if evidence_reference already exists
    (same actor_mention + document + offset). If yes, skips. If no, creates.

    Request body: {"dry_run": bool}
    - dry_run=false: commits changes to database
    - dry_run=true: returns counts without committing

    Returns: BackfillActorMentionsResponse
    """
    # Verify case exists
    stmt = select(Case).where(Case.id == case_id)
    res = await db.execute(stmt)
    if res.scalar_one_or_none() is None:
        raise HTTPException(404, "case not found")

    result = await backfill_evidence_references_from_actor_mentions(
        db,
        case_id=case_id,
        dry_run=request.dry_run,
    )
    return result
