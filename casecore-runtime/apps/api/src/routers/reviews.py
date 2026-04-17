from fastapi import APIRouter, Depends
from src.schemas.reviews import ListReviewsResponse, ReviewDecisionRequest, ReviewDecisionResponse
from src.dependencies import get_review_client
from src.utils.ids import new_id

router = APIRouter(tags=["reviews"])


@router.get("/cases/{case_id}/reviews", response_model=ListReviewsResponse)
def list_reviews(case_id: str, reviews=Depends(get_review_client)):
    correlation_id = new_id()
    items = reviews.list_reviews(case_id)
    return ListReviewsResponse(correlation_id=correlation_id, items=items)


@router.post("/reviews/{review_id}/decision", response_model=ReviewDecisionResponse)
def review_decision(review_id: str, body: ReviewDecisionRequest, reviews=Depends(get_review_client)):
    correlation_id = new_id()
    review = reviews.decide_review(review_id, body.model_dump())
    return ReviewDecisionResponse(correlation_id=correlation_id, review=review)

