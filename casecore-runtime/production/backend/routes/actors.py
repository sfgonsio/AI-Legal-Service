"""
Actor routes. Reads + attorney disambiguation PATCH.

Read endpoint groups actors by resolution_state for the Dashboard. PATCH lets
attorneys promote CANDIDATE -> RESOLVED and disambiguate AMBIGUOUS. No imports
from authority-resolution modules. Enforced by SR-12.
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Actor, ActorMention, Case
from schemas import (
    ActorResponse,
    ActorsGroupedResponse,
    ActorUpdateRequest,
    ActorMentionResponse,
    ActorCreateRequest,
    ActorMergeRequest,
    ActorMergeResponse,
)
from brain.actor_extractor import canonicalize

router = APIRouter(prefix="/actors", tags=["actors"])


VALID_STATES = {"RESOLVED", "CANDIDATE", "AMBIGUOUS"}
VALID_TYPES = {"PERSON", "ORGANIZATION", "UNKNOWN"}


async def _case_or_404(db: AsyncSession, case_id: int) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "case not found")
    return case


@router.get("/case/{case_id}", response_model=ActorsGroupedResponse)
async def list_case_actors(case_id: int, db: AsyncSession = Depends(get_db)):
    await _case_or_404(db, case_id)
    res = await db.execute(select(Actor).where(Actor.case_id == case_id))
    rows = list(res.scalars().all())

    resolved, candidate, ambiguous, orgs = [], [], [], []
    for a in rows:
        item = ActorResponse.model_validate(a)
        if a.entity_type == "ORGANIZATION":
            orgs.append(item)
            continue
        if a.resolution_state == "RESOLVED":
            resolved.append(item)
        elif a.resolution_state == "AMBIGUOUS":
            ambiguous.append(item)
        else:
            candidate.append(item)

    counts = {
        "total": len(rows),
        "resolved": len(resolved),
        "candidate": len(candidate),
        "ambiguous": len(ambiguous),
        "organizations": len(orgs),
    }
    return ActorsGroupedResponse(
        case_id=case_id,
        counts=counts,
        resolved=resolved,
        candidate=candidate,
        ambiguous=ambiguous,
        organizations=orgs,
    )


@router.get("/{actor_id}", response_model=ActorResponse)
async def get_actor(actor_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Actor).where(Actor.id == actor_id))
    actor = res.scalar_one_or_none()
    if actor is None:
        raise HTTPException(404, "actor not found")
    return actor


@router.patch("/{actor_id}", response_model=ActorResponse)
async def update_actor(
    actor_id: int, body: ActorUpdateRequest, db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Actor).where(Actor.id == actor_id))
    actor = res.scalar_one_or_none()
    if actor is None:
        raise HTTPException(404, "actor not found")

    data = body.model_dump(exclude_unset=True)
    if "resolution_state" in data and data["resolution_state"] not in VALID_STATES:
        raise HTTPException(400, f"invalid resolution_state: {data['resolution_state']}")
    if "entity_type" in data and data["entity_type"] not in VALID_TYPES:
        raise HTTPException(400, f"invalid entity_type: {data['entity_type']}")

    for field, value in data.items():
        if field in ("actor_id",):
            continue
        if value is None:
            continue
        setattr(actor, field, value)

    actor.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(actor)
    return actor


@router.get("/{actor_id}/mentions", response_model=List[ActorMentionResponse])
async def get_mentions(actor_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Actor).where(Actor.id == actor_id))
    if res.scalar_one_or_none() is None:
        raise HTTPException(404, "actor not found")
    m_res = await db.execute(
        select(ActorMention).where(ActorMention.actor_id == actor_id)
    )
    return list(m_res.scalars().all())


# ---------------- create / delete / merge ----------------

@router.post("/", response_model=ActorResponse, status_code=201)
async def create_actor(body: ActorCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    Manual actor creation. Defaults to RESOLVED (attorney-entered).
    Uses the same canonicalization as the ingest/interview extractor so
    subsequent mentions resolve to this row automatically.
    """
    await _case_or_404(db, body.case_id)
    if body.entity_type not in VALID_TYPES:
        raise HTTPException(400, f"invalid entity_type: {body.entity_type}")
    if body.resolution_state not in VALID_STATES:
        raise HTTPException(400, f"invalid resolution_state: {body.resolution_state}")

    canonical = body.canonical_name or canonicalize(body.display_name)
    if not canonical:
        raise HTTPException(400, "display_name is empty after canonicalization")

    # Enforce the (case_id, canonical_name) unique constraint.
    existing = await db.execute(
        select(Actor).where(Actor.case_id == body.case_id).where(Actor.canonical_name == canonical)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(409, f"actor with canonical_name '{canonical}' already exists in case")

    actor = Actor(
        case_id=body.case_id,
        display_name=body.display_name,
        canonical_name=canonical,
        entity_type=body.entity_type,
        resolution_state=body.resolution_state,
        role_hint=body.role_hint,
        mention_count=0,
        source="MANUAL",
        notes=body.notes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(actor)
    await db.commit()
    await db.refresh(actor)
    return actor


@router.delete("/{actor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_actor(actor_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete an actor and its mention rows (cascaded). Use /actors/merge to
    consolidate mentions before deleting duplicates.
    """
    res = await db.execute(select(Actor).where(Actor.id == actor_id))
    actor = res.scalar_one_or_none()
    if actor is None:
        raise HTTPException(404, "actor not found")
    await db.delete(actor)
    await db.commit()
    return None


@router.post("/merge", response_model=ActorMergeResponse)
async def merge_actors(body: ActorMergeRequest, db: AsyncSession = Depends(get_db)):
    """
    Merge one or more source actors into a target actor. Moves all
    ActorMention rows from sources to target, stamps the sources with
    merged_into_actor_id, then deletes the source rows. All actors must
    belong to the same case.
    """
    if body.target_actor_id in body.source_actor_ids:
        raise HTTPException(400, "target_actor_id cannot be in source_actor_ids")
    if not body.source_actor_ids:
        raise HTTPException(400, "source_actor_ids must be non-empty")

    res_t = await db.execute(select(Actor).where(Actor.id == body.target_actor_id))
    target = res_t.scalar_one_or_none()
    if target is None:
        raise HTTPException(404, "target actor not found")

    res_s = await db.execute(select(Actor).where(Actor.id.in_(body.source_actor_ids)))
    sources = list(res_s.scalars().all())
    if len(sources) != len(body.source_actor_ids):
        raise HTTPException(404, "one or more source actors not found")
    for s in sources:
        if s.case_id != target.case_id:
            raise HTTPException(400, "all actors must belong to the same case")

    # Move mentions
    moved = 0
    m_res = await db.execute(
        select(ActorMention).where(ActorMention.actor_id.in_(body.source_actor_ids))
    )
    for m in m_res.scalars().all():
        m.actor_id = target.id
        moved += 1

    # Sum mention counts onto target
    extra_count = sum((s.mention_count or 0) for s in sources)
    target.mention_count = (target.mention_count or 0) + extra_count
    target.updated_at = datetime.utcnow()
    # Merged actor never downgraded: if any source was RESOLVED, keep target RESOLVED.
    if target.resolution_state != "RESOLVED" and any(s.resolution_state == "RESOLVED" for s in sources):
        target.resolution_state = "RESOLVED"

    # Mark sources merged then delete
    for s in sources:
        s.merged_into_actor_id = target.id
    await db.flush()
    for s in sources:
        await db.delete(s)

    await db.commit()
    await db.refresh(target)
    return ActorMergeResponse(
        target_actor_id=target.id,
        merged_actor_ids=body.source_actor_ids,
        moved_mentions=moved,
    )
