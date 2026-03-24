from fastapi import APIRouter, Depends
from src.schemas.retrieval import RetrievalRequest, RetrievalResponse
from src.dependencies import get_retrieval_gateway
from src.utils.ids import new_id

router = APIRouter(tags=["retrieval"])


@router.post("/cases/{case_id}/retrieve", response_model=RetrievalResponse)
def retrieve(case_id: str, body: RetrievalRequest, gateway=Depends(get_retrieval_gateway)):
    correlation_id = new_id()
    result = gateway.execute(
        case_id=case_id,
        correlation_id=correlation_id,
        request=body.model_dump(),
    )
    return RetrievalResponse(
        correlation_id=correlation_id,
        retrieval_audit_id=result["retrieval_audit_id"],
        results=result["results"],
    )

