from fastapi import APIRouter, Depends
from src.schemas.workflow import GetWorkflowResponse
from src.dependencies import get_workflow_client
from src.utils.ids import new_id

router = APIRouter(tags=["workflow"])


@router.get("/cases/{case_id}/workflow", response_model=GetWorkflowResponse)
def get_workflow(case_id: str, workflow=Depends(get_workflow_client)):
    correlation_id = new_id()
    state = workflow.get_workflow(case_id)
    return GetWorkflowResponse(correlation_id=correlation_id, workflow=state)

