from fastapi import APIRouter, Depends
from src.schemas.artifacts import ListArtifactsResponse, GetArtifactResponse
from src.dependencies import get_artifact_client
from src.utils.ids import new_id

router = APIRouter(tags=["artifacts"])


@router.get("/cases/{case_id}/artifacts", response_model=ListArtifactsResponse)
def list_artifacts(case_id: str, artifacts=Depends(get_artifact_client)):
    correlation_id = new_id()
    items = artifacts.list_artifacts(case_id)
    return ListArtifactsResponse(correlation_id=correlation_id, items=items)


@router.get("/artifacts/{artifact_id}", response_model=GetArtifactResponse)
def get_artifact(artifact_id: str, artifacts=Depends(get_artifact_client)):
    correlation_id = new_id()
    artifact = artifacts.get_artifact(artifact_id)
    return GetArtifactResponse(correlation_id=correlation_id, artifact=artifact)

