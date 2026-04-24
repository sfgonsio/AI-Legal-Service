"""
Case save-state machine. Enforces the transition matrix from
contract/v1/schemas/case/case_save_state.schema.json and writes an audit
event on every transition.

No code path outside this module should mutate `case.save_state` directly.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models import Case, CaseStateEvent


DRAFT = "DRAFT"
SAVED = "SAVED"
READY_FOR_ANALYSIS = "READY_FOR_ANALYSIS"
PROCESSING = "PROCESSING"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
APPROVED = "APPROVED"
RETURNED_TO_INTAKE = "RETURNED_TO_INTAKE"

ALL_STATES = {
    DRAFT, SAVED, READY_FOR_ANALYSIS, PROCESSING,
    REVIEW_REQUIRED, APPROVED, RETURNED_TO_INTAKE,
}

# Allowed transitions (including self-loops where saving stays in DRAFT/SAVED).
ALLOWED = {
    DRAFT:              {DRAFT, SAVED, RETURNED_TO_INTAKE},
    SAVED:              {DRAFT, SAVED, READY_FOR_ANALYSIS, PROCESSING, RETURNED_TO_INTAKE},
    READY_FOR_ANALYSIS: {DRAFT, SAVED, READY_FOR_ANALYSIS, PROCESSING, RETURNED_TO_INTAKE},
    PROCESSING:         {REVIEW_REQUIRED, RETURNED_TO_INTAKE},
    REVIEW_REQUIRED:    {REVIEW_REQUIRED, APPROVED, RETURNED_TO_INTAKE},
    APPROVED:           {APPROVED, RETURNED_TO_INTAKE},
    RETURNED_TO_INTAKE: {DRAFT},
}

# States in which analytical reads (COA authority, case-to-authority map) are allowed.
POST_ANALYSIS_STATES = {PROCESSING, REVIEW_REQUIRED, APPROVED}

# States in which save-draft is a valid transition target.
SAVE_TARGETS = {DRAFT, SAVED}


class InvalidTransition(Exception):
    def __init__(self, from_state: str, to_state: str):
        super().__init__(f"Invalid state transition {from_state} -> {to_state}")
        self.from_state = from_state
        self.to_state = to_state


async def transition(
    db: AsyncSession,
    case: Case,
    to_state: str,
    actor_id: str = "system",
    actor_type: str = "SYSTEM",
    reason: Optional[str] = None,
) -> CaseStateEvent:
    """Transition a case to a new state, or raise InvalidTransition."""
    from_state = case.save_state or DRAFT
    if to_state not in ALL_STATES:
        raise InvalidTransition(from_state, to_state)
    if to_state not in ALLOWED.get(from_state, set()):
        raise InvalidTransition(from_state, to_state)

    case.save_state = to_state
    event = CaseStateEvent(
        case_id=case.id,
        from_state=from_state,
        to_state=to_state,
        actor_id=actor_id,
        actor_type=actor_type,
        reason=reason,
        at=datetime.utcnow(),
    )
    db.add(event)
    return event
