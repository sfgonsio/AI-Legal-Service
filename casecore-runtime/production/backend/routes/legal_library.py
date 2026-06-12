"""
Legal Library HTTP routes.

GET /legal-library/stats         — corpus stats, root path, supported codes
GET /legal-library/records       — list, filterable by code + q, pagination
GET /legal-library/records/{id}  — full record with body_text + body_status
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from brain import legal_library


router = APIRouter(prefix="/legal-library", tags=["legal-library"])


class StatsResponse(BaseModel):
    root: str
    total_records: int
    by_code: dict
    supported_codes: list
    missing_codes_hint: str


@router.get("/stats", response_model=StatsResponse)
def stats():
    return legal_library.corpus_stats()


@router.get("/records")
def list_records(
    code: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
):
    limit = max(1, min(int(limit or 200), 1000))
    offset = max(0, int(offset or 0))
    return legal_library.list_records(code=code, q=q, limit=limit, offset=offset)


@router.get("/records/{record_id}")
def get_record(record_id: str):
    rec = legal_library.fetch_record(record_id)
    return rec.to_dict()
