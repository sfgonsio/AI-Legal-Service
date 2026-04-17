from fastapi import APIRouter, Depends
from src.schemas.audit import ListAuditResponse
from src.dependencies import get_audit_client
from src.utils.ids import new_id

router = APIRouter(tags=["audit"])


@router.get("/cases/{case_id}/audit", response_model=ListAuditResponse)
def list_audit(case_id: str, audit=Depends(get_audit_client)):
    correlation_id = new_id()
    items = audit.list_events(case_id)
    return ListAuditResponse(correlation_id=correlation_id, items=items)

