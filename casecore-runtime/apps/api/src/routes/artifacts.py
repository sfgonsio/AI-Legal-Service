from fastapi import APIRouter

router = APIRouter()

@router.get("/artifacts/{artifact_id}")
def get_artifact(artifact_id: str):
    return {
        "artifact_id": artifact_id,
        "status": "scaffold",
        "note": "Artifact retrieval scaffold only."
    }
