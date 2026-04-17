from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class PromotionRequest(BaseModel):
    artifact_id: str
    actor_id: str
    promotion_reason: str

@router.post("/artifacts/promote")
def promote_artifact(payload: PromotionRequest):
    return {
        "accepted": False,
        "artifact_id": payload.artifact_id,
        "actor_id": payload.actor_id,
        "note": "Promotion scaffold only. Runtime enforcement integration required before activation."
    }
