"""
Analysis runner — the ONLY entry point that invokes the authority resolver
during a case's PROCESSING state.

See contract/v1/programs/program_ANALYSIS_TRIGGER.md and
contract/v1/programs/program_CASE_SAVE_LIFECYCLE.md.

Side effects on a case:
  - snapshot (authority_decision_id, authority_pinned_record_id,
    authority_effective_grounding) onto every COA row whose caci_ref
    resolves against the provisional store.
  - tally review_required_count = COAs with effective_grounding
    in {PROPOSED, NONE}.
  - transition case PROCESSING -> REVIEW_REQUIRED on success,
    or record the failure and transition REVIEW_REQUIRED with error flag.
"""
from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models import Case, COA, AnalysisRun
from .authority_resolver import (
    resolve_authority,
    GROUNDED,
    GROUNDED_VIA_REPLACEMENT,
    PROPOSED,
    NONE as GROUNDING_NONE,
)
from . import state_machine as sm


async def run_analysis(case_id: int, run_id: str) -> None:
    """
    Background task entry. Opens its own DB session because the HTTP handler
    that scheduled it has already returned.
    """
    async with AsyncSessionLocal() as db:
        run = await _load_run(db, run_id)
        case = await _load_case(db, case_id)
        if run is None or case is None:
            return

        run.state = "RUNNING"
        await db.commit()

        try:
            await _execute(db, case, run)
            await _finish_success(db, case, run)
        except Exception as exc:
            await _finish_failure(db, case, run, exc)


async def _load_run(db: AsyncSession, run_id: str) -> AnalysisRun:
    res = await db.execute(select(AnalysisRun).where(AnalysisRun.run_id == run_id))
    return res.scalar_one_or_none()


async def _load_case(db: AsyncSession, case_id: int) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    return res.scalar_one_or_none()


async def _execute(db: AsyncSession, case: Case, run: AnalysisRun) -> None:
    res = await db.execute(select(COA).where(COA.case_id == case.id))
    coas: List[COA] = list(res.scalars().all())
    run.coa_count = len(coas)

    review_count = 0
    for coa in coas:
        if not coa.caci_ref:
            continue
        resolved = await resolve_authority(db, case.id, coa.caci_ref)
        coa.authority_decision_id = resolved.decision_id
        coa.authority_pinned_record_id = resolved.pinned_record_id
        coa.authority_effective_grounding = resolved.effective_grounding

        eg = resolved.effective_grounding
        if eg == GROUNDED:
            coa.status = "grounded"
        elif eg == GROUNDED_VIA_REPLACEMENT:
            coa.status = "grounded_via_replacement"
        elif eg == PROPOSED:
            coa.status = "proposed"
            review_count += 1
        elif eg == GROUNDING_NONE:
            coa.status = "none"
            review_count += 1

    run.review_required_count = review_count
    case.review_required_count = review_count
    case.last_error_detail = None


async def _finish_success(db: AsyncSession, case: Case, run: AnalysisRun) -> None:
    run.state = "COMPLETED"
    run.completed_at = datetime.utcnow()
    case.processing_finished_at = datetime.utcnow()
    try:
        await sm.transition(
            db, case,
            to_state=sm.REVIEW_REQUIRED,
            actor_id="system:analysis_runner",
            actor_type="SYSTEM",
            reason=f"AnalysisRun {run.run_id} completed: review_required={run.review_required_count}",
        )
    except sm.InvalidTransition:
        # already transitioned by another process — tolerate
        pass
    await db.commit()


async def _finish_failure(
    db: AsyncSession, case: Case, run: AnalysisRun, exc: Exception
) -> None:
    # Don't let a failure leave the case stuck in PROCESSING.
    await db.rollback()
    async with AsyncSessionLocal() as db2:
        run = await _load_run(db2, run.run_id)
        case = await _load_case(db2, case.id)
        if run is None or case is None:
            return
        run.state = "FAILED"
        run.completed_at = datetime.utcnow()
        run.error_detail = f"{type(exc).__name__}: {exc}"
        case.processing_finished_at = datetime.utcnow()
        case.last_error_detail = run.error_detail
        try:
            await sm.transition(
                db2, case,
                to_state=sm.REVIEW_REQUIRED,
                actor_id="system:analysis_runner",
                actor_type="SYSTEM",
                reason=f"AnalysisRun {run.run_id} FAILED: {run.error_detail}",
            )
        except sm.InvalidTransition:
            pass
        await db2.commit()
