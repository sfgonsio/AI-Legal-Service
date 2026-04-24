"""
Interview processor — runs on explicit interview completion only.

Bounded operations:
  1. persist interview state
  2. assemble a single text body from mode-appropriate source
  3. run actor extraction (shared with ingest pipeline)
  4. record ActorMention rows with source_kind=INTERVIEW
  5. mark interview processing_state -> complete

Does NOT invoke the authority resolver or any analytical path.
Enforced by SR-12 (audit script greps this file).
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models import Actor, ActorMention, Interview, InterviewQuestion
from .actor_extractor import (
    ExtractedActor,
    canonicalize,
    extract_actors,
    resolve_against_existing,
)


def _build_text(interview: Interview) -> str:
    if interview.mode == "FREEFORM_NARRATIVE":
        return interview.narrative_text or ""
    parts: List[str] = []
    for q in sorted(interview.questions or [], key=lambda x: x.order_index):
        if q.answer_text:
            parts.append(f"Q: {q.prompt}\nA: {q.answer_text}")
    return "\n\n".join(parts)


async def _load_existing_actor_map(db: AsyncSession, case_id: int) -> dict:
    res = await db.execute(select(Actor).where(Actor.case_id == case_id))
    return {a.canonical_name: a.id for a in res.scalars().all()}


async def _persist_actor(
    db: AsyncSession,
    interview: Interview,
    ex: ExtractedActor,
    existing_actor_id,
    state: str,
) -> None:
    actor_id = existing_actor_id
    if actor_id is None:
        new_actor = Actor(
            case_id=interview.case_id,
            display_name=ex.display_name,
            canonical_name=ex.canonical,
            entity_type=ex.entity_type,
            resolution_state=state,
            role_hint=None,
            mention_count=1,
            source="INTERVIEW",
            source_interview_id=interview.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_actor)
        await db.flush()
        actor_id = new_actor.id
    else:
        res = await db.execute(select(Actor).where(Actor.id == actor_id))
        actor = res.scalar_one_or_none()
        if actor is not None:
            actor.mention_count = (actor.mention_count or 0) + 1
            actor.updated_at = datetime.utcnow()
            # Do not downgrade RESOLVED actors.

    db.add(ActorMention(
        actor_id=actor_id,
        document_id=None,
        interview_id=interview.id,
        source_kind="INTERVIEW",
        snippet=ex.snippet,
        offset_start=ex.offset_start,
        offset_end=ex.offset_end,
        confidence=ex.confidence,
        created_at=datetime.utcnow(),
    ))


async def run_interview_processing(interview_id: int) -> None:
    """
    Background task entry. Opens its own session.

    Lifecycle transitions on the Interview row:
      draft | saved -> processing -> actors_identified -> complete
                    -> failed (with last_error_detail) on exception
    """
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Interview).where(Interview.id == interview_id))
        interview: Interview = res.scalar_one_or_none()
        if interview is None:
            return
        interview.processing_state = "processing"
        await db.commit()

        try:
            # reload with questions for guided mode
            res2 = await db.execute(select(Interview).where(Interview.id == interview_id))
            interview = res2.scalar_one_or_none()
            text = _build_text(interview)
            extracted = extract_actors(text) if text else []

            if extracted:
                existing = await _load_existing_actor_map(db, interview.case_id)
                resolved = resolve_against_existing(extracted, existing)
                for ex, existing_id, state in resolved:
                    await _persist_actor(db, interview, ex, existing_id, state)
                interview.processing_state = "actors_identified"
                await db.flush()

            interview.processing_state = "complete"
            interview.processed_at = datetime.utcnow()
            await db.commit()
        except Exception as exc:
            await db.rollback()
            async with AsyncSessionLocal() as fdb:
                res3 = await fdb.execute(select(Interview).where(Interview.id == interview_id))
                i2 = res3.scalar_one_or_none()
                if i2 is not None:
                    i2.processing_state = "failed"
                    i2.last_error_detail = f"{type(exc).__name__}: {exc}"
                    i2.processed_at = datetime.utcnow()
                    await fdb.commit()


# Default guided-question set. Deterministic, editable in one place.
DEFAULT_QUESTION_SET = [
    ("intake_case_summary", "In one or two sentences, what is this case about?", "LONG_TEXT"),
    ("intake_parties", "Who are the main parties involved (plaintiffs, defendants, organizations)?", "LONG_TEXT"),
    ("intake_key_dates", "What are the key dates (incident, notice, filings)?", "TEXT"),
    ("intake_venue", "In what court or jurisdiction is the matter filed or expected?", "TEXT"),
    ("intake_relationship", "What is the relationship between the parties (contract, partnership, employer, other)?", "TEXT"),
    ("intake_what_happened", "What happened? Describe the sequence of events chronologically.", "LONG_TEXT"),
    ("intake_harm", "What harm or damages has the client suffered?", "LONG_TEXT"),
    ("intake_evidence", "What documents, emails, or records exist to support the claim?", "LONG_TEXT"),
    ("intake_witnesses", "Who are the witnesses or other people who know about this?", "LONG_TEXT"),
    ("intake_opposing_counsel", "Is opposing counsel known? If so, who?", "TEXT"),
    ("intake_prior_actions", "Have any prior legal actions, demand letters, or settlements occurred?", "TEXT"),
    ("intake_client_goals", "What outcome is the client seeking?", "LONG_TEXT"),
    ("intake_other", "Is there anything else important the attorney should know?", "LONG_TEXT"),
]


def seed_questions_payload():
    """Return the default question-set payload as dict rows."""
    return [
        {"question_key": k, "prompt": p, "order_index": i, "completion_kind": ck}
        for i, (k, p, ck) in enumerate(DEFAULT_QUESTION_SET)
    ]


# --- Completion logic (mirrored by the route's progress endpoint) ---

MIN_TEXT_LEN = 2
MIN_LONG_TEXT_LEN = 20


def is_question_answered(q: InterviewQuestion) -> bool:
    t = (q.answer_text or "").strip()
    if not t:
        return False
    if q.completion_kind == "LONG_TEXT":
        return len(t) >= MIN_LONG_TEXT_LEN
    if q.completion_kind == "TEXT":
        return len(t) >= MIN_TEXT_LEN
    if q.completion_kind == "DATE":
        return len(t) >= 4  # at least a year token
    if q.completion_kind == "YESNO":
        return t.lower() in ("yes", "no", "y", "n", "true", "false")
    return bool(t)
