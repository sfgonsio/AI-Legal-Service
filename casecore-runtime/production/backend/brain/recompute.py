"""
Downstream recompute pipeline triggered by case authority decision changes.

Invoked from the /case-authority/decisions route after commit.

Scope per decision:
  - COA rows where coa.caci_ref == decision.caci_id AND coa.case_id == decision.case_id
    → re-resolve authority and snapshot (decision_id, pinned_record_id, effective_grounding)
      onto the COA row.
    → if REJECTED: mark COA status "blocked_by_rejection" (audit), do not delete.
    → if REPLACED: COA now resolves via the replacement; snapshot reflects this.
  - Burden rows (BurdenElement) attached to affected COAs are left in place for audit;
    the next burden-mapping build will re-emit preview/grounded rows per program contract.
  - Remedy rows (program_REMEDY_DERIVATION) are program-level; this function emits
    the recompute event that the remedy builder consumes on next run.
  - Complaint mapping (program_COMPLAINT_PARSE) is gated at citation time against the
    resolver; no rewrite here.
  - Weapons carry a `caci` ref; snapshot is advisory — weapons route fetches authority
    block on demand.

All activity is recorded in a RecomputeEvent row for audit.
"""
from datetime import datetime
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import CaseAuthorityDecision, COA, BurdenElement, RecomputeEvent
from .authority_resolver import resolve_authority, NONE as GROUNDING_NONE, GROUNDED_VIA_REPLACEMENT


async def recompute_for_decision(
    db: AsyncSession, decision: CaseAuthorityDecision
) -> RecomputeEvent:
    """
    Re-resolve authority for all downstream artifacts in this case that depend
    on decision.caci_id, and record a RecomputeEvent for audit.
    """
    scope = {
        "coa_ids": [],
        "burden_element_count": 0,
        "remedy_recompute_requested": True,
        "complaint_revalidation_requested": True,
    }

    # COAs impacted
    res = await db.execute(
        select(COA).where(COA.case_id == decision.case_id).where(COA.caci_ref == decision.caci_id)
    )
    coas: List[COA] = list(res.scalars().all())
    for coa in coas:
        resolved = await resolve_authority(db, decision.case_id, decision.caci_id)
        coa.authority_decision_id = resolved.decision_id
        coa.authority_pinned_record_id = resolved.pinned_record_id
        coa.authority_effective_grounding = resolved.effective_grounding
        if resolved.effective_grounding == GROUNDING_NONE and decision.state == "REJECTED":
            coa.status = "blocked_by_rejection"
        elif resolved.effective_grounding == GROUNDED_VIA_REPLACEMENT:
            coa.status = "grounded_via_replacement"
        elif resolved.effective_grounding == "GROUNDED":
            coa.status = "grounded"
        elif resolved.effective_grounding == "PROPOSED":
            coa.status = "proposed"
        scope["coa_ids"].append(coa.id)
        # explicit async count to avoid lazy-load of burden_elements
        be_res = await db.execute(
            select(func.count(BurdenElement.id)).where(BurdenElement.coa_id == coa.id)
        )
        scope["burden_element_count"] += int(be_res.scalar() or 0)

    event = RecomputeEvent(
        case_id=decision.case_id,
        triggered_by_decision_id=decision.decision_id,
        caci_id=decision.caci_id,
        scope_json=scope,
        status="completed",
        created_at=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
