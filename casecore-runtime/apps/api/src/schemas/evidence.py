from typing import Optional
from pydantic import BaseModel, Field
from .common import StandardResponse


class RegisterEvidenceRequest(BaseModel):
    evidence_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    storage_ref: Optional[str] = None


class EvidenceItem(BaseModel):
    evidence_id: str
    case_id: str
    evidence_type: str
    title: str
    description: Optional[str] = None
    status: str


class RegisterEvidenceResponse(StandardResponse):
    evidence: EvidenceItem


class ListEvidenceResponse(StandardResponse):
    items: list[EvidenceItem]
