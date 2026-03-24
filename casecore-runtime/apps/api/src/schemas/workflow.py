from pydantic import BaseModel
from .common import StandardResponse


class WorkflowState(BaseModel):
    case_id: str
    current_state: str
    last_transition_at: str


class GetWorkflowResponse(StandardResponse):
    workflow: WorkflowState
