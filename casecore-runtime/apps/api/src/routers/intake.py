from fastapi import APIRouter
from src.schemas.intake import SubmitIntakeRequest, SubmitIntakeResponse, GetIntakeResponse
from src.utils.ids import new_id

router = APIRouter(tags=["intake"])


@router.post("/cases/{case_id}/intake", response_model=SubmitIntakeResponse)
def submit_intake(case_id: str, body: SubmitIntakeRequest):
    correlation_id = new_id()
    intake = {
        "case_id": case_id,
        "intake_id": new_id(),
        "narrative": body.narrative,
        "status": "RECEIVED",
    }
    return SubmitIntakeResponse(correlation_id=correlation_id, intake=intake)


@router.get("/cases/{case_id}/intake", response_model=GetIntakeResponse)
def get_intake(case_id: str):
    correlation_id = new_id()
    intake = {
        "case_id": case_id,
        "intake_id": new_id(),
        "narrative": "Sample intake narrative",
        "status": "RECEIVED",
    }
    return GetIntakeResponse(correlation_id=correlation_id, intake=intake)

