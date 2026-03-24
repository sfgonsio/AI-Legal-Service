from pydantic import BaseModel, Field
from .common import StandardResponse


class CreateCaseRequest(BaseModel):
    title: str = Field(..., min_length=1)
    case_type: str = Field(..., min_length=1)
    jurisdiction: str = Field(..., min_length=1)
    perspective: str = Field(..., min_length=1)


class CaseRecord(BaseModel):
    case_id: str
    title: str
    case_type: str
    jurisdiction: str
    perspective: str
    status: str


class CreateCaseResponse(StandardResponse):
    case: CaseRecord


class GetCaseResponse(StandardResponse):
    case: CaseRecord
