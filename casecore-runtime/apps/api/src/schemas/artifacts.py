from pydantic import BaseModel
from .common import StandardResponse


class ArtifactRecord(BaseModel):
    artifact_id: str
    case_id: str
    artifact_type: str
    truth_class: str
    review_status: str
    title: str


class ListArtifactsResponse(StandardResponse):
    items: list[ArtifactRecord]


class GetArtifactResponse(StandardResponse):
    artifact: ArtifactRecord
