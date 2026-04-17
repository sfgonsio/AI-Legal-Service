from typing import Literal, Optional
from pydantic import BaseModel, Field
from .common import StandardResponse


RetrievalMode = Literal[
    "AUTHORITATIVE_ONLY",
    "AUTHORITATIVE_PLUS_SECONDARY",
    "EXPLORATORY_ALLOWED",
    "COMPARATIVE_RESEARCH",
    "BROAD_RESEARCH",
]

PurposeType = Literal["LEGAL_ANALYSIS", "EXPLORATION", "COMPARISON"]
SourceClass = Literal[
    "AUTHORITATIVE_PRIMARY",
    "AUTHORITATIVE_SECONDARY",
    "EXPLORATORY",
    "UNTRUSTED",
]
TrustLane = Literal["PRIMARY", "SECONDARY", "EXPLORATORY", "UNTRUSTED", "DERIVED"]


class RetrievalFilters(BaseModel):
    source_classes: list[SourceClass] = []
    authority_level: list[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1)
    mode: RetrievalMode
    jurisdiction: str = Field(..., min_length=1)
    purpose: PurposeType
    requesting_component: str = Field(..., min_length=1)
    filters: RetrievalFilters = RetrievalFilters()


class RetrievalResultMetadata(BaseModel):
    source_name: str
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    retrieved_at: str
    ingest_hash: str


class RetrievalResult(BaseModel):
    content: str
    source_class: SourceClass
    trust_lane: TrustLane
    citation: str
    jurisdiction: str
    confidence: str
    metadata: RetrievalResultMetadata


class RetrievalResponse(StandardResponse):
    retrieval_audit_id: str
    results: list[RetrievalResult]
