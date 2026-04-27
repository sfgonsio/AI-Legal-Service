"""
Phase 1 Evidence Service

Helper for creating EvidenceReference records from ActorMention backfill.
Idempotent: deterministic duplicate check (same actor_mention + document + offset = skip).
"""
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import EvidenceReference, ActorMention, Document

logger = logging.getLogger(__name__)


async def backfill_evidence_references_from_actor_mentions(
    db: AsyncSession,
    case_id: int,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Backfill EvidenceReference table from existing ActorMention records.

    Idempotent: For each actor_mention, check if evidence_reference already exists
    (same actor_mention + document + offset span). If yes, skip. If no, create.

    Args:
        db: AsyncSession
        case_id: int
        dry_run: bool — if True, return counts but do NOT commit

    Returns:
        {
            "case_id": int,
            "dry_run": bool,
            "evidence_references_created": int,
            "evidence_references_skipped": int,
            "total_actor_mentions_processed": int,
            "errors": List[Dict],
            "message": str
        }
    """
    created_count = 0
    skipped_count = 0
    error_list = []

    try:
        # Load all ActorMention records for this case
        stmt = (
            select(ActorMention)
            .join(Document)
            .where(Document.case_id == case_id)
        )
        res = await db.execute(stmt)
        actor_mentions = res.scalars().all()

        logger.info(f"[EVIDENCE_SERVICE] Backfill: Found {len(actor_mentions)} actor mentions for case {case_id}")

        for mention in actor_mentions:
            try:
                # Deterministic duplicate check: same (actor_mention_id + document_id + offset)
                # For now, we use a simple key: (fact_type=actor_mention, fact_id=mention.id)
                # to prevent duplicates if backfill runs twice.
                existing_stmt = (
                    select(EvidenceReference).where(
                        (EvidenceReference.case_id == case_id)
                        & (EvidenceReference.fact_type == "actor_mention")
                        & (EvidenceReference.fact_id == str(mention.id))
                        & (EvidenceReference.source_document_id == mention.document_id)
                    )
                )
                existing = await db.execute(existing_stmt)
                if existing.scalar_one_or_none() is not None:
                    skipped_count += 1
                    continue

                # Create EvidenceReference from ActorMention
                evidence_ref = EvidenceReference(
                    case_id=case_id,
                    fact_type="actor_mention",
                    fact_id=str(mention.id),
                    source_type="document",
                    source_document_id=mention.document_id,
                    source_interview_session_id=None,
                    page_number=mention.page_number if hasattr(mention, "page_number") else None,
                    text_span=mention.extracted_text if hasattr(mention, "extracted_text") else None,
                    offset_start=mention.offset_start if hasattr(mention, "offset_start") else None,
                    offset_end=mention.offset_end if hasattr(mention, "offset_end") else None,
                    extraction_confidence=mention.confidence if hasattr(mention, "confidence") else 0.5,
                    source_reliability=0.5,  # Phase 1: simple default
                    binding_type="direct_evidence",
                    supporting_actor_ids=None,
                    notes=f"Backfilled from ActorMention {mention.id}",
                    created_by="system",
                )
                if not dry_run:
                    db.add(evidence_ref)
                created_count += 1

            except Exception as e:
                error_msg = f"Error processing ActorMention {mention.id}: {str(e)}"
                logger.error(f"[EVIDENCE_SERVICE] {error_msg}")
                error_list.append({"mention_id": mention.id, "error": str(e)})

        if not dry_run:
            await db.commit()
            logger.info(
                f"[EVIDENCE_SERVICE] Backfill complete: created={created_count}, "
                f"skipped={skipped_count}, errors={len(error_list)}"
            )
        else:
            logger.info(
                f"[EVIDENCE_SERVICE] Backfill DRY_RUN: would create={created_count}, "
                f"would skip={skipped_count}"
            )

        return {
            "case_id": case_id,
            "dry_run": dry_run,
            "evidence_references_created": created_count,
            "evidence_references_skipped": skipped_count,
            "total_actor_mentions_processed": len(actor_mentions),
            "errors": error_list,
            "message": (
                f"Backfill complete. Created {created_count}, skipped {skipped_count}, "
                f"errors {len(error_list)}. Dry run: {dry_run}."
            ),
        }

    except Exception as e:
        logger.error(f"[EVIDENCE_SERVICE] Backfill failed: {str(e)}")
        error_list.append({"global": str(e)})
        return {
            "case_id": case_id,
            "dry_run": dry_run,
            "evidence_references_created": 0,
            "evidence_references_skipped": 0,
            "total_actor_mentions_processed": 0,
            "errors": error_list,
            "message": f"Backfill failed: {str(e)}",
        }


async def get_evidence_references(
    db: AsyncSession,
    case_id: int,
    fact_type: Optional[str] = None,
    source_type: Optional[str] = None,
    binding_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Retrieve EvidenceReference records with optional filtering.

    Args:
        db: AsyncSession
        case_id: int
        fact_type: Optional filter (actor_mention | event | claim | finding)
        source_type: Optional filter (document | interview_session | deposition | email)
        binding_type: Optional filter (direct_evidence | supporting | circumstantial | contradiction)
        limit: int (default 100)
        offset: int (default 0)

    Returns:
        {
            "case_id": int,
            "total": int,
            "limit": int,
            "offset": int,
            "evidence_references": List[EvidenceReferenceResponse]
        }
    """
    stmt = select(EvidenceReference).where(EvidenceReference.case_id == case_id)

    if fact_type:
        stmt = stmt.where(EvidenceReference.fact_type == fact_type)
    if source_type:
        stmt = stmt.where(EvidenceReference.source_type == source_type)
    if binding_type:
        stmt = stmt.where(EvidenceReference.binding_type == binding_type)

    # Get total count
    count_stmt = select(EvidenceReference).where(EvidenceReference.case_id == case_id)
    if fact_type:
        count_stmt = count_stmt.where(EvidenceReference.fact_type == fact_type)
    if source_type:
        count_stmt = count_stmt.where(EvidenceReference.source_type == source_type)
    if binding_type:
        count_stmt = count_stmt.where(EvidenceReference.binding_type == binding_type)

    count_res = await db.execute(count_stmt)
    total = len(count_res.scalars().all())

    # Apply pagination
    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    references = res.scalars().all()

    return {
        "case_id": case_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "evidence_references": references,
    }
