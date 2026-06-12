"""
Interview routes: two-mode intake (guided questions + freeform narrative),
explicit completion trigger, progress endpoint, background actor extraction.

Never invokes the authority resolver. Actor extraction is the only
side-effect of interview processing.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Case, Interview, InterviewQuestion
from schemas import (
    InterviewCompleteRequest,
    InterviewCreateRequest,
    InterviewModeSwitchRequest,
    InterviewNarrativeUpdate,
    InterviewProgressResponse,
    InterviewQuestionResponse,
    InterviewQuestionUpdate,
    InterviewResponse,
)
from brain.interview_processor import (
    DEFAULT_QUESTION_SET,
    is_question_answered,
    run_interview_processing,
    seed_questions_payload,
)

router = APIRouter(prefix="/interviews", tags=["interviews"])


VALID_MODES = {"GUIDED_QUESTIONS", "FREEFORM_NARRATIVE"}


async def _case_or_404(db: AsyncSession, case_id: int) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if case is None:
        raise HTTPException(404, "case not found")
    return case


async def _interview_or_404(db: AsyncSession, interview_id: int) -> Interview:
    res = await db.execute(
        select(Interview)
        .where(Interview.id == interview_id)
        .options(selectinload(Interview.questions))
    )
    iv = res.scalar_one_or_none()
    if iv is None:
        raise HTTPException(404, "interview not found")
    return iv


# ---------- CRUD ----------

@router.post("", response_model=InterviewResponse, status_code=201)
@router.post("/", response_model=InterviewResponse, status_code=201)
async def create_interview(body: InterviewCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    Create an interview for a case. One interview per case in v1: if one
    already exists, return that row so the UI can resume.
    """
    await _case_or_404(db, body.case_id)
    if body.mode not in VALID_MODES:
        raise HTTPException(400, f"invalid mode: {body.mode}")

    # Return existing if any
    existing = await db.execute(
        select(Interview)
        .where(Interview.case_id == body.case_id)
        .order_by(desc(Interview.id))
        .options(selectinload(Interview.questions))
        .limit(1)
    )
    iv = existing.scalar_one_or_none()
    if iv is not None:
        return iv

    iv = Interview(
        case_id=body.case_id,
        mode=body.mode,
        processing_state="draft",
        started_at=datetime.utcnow(),
    )
    db.add(iv)
    await db.flush()

    # Always seed the guided question set so the user can switch modes
    # without losing data. Questions are only used in GUIDED_QUESTIONS mode.
    for payload in seed_questions_payload():
        db.add(InterviewQuestion(interview_id=iv.id, **payload))

    await db.commit()
    # Re-fetch with questions eager-loaded for serialization.
    return await _interview_or_404(db, iv.id)


@router.get("/case/{case_id}", response_model=InterviewResponse)
async def get_case_interview(case_id: int, db: AsyncSession = Depends(get_db)):
    """Return the latest interview for a case, or 404."""
    await _case_or_404(db, case_id)
    res = await db.execute(
        select(Interview)
        .where(Interview.case_id == case_id)
        .order_by(desc(Interview.id))
        .options(selectinload(Interview.questions))
        .limit(1)
    )
    iv = res.scalar_one_or_none()
    if iv is None:
        raise HTTPException(404, "no interview for case")
    return iv


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(interview_id: int, db: AsyncSession = Depends(get_db)):
    return await _interview_or_404(db, interview_id)


@router.patch("/{interview_id}/mode", response_model=InterviewResponse)
async def switch_mode(interview_id: int, body: InterviewModeSwitchRequest, db: AsyncSession = Depends(get_db)):
    """
    Switch between GUIDED_QUESTIONS and FREEFORM_NARRATIVE. Data is preserved:
      - switching guided -> freeform does NOT delete question answers
      - switching freeform -> guided does NOT delete narrative_text
    """
    iv = await _interview_or_404(db, interview_id)
    if body.mode not in VALID_MODES:
        raise HTTPException(400, f"invalid mode: {body.mode}")
    if iv.processing_state in ("processing", "complete"):
        raise HTTPException(409, f"cannot switch mode in state {iv.processing_state}")
    iv.mode = body.mode
    await db.commit()
    return await _interview_or_404(db, iv.id)


@router.patch("/{interview_id}/narrative", response_model=InterviewResponse)
async def update_narrative(interview_id: int, body: InterviewNarrativeUpdate, db: AsyncSession = Depends(get_db)):
    """Update the freeform narrative. Allowed in any non-terminal state."""
    iv = await _interview_or_404(db, interview_id)
    if iv.processing_state in ("processing", "complete"):
        raise HTTPException(409, f"cannot edit narrative in state {iv.processing_state}")
    iv.narrative_text = body.narrative_text
    if iv.processing_state == "draft":
        iv.processing_state = "saved"
    await db.commit()
    return await _interview_or_404(db, iv.id)


@router.patch("/questions/{question_id}", response_model=InterviewQuestionResponse)
async def update_question(question_id: int, body: InterviewQuestionUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == question_id))
    q = res.scalar_one_or_none()
    if q is None:
        raise HTTPException(404, "question not found")
    iv = (await db.execute(select(Interview).where(Interview.id == q.interview_id))).scalar_one_or_none()
    if iv and iv.processing_state in ("processing", "complete"):
        raise HTTPException(409, f"cannot edit answers in state {iv.processing_state}")

    if body.answer_text is not None:
        q.answer_text = body.answer_text
    q.answered = is_question_answered(q)
    q.answered_at = datetime.utcnow() if q.answered else None
    if iv and iv.processing_state == "draft":
        iv.processing_state = "saved"
    await db.commit()
    await db.refresh(q)
    return q


@router.get("/{interview_id}/progress", response_model=InterviewProgressResponse)
async def get_progress(interview_id: int, db: AsyncSession = Depends(get_db)):
    iv = await _interview_or_404(db, interview_id)
    qs_res = await db.execute(
        select(InterviewQuestion).where(InterviewQuestion.interview_id == interview_id)
    )
    qs: List[InterviewQuestion] = list(qs_res.scalars().all())
    total = len(qs)
    answered = sum(1 for q in qs if is_question_answered(q))
    narrative_started = bool((iv.narrative_text or "").strip())
    narrative_complete = iv.processing_state in ("complete", "actors_identified")

    if iv.mode == "FREEFORM_NARRATIVE":
        if narrative_complete:
            display = "Narrative complete"
        elif narrative_started:
            chars = len((iv.narrative_text or "").strip())
            display = f"Freeform narrative started ({chars} chars)"
        else:
            display = "Freeform — not started"
    else:
        display = f"{answered}/{total} answered"
        if iv.processing_state == "complete":
            display += " · complete"
        elif iv.processing_state == "processing":
            display += " · processing"

    return InterviewProgressResponse(
        interview_id=iv.id,
        mode=iv.mode,
        processing_state=iv.processing_state,
        answered_count=answered,
        total_count=total,
        completion_pct=(answered / total) if total else 0.0,
        narrative_started=narrative_started,
        narrative_complete=narrative_complete,
        display=display,
    )


@router.post("/{interview_id}/complete", response_model=InterviewResponse, status_code=202)
async def complete_interview(
    interview_id: int,
    body: InterviewCompleteRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Explicit completion trigger. Transitions processing_state -> processing and
    enqueues the interview processor (actor extraction only; no analysis).

    Preconditions:
      - GUIDED_QUESTIONS: at least one question must be answered
      - FREEFORM_NARRATIVE: narrative_text must be non-empty (trimmed)
    """
    iv = await _interview_or_404(db, interview_id)
    if iv.processing_state in ("processing", "complete"):
        raise HTTPException(409, f"already {iv.processing_state}")

    if iv.mode == "FREEFORM_NARRATIVE":
        if not (iv.narrative_text or "").strip():
            raise HTTPException(409, "narrative_text is empty")
    else:
        qs_res = await db.execute(
            select(InterviewQuestion).where(InterviewQuestion.interview_id == interview_id)
        )
        qs = list(qs_res.scalars().all())
        if not any(is_question_answered(q) for q in qs):
            raise HTTPException(409, "no questions are answered yet")

    iv.completed_at = datetime.utcnow()
    iv.processing_state = "processing"
    await db.commit()

    background.add_task(run_interview_processing, iv.id)
    return await _interview_or_404(db, iv.id)
