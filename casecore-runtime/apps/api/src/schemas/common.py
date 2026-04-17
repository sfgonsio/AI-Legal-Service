from typing import Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: Optional[dict] = None


class StandardResponse(BaseModel):
    success: bool = True
    correlation_id: str = Field(..., min_length=1)
