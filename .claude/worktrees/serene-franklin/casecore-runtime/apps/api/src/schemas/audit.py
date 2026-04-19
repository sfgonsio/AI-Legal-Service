from pydantic import BaseModel
from .common import StandardResponse


class AuditEvent(BaseModel):
    event_id: str
    event_type: str
    case_id: str
    timestamp: str
    correlation_id: str


class ListAuditResponse(StandardResponse):
    items: list[AuditEvent]
