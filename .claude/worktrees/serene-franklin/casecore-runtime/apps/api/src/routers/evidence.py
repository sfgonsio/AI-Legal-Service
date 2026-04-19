from fastapi import APIRouter
from src.schemas.evidence import RegisterEvidenceRequest, RegisterEvidenceResponse, ListEvidenceResponse
from src.utils.ids import new_id

router = APIRouter(tags=["evidence"])


@router.post("/cases/{case_id}/evidence", response_model=RegisterEvidenceResponse)
def register_evidence(case_id: str, body: RegisterEvidenceRequest):
    correlation_id = new_id()
    item = {
        "evidence_id": new_id(),
        "case_id": case_id,
        "evidence_type": body.evidence_type,
        "title": body.title,
        "description": body.description,
        "status": "REGISTERED",
    }
    return RegisterEvidenceResponse(correlation_id=correlation_id, evidence=item)


@router.get("/cases/{case_id}/evidence", response_model=ListEvidenceResponse)
def list_evidence(case_id: str):
    correlation_id = new_id()
    return ListEvidenceResponse(correlation_id=correlation_id, items=[])

