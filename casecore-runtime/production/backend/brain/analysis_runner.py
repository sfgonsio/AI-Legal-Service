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
from sqlalchemy.orm import selectinload

from database import AsyncSessionLocal
from models import (
    Actor, AnalysisRun, Case, COA, Document, Interview,
    TimelineEvent,
)
from .authority_resolver import (
    resolve_authority,
    GROUNDED,
    GROUNDED_VIA_REPLACEMENT,
    PROPOSED,
    NONE as GROUNDING_NONE,
)
from . import state_machine as sm
from . import timeline_builder, coa_engine
from . import burden_mapper_v2 as burden_mapper
from . import remedy_deriver, complaint_builder, evidence_mapper


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
    # ---- Step 1: Ensure the timeline is current. Timeline is built BEFORE
    # COA / burden / remedy per contract. This is an internal call — it does
    # not modify the ingest pipeline.
    # Commit the PROCESSING state before we open a nested session, so the
    # builder sees fresh data.
    await db.commit()
    await timeline_builder.build_for_case(case.id, replace=True)

    # ---- Step 2: Snapshot authority onto pre-existing COA rows (legacy path;
    # attorney-decision-scoped). This keeps the prior decision + gated
    # surfaces coherent with the new analysis artifact.
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

    # ---- Step 3: Build the analytical artifact. Everything below reads the
    # case's current state and produces a structured blob persisted as
    # AnalysisRun.result_json. Authority is grounded in the Legal Library
    # (IMPORTED records only).
    ev_res = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.case_id == case.id)
        .options(selectinload(TimelineEvent.legal_mappings))
    )
    tl_events: List[TimelineEvent] = list(ev_res.scalars().all())

    actor_res = await db.execute(select(Actor).where(Actor.case_id == case.id))
    actors = list(actor_res.scalars().all())

    doc_res = await db.execute(select(Document).where(Document.case_id == case.id))
    docs = list(doc_res.scalars().all())

    iv_res = await db.execute(select(Interview).where(Interview.case_id == case.id))
    interviews = list(iv_res.scalars().all())

    coa_candidates = coa_engine.generate_coa_candidates(tl_events)
    burdens = burden_mapper.map_burdens(coa_candidates)
    remedy_bundles = remedy_deriver.derive_remedies(coa_candidates, tl_events)
    complaint = complaint_builder.build_complaint(
        case=case, actors=actors, timeline_events=tl_events,
        coa_candidates=coa_candidates, remedy_bundles=remedy_bundles,
    )
    ev_map = evidence_mapper.build_evidence_map(
        tl_events, coa_candidates, docs, interviews,
    )

    # Count unresolved-authority signals so the attorney sees a review count.
    pre_analysis_review = sum(
        1 for c in coa_candidates
        if any(s.status in ("PARTIAL", "UNSUPPORTED") for s in c.elements)
    )
    review_count = max(review_count, pre_analysis_review)

    result = {
        "stats": {
            "timeline_events": len(tl_events),
            "actors": len(actors),
            "documents": len(docs),
            "interviews": len(interviews),
            "coa_candidates": len(coa_candidates),
        },
        "coas": coa_engine.serialize(coa_candidates),
        "burdens": burden_mapper.serialize(burdens),
        "remedies": remedy_deriver.serialize(remedy_bundles),
        "complaint": complaint_builder.serialize(complaint),
        "evidence_map": evidence_mapper.serialize(ev_map),
        "provenance": {
            "authority_grounding": "Every COA reference verified against the "
                                    "Legal Library corpus (body_status=IMPORTED); "
                                    "COAs with missing body text are dropped.",
            "run_id": run.run_id,
            "case_id": case.id,
        },
    }
    run.result_json = result

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
