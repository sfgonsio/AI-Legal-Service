from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class RunCreateRequest(BaseModel):
    matter_id: str
    initiated_by: str

@router.post("/runs")
def create_run(payload: RunCreateRequest):
    return {
        "accepted": True,
        "run_id": "RUN-API-001",
        "matter_id": payload.matter_id,
        "initiated_by": payload.initiated_by,
        "note": "Scaffold route only. Runtime orchestration not yet implemented."
    }

@router.get("/runs/{run_id}")
def get_run(run_id: str):
    return {
        "run_id": run_id,
        "status": "scaffold",
        "note": "Run retrieval scaffold only."
    }
