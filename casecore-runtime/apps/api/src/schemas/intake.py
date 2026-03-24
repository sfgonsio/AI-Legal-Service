from typing import Optional
from pydantic import BaseModel, Field
from .common import StandardResponse


class SubmitIntakeRequest(BaseModel):
    narrative: str = Field(..., min_length=1)
    client_name: Optional[str] = None
    incident_date: Optional[str] = None


class IntakeRecord(BaseModel):
    case_id: str
    intake_id: str
    narrative: str
    status: str


class SubmitIntakeResponse(StandardResponse):
    intake: IntakeRecord


class GetIntakeResponse(StandardResponse):
    intake: IntakeRecord
