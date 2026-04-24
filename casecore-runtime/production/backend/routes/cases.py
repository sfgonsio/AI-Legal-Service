"""
Case CRUD + lifecycle routes.

Lifecycle endpoints:
  POST /cases/{id}/save-draft          - ingest-only; state -> DRAFT|SAVED
  POST /cases/{id}/mark-ready          - SAVED -> READY_FOR_ANALYSIS
  POST /cases/{id}/submit-for-analysis - SAVED|READY_FOR_ANALYSIS -> PROCESSING
  POST /cases/{id}/return-to-intake    - any -> RETURNED_TO_INTAKE -> DRAFT
  GET  /cases/{id}/progress            - save state + analysis run summary
  GET  /cases/{id}/state-events        - audit trail of transitions
"""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import (
    Case,
    Document,
    COA,
    AnalysisRun,
    CaseStateEvent,
)
from schemas import (
    CaseCreate,
    CaseUpdate,
    CaseResponse,
    CaseDetailResponse,
    SaveDraftRequest,
    MarkReadyRequest,
    SubmitForAnalysisRequest,
    ReturnToIntakeRequest,
    AnalysisRunResponse,
    CaseProgressResponse,
    CaseStateEventResponse,
)
from brain import state_machine as sm
from brain.analysis_runner import run_analysis

router = APIRouter(prefix="/cases", tags=["cases"])


# ---------------- Basic CRUD ----------------

@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(case: CaseCreate, db: AsyncSession = Depends(get_db)):
    """Create a new case in DRAFT state."""
    db_case = Case(**case.model_dump(), save_state=sm.DRAFT)
    db.add(db_case)
    await db.flush()
    # initial state event
    db.add(CaseStateEvent(
        case_id=db_case.id,
        from_state=None,
        to_state=sm.DRAFT,
        actor_id="system:create_case",
        actor_type="SYSTEM",
        reason="case created",
    ))
    await db.commit()
    await db.refresh(db_case)
    return db_case


@router.get("/", response_model=List[CaseResponse])
async def list_cases(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case))
    return list(result.scalars().all())


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(case_id: int, case_update: CaseUpdate, db: AsyncSession = Depends(get_db)):
    """
    Low-level metadata update. Does NOT transition state.
    Use POST /cases/{id}/save-draft for state-aware saves.
    """
    result = await db.execute(select(Case).where(Case.id == case_id))
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    update_data = case_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_case, field, value)
    await db.commit()
    await db.refresh(db_case)
    return db_case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    await db.delete(db_case)
    await db.commit()
    return None


# ---------------- Lifecycle ----------------

async def _load_case_or_404(db: AsyncSession, case_id: int) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    return case


def _transition_or_409(case: Case, target: str) -> None:
    """Check transition allowed; raise 409 with detail if not."""
    if target not in sm.ALLOWED.get(case.save_state, set()):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={
                "detail": "invalid_state_transition",
                "save_state": case.save_state,
                "required_states": sorted(
                    [s for s, targets in sm.ALLOWED.items() if target in targets]
                ),
                "attempted_target": target,
                "message": f"Cannot transition {case.save_state} -> {target}",
            },
        )


@router.post("/{case_id}/save-draft", response_model=CaseResponse)
async def save_draft(case_id: int, body: SaveDraftRequest, db: AsyncSession = Depends(get_db)):
    """
    Ingest-only save. Persists metadata + documents (already persisted via
    prior routes); transitions state to DRAFT or SAVED depending on
    `return_to_dashboard`. Never invokes the authority resolver.
    """
    case = await _load_case_or_404(db, case_id)

    # Target state
    target = sm.SAVED if body.return_to_dashboard else sm.DRAFT
    _transition_or_409(case, target)

    # Apply metadata updates (ingest-pipeline-only fields)
    for field in ("name", "court", "plaintiff", "defendant"):
        val = getattr(body, field)
        if val is not None:
            setattr(case, field, val)

    case.last_saved_at = datetime.utcnow()

    await sm.transition(
        db, case,
        to_state=target,
        actor_id=body.actor_id,
        actor_type=body.actor_type,
        reason=body.reason or ("save-and-return" if body.return_to_dashboard else "save-draft"),
    )
    await db.commit()
    await db.refresh(case)
    return case


@router.post("/{case_id}/mark-ready", response_model=CaseResponse)
async def mark_ready(case_id: int, body: MarkReadyRequest, db: AsyncSession = Depends(get_db)):
    """SAVED -> READY_FOR_ANALYSIS."""
    case = await _load_case_or_404(db, case_id)
    _transition_or_409(case, sm.READY_FOR_ANALYSIS)
    await sm.transition(
        db, case,
        to_state=sm.READY_FOR_ANALYSIS,
        actor_id=body.actor_id,
        actor_type=body.actor_type,
        reason=body.reason or "marked-ready",
    )
    await db.commit()
    await db.refresh(case)
    return case


@router.post("/{case_id}/submit-for-analysis", status_code=202)
async def submit_for_analysis(
    case_id: int,
    body: SubmitForAnalysisRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Transition SAVED|READY_FOR_ANALYSIS -> PROCESSING and enqueue the
    analysis runner. Returns 202 with run_id.

    Preconditions:
      - save_state in {SAVED, READY_FOR_ANALYSIS}
      - >= 1 document
      - >= 1 COA
      - no in-flight RUNNING AnalysisRun for this case
    """
    case = await _load_case_or_404(db, case_id)
    _transition_or_409(case, sm.PROCESSING)

    doc_count = (await db.execute(
        select(func.count(Document.id)).where(Document.case_id == case_id)
    )).scalar() or 0
    coa_count = (await db.execute(
        select(func.count(COA.id)).where(COA.case_id == case_id)
    )).scalar() or 0
    if doc_count == 0:
        raise HTTPException(409, {"detail": "no_documents", "message": "Case has no documents"})
    if coa_count == 0:
        raise HTTPException(409, {"detail": "no_coas", "message": "Case has no COAs"})

    in_flight = (await db.execute(
        select(func.count(AnalysisRun.id))
        .where(AnalysisRun.case_id == case_id)
        .where(AnalysisRun.state == "RUNNING")
    )).scalar() or 0
    if in_flight > 0:
        raise HTTPException(409, {"detail": "analysis_in_flight", "message": "An AnalysisRun is already RUNNING"})

    run_id = str(uuid.uuid4())
    now = datetime.utcnow()

    run = AnalysisRun(
        run_id=run_id,
        case_id=case_id,
        state="PENDING",
        triggered_by_actor_id=body.actor_id,
        triggered_by_actor_type=body.actor_type,
        triggered_at=now,
        coa_count=coa_count,
        review_required_count=0,
    )
    db.add(run)

    case.processing_started_at = now
    case.last_submitted_at = now
    case.current_analysis_run_id = run_id

    await sm.transition(
        db, case,
        to_state=sm.PROCESSING,
        actor_id=body.actor_id,
        actor_type=body.actor_type,
        reason=f"submit-for-analysis run_id={run_id}",
    )
    await db.commit()

    background.add_task(run_analysis, case_id, run_id)
    return {"run_id": run_id, "state": "PENDING", "case_id": case_id}


@router.post("/{case_id}/return-to-intake", response_model=CaseResponse)
async def return_to_intake(case_id: int, body: ReturnToIntakeRequest, db: AsyncSession = Depends(get_db)):
    """
    From any state -> RETURNED_TO_INTAKE -> DRAFT (auto-chained).
    Prior analysis artifacts are retained for audit.
    """
    case = await _load_case_or_404(db, case_id)
    _transition_or_409(case, sm.RETURNED_TO_INTAKE)

    await sm.transition(
        db, case,
        to_state=sm.RETURNED_TO_INTAKE,
        actor_id=body.actor_id,
        actor_type=body.actor_type,
        reason=body.reason,
    )
    # Auto-chain to DRAFT per program contract.
    await sm.transition(
        db, case,
        to_state=sm.DRAFT,
        actor_id=body.actor_id,
        actor_type=body.actor_type,
        reason="auto-chain after return-to-intake",
    )
    case.current_analysis_run_id = None
    case.processing_started_at = None
    case.processing_finished_at = None
    await db.commit()
    await db.refresh(case)
    return case


# ---------------- Observability ----------------

@router.get("/{case_id}/progress", response_model=CaseProgressResponse)
async def get_progress(case_id: int, db: AsyncSession = Depends(get_db)):
    case = await _load_case_or_404(db, case_id)

    current_run: Optional[AnalysisRun] = None
    if case.current_analysis_run_id:
        res = await db.execute(
            select(AnalysisRun).where(AnalysisRun.run_id == case.current_analysis_run_id)
        )
        current_run = res.scalar_one_or_none()

    gated = []
    if case.save_state not in sm.POST_ANALYSIS_STATES:
        gated = [
            "/coas/case/{id}",
            "/case-authority/case/{id}/map",
            "/case-authority/resolve",
        ]
    if case.save_state != sm.REVIEW_REQUIRED:
        gated.append("/case-authority/decisions (POST)")

    return CaseProgressResponse(
        case_id=case.id,
        save_state=case.save_state,
        last_saved_at=case.last_saved_at,
        last_submitted_at=case.last_submitted_at,
        processing_started_at=case.processing_started_at,
        processing_finished_at=case.processing_finished_at,
        review_required_count=case.review_required_count,
        current_analysis_run=current_run,
        gated_surfaces=gated,
        last_error_detail=case.last_error_detail,
    )


@router.get("/{case_id}/state-events", response_model=List[CaseStateEventResponse])
async def get_state_events(case_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(CaseStateEvent)
        .where(CaseStateEvent.case_id == case_id)
        .order_by(desc(CaseStateEvent.at))
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{case_id}/analysis-runs", response_model=List[AnalysisRunResponse])
async def list_analysis_runs(case_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(AnalysisRun)
        .where(AnalysisRun.case_id == case_id)
        .order_by(desc(AnalysisRun.triggered_at))
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())
