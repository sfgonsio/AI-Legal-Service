from pydantic import BaseModel, Field
from .common import StandardResponse


class ReviewItem(BaseModel):
    review_id: str
    case_id: str
    artifact_id: str
    status: str
    decision: str | None = None


class ListReviewsResponse(StandardResponse):
    items: list[ReviewItem]


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(accept|reject|promote)$")
    rationale: str | None = None


class ReviewDecisionResponse(StandardResponse):
    review: ReviewItem
