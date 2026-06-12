"""
Brain authority resolver.

Single gate between case decisions / provisional records and all downstream mappers.

Resolution order (non-negotiable):
  1. case-level decision
  2. active provisional record status
  3. confidence threshold (already baked into record status)

See contract/v1/brain/case_authority_resolution.md
"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models import CaseAuthorityDecision
from .provisional_store import load_active_record, load_record_by_id, ProvisionalStoreError


# Grounding vocabulary
GROUNDED = "GROUNDED"
GROUNDED_VIA_REPLACEMENT = "GROUNDED_VIA_REPLACEMENT"
PROPOSED = "PROPOSED"
NONE = "NONE"

# Provisional record status
STATUS_PROVISIONAL = "PROVISIONAL"
STATUS_BLOCKED = "BLOCKED_UNTRUSTED"
STATUS_SUPERSEDED = "SUPERSEDED"

# Decision states
DEC_PENDING = "PENDING_REVIEW"
DEC_ACCEPTED = "ACCEPTED"
DEC_REJECTED = "REJECTED"
DEC_REPLACED = "REPLACED"


@dataclass
class ResolvedAuthority:
    case_id: int
    caci_id: str
    certified: Dict[str, Any] = field(default_factory=lambda: {
        "present": False, "authority_id": None, "record_ref": None,
    })
    provisional_candidate: Dict[str, Any] = field(default_factory=lambda: {
        "caci_id": None, "record_id": None, "confidence": None, "status": None,
    })
    case_decision: Dict[str, Any] = field(default_factory=lambda: {
        "state": DEC_PENDING, "decision_id": None, "replacement_authority_id": None,
    })
    effective_grounding: str = PROPOSED
    display_badge: str = "provisional-candidate"
    decision_id: Optional[str] = None
    pinned_record_id: Optional[str] = None
    requires_attorney_review: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


async def _latest_decision(
    db: AsyncSession, case_id: int, caci_id: str
) -> Optional[CaseAuthorityDecision]:
    """Latest decision that is NOT itself superseded."""
    stmt = (
        select(CaseAuthorityDecision)
        .where(CaseAuthorityDecision.case_id == case_id)
        .where(CaseAuthorityDecision.caci_id == caci_id)
        .where(CaseAuthorityDecision.superseded_by_decision_id.is_(None))
        .order_by(desc(CaseAuthorityDecision.decided_at))
        .limit(1)
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


def _provisional_signal(record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not record:
        return {"caci_id": None, "record_id": None, "confidence": None, "status": None}
    return {
        "caci_id": record.get("caci_id"),
        "record_id": record.get("record_id"),
        "confidence": (record.get("confidence") or {}).get("overall"),
        "status": record.get("status"),
    }


async def resolve_authority(
    db: AsyncSession, case_id: int, caci_id: str
) -> ResolvedAuthority:
    """
    Produce the tri-signal resolved authority for a (case_id, caci_id).

    This is the ONLY supported path for downstream mappers to read CACI authority.
    """
    out = ResolvedAuthority(case_id=case_id, caci_id=caci_id)

    # --- Step 1: case-level decision ---
    decision = await _latest_decision(db, case_id, caci_id)

    # --- Step 2: load provisional records ---
    try:
        active_record = load_active_record(caci_id)
    except ProvisionalStoreError:
        active_record = None

    # Default provisional-signal is the currently active record (used for display
    # in all branches, even after a REJECTED decision, so UI can show history).
    out.provisional_candidate = _provisional_signal(active_record)

    if decision is None:
        # Synthesize PENDING_REVIEW against the active record.
        out.case_decision = {
            "state": DEC_PENDING,
            "decision_id": None,
            "replacement_authority_id": None,
        }
        out.pinned_record_id = (active_record or {}).get("record_id")
        if active_record and active_record.get("status") == STATUS_BLOCKED:
            out.effective_grounding = NONE
            out.display_badge = "blocked-untrusted"
            out.requires_attorney_review = True
        elif active_record:
            out.effective_grounding = PROPOSED
            out.display_badge = "provisional-candidate"
            out.requires_attorney_review = True
        else:
            out.effective_grounding = NONE
            out.display_badge = "no-provisional-record"
            out.requires_attorney_review = True
        return out

    out.decision_id = decision.decision_id
    out.pinned_record_id = decision.pinned_record_id
    out.case_decision = {
        "state": decision.state,
        "decision_id": decision.decision_id,
        "replacement_authority_id": (
            (decision.replacement_json or {}).get("authority_id")
            if decision.state == DEC_REPLACED else None
        ),
    }

    if decision.state == DEC_REJECTED:
        out.effective_grounding = NONE
        out.display_badge = "attorney-rejected"
        out.requires_attorney_review = False
        return out

    if decision.state == DEC_REPLACED:
        rep = decision.replacement_json or {}
        out.effective_grounding = GROUNDED_VIA_REPLACEMENT
        out.display_badge = f"replaced-by:{rep.get('authority_id', 'unknown')}"
        out.requires_attorney_review = False
        is_certified = rep.get("authority_type") in ("STATUTE", "CASE_LAW", "CERTIFIED_CACI", "REGULATION")
        out.certified = {
            "present": is_certified,
            "authority_id": rep.get("authority_id"),
            "record_ref": rep.get("record_ref"),
        }
        return out

    if decision.state == DEC_ACCEPTED:
        # Load the pinned record (may be in active or superseded store).
        pinned = None
        if decision.pinned_record_id:
            try:
                pinned = load_record_by_id(caci_id, decision.pinned_record_id)
            except ProvisionalStoreError:
                pinned = None

        if not pinned:
            out.effective_grounding = NONE
            out.display_badge = "pinned-record-missing"
            out.error = "pinned_record_id not found in active or superseded store"
            out.requires_attorney_review = True
            return out

        # Safety rule: an ACCEPTED decision written against a BLOCKED_UNTRUSTED
        # record is refused. (The create-decision route already refuses this, but
        # we re-check here to cover data that may drift over time.)
        if pinned.get("status") == STATUS_BLOCKED:
            out.effective_grounding = NONE
            out.display_badge = "accepted-over-blocked-refused"
            out.error = "ERROR_ACCEPTED_OVER_BLOCKED"
            out.requires_attorney_review = True
            return out

        out.effective_grounding = GROUNDED
        out.display_badge = "attorney-accepted (provisional)"
        out.requires_attorney_review = False
        # Override provisional_candidate to show the PINNED record (not active),
        # so downstream sees what was actually used.
        out.provisional_candidate = _provisional_signal(pinned)
        return out

    # Fallback: PENDING_REVIEW (explicitly written)
    if active_record and active_record.get("status") == STATUS_BLOCKED:
        out.effective_grounding = NONE
        out.display_badge = "blocked-untrusted"
    elif active_record:
        out.effective_grounding = PROPOSED
        out.display_badge = "provisional-candidate"
    else:
        out.effective_grounding = NONE
        out.display_badge = "no-provisional-record"
    out.requires_attorney_review = True
    return out
