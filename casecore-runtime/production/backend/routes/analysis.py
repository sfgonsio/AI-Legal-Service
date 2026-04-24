"""
Analysis result endpoint.

GET /cases/{case_id}/analysis   — full analysis blob from the latest COMPLETED
                                   AnalysisRun. Gated: only available when the
                                   case is in a post-analysis state.

The analysis blob is produced by brain.analysis_runner._execute during
Submit for Legal Analysis. It contains:
  stats, coas, burdens, remedies, complaint, evidence_map, provenance.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import AnalysisRun, Case
from brain import state_machine as sm


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
