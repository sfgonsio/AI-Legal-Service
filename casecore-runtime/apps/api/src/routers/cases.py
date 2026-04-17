from fastapi import APIRouter, Depends
from src.schemas.cases import CreateCaseRequest, CreateCaseResponse, GetCaseResponse
from src.dependencies import get_persistence_client
from src.utils.ids import new_id

router = APIRouter(tags=["cases"])


@router.post("/cases", response_model=CreateCaseResponse)
def create_case(body: CreateCaseRequest, persistence=Depends(get_persistence_client)):
    correlation_id = new_id()
    case = {
        "case_id": new_id(),
        "title": body.title,
        "case_type": body.case_type,
        "jurisdiction": body.jurisdiction,
        "perspective": body.perspective,
        "status": "OPEN",
    }
    persistence.create_case(case)
    return CreateCaseResponse(correlation_id=correlation_id, case=case)


@router.get("/cases/{case_id}", response_model=GetCaseResponse)
def get_case(case_id: str, persistence=Depends(get_persistence_client)):
    correlation_id = new_id()
    case = persistence.get_case(case_id)
    return GetCaseResponse(correlation_id=correlation_id, case=case)

