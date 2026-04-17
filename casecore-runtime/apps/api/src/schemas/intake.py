"""
INTAKE_ENGINE Schemas — Phase 2: Structured Intake & Narrative Modeling

Artifacts:
  1. IntakeNarrativeRecord — original client narrative, preserved unmodified
  2. StructuredIntakeModel — parties, events, timeline, relationships
  3. CaseContextRecord — case type, jurisdiction, claim categories
  4. IntakeGapSummary — missing info, ambiguities, inconsistencies

State machine: CREATED -> INTERVIEWING -> STRUCTURING -> REFINING -> COMPLETE | ESCALATED
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from .common import StandardResponse


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IntakeStatus(str, Enum):
    CREATED = "CREATED"
    INTERVIEWING = "INTERVIEWING"
    STRUCTURING = "STRUCTURING"
    REFINING = "REFINING"
    COMPLETE = "COMPLETE"
    ESCALATED = "ESCALATED"


class PartyRole(str, Enum):
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    WITNESS = "witness"
    EXPERT = "expert"
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


class GapSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GapType(str, Enum):
    MISSING_INFO = "missing_info"
    AMBIGUITY = "ambiguity"
    CONTRADICTION = "contradiction"
    TIMELINE_GAP = "timeline_gap"
    UNIDENTIFIED_PARTY = "unidentified_party"


class EventType(str, Enum):
    INCIDENT = "incident"
    COMMUNICATION = "communication"
    AGREEMENT = "agreement"
    BREACH = "breach"
    DISCOVERY = "discovery"
    LEGAL_ACTION = "legal_action"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Sub-models: Parties, Events, Relationships, Timeline
# ---------------------------------------------------------------------------

class Party(BaseModel):
    party_id: str
    name: Optional[str] = None
    role: PartyRole = PartyRole.UNKNOWN
    description: Optional[str] = None
    known_aliases: list[str] = Field(default_factory=list)
    contact_info: Optional[str] = None


class Event(BaseModel):
    event_id: str
    event_type: EventType = EventType.OTHER
    description: str
    date_approximate: Optional[str] = None
    date_precision: Optional[str] = None  # "exact", "month", "quarter", "year", "unknown"
    location: Optional[str] = None
    parties_involved: list[str] = Field(default_factory=list)
    source_narrative_ref: Optional[str] = None


class Relationship(BaseModel):
    relationship_id: str
    party_a: str
    party_b: str
    relationship_type: str  # "employer_employee", "contractual", "familial", etc.
    description: Optional[str] = None


class TimelineEntry(BaseModel):
    event_id: str
    sequence_order: int
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    disputed: bool = False
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Artifact 1: Intake Narrative Record (original, immutable)
# ---------------------------------------------------------------------------

class IntakeNarrativeRecord(BaseModel):
    """Original client narrative preserved without modification (governance control)."""
    narrative_id: str
    case_id: str
    original_text: str
    captured_at: datetime
    captured_by: str  # "client", "attorney", "interview_agent"
    source_method: str  # "direct_entry", "interview", "document_upload"


# ---------------------------------------------------------------------------
# Artifact 2: Structured Intake Model
# ---------------------------------------------------------------------------

class StructuredIntakeModel(BaseModel):
    """Organized representation of parties, events, timeline, relationships."""
    intake_model_id: str
    case_id: str
    narrative_id: str
    parties: list[Party] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    structured_at: datetime
    version: int = 1


# ---------------------------------------------------------------------------
# Artifact 3: Case Context Record
# ---------------------------------------------------------------------------

class CaseContextRecord(BaseModel):
    """Initial classification: case type, jurisdiction, claim categories."""
    context_id: str
    case_id: str
    case_type: Optional[str] = None
    case_subtype: Optional[str] = None
    jurisdiction: Optional[str] = None
    venue: Optional[str] = None
    claim_categories: list[str] = Field(default_factory=list)
    applicable_codes: list[str] = Field(default_factory=list)
    statute_of_limitations: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Artifact 4: Intake Gap Summary
# ---------------------------------------------------------------------------

class IntakeGap(BaseModel):
    gap_id: str
    gap_type: GapType
    severity: GapSeverity
    description: str
    related_events: list[str] = Field(default_factory=list)
    related_parties: list[str] = Field(default_factory=list)
    suggested_question: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class IntakeGapSummary(BaseModel):
    gap_summary_id: str
    case_id: str
    intake_model_id: str
    gaps: list[IntakeGap] = Field(default_factory=list)
    total_gaps: int = 0
    critical_gaps: int = 0
    assessed_at: datetime


# ---------------------------------------------------------------------------
# Conversation / Interview Models
# ---------------------------------------------------------------------------

class InterviewMessage(BaseModel):
    message_id: str
    role: str  # "agent", "client", "attorney"
    content: str
    timestamp: datetime
    metadata: Optional[dict] = None


class InterviewSession(BaseModel):
    session_id: str
    case_id: str
    intake_id: str
    messages: list[InterviewMessage] = Field(default_factory=list)
    status: str = "active"
    started_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Master Intake Record
# ---------------------------------------------------------------------------

class IntakeRecord(BaseModel):
    case_id: str
    intake_id: str
    status: IntakeStatus = IntakeStatus.CREATED
    narrative: Optional[IntakeNarrativeRecord] = None
    structured_model: Optional[StructuredIntakeModel] = None
    case_context: Optional[CaseContextRecord] = None
    gap_summary: Optional[IntakeGapSummary] = None
    interview_session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    refinement_count: int = 0


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------

class StartIntakeRequest(BaseModel):
    """POST /cases/{case_id}/intake/start"""
    narrative: str = Field(..., min_length=1, description="Initial client narrative")
    client_name: Optional[str] = None
    incident_date: Optional[str] = None
    case_type_hint: Optional[str] = None
    jurisdiction_hint: Optional[str] = None


class StartIntakeResponse(StandardResponse):
    intake: IntakeRecord
    interview_session_id: str
    initial_questions: list[str] = Field(default_factory=list)


class RespondIntakeRequest(BaseModel):
    """POST /cases/{case_id}/intake/respond"""
    session_id: str
    message: str = Field(..., min_length=1)
    role: str = "client"


class RespondIntakeResponse(StandardResponse):
    intake: IntakeRecord
    follow_up_questions: list[str] = Field(default_factory=list)
    new_gaps_detected: int = 0
    gaps_resolved: int = 0


class GetIntakeResponse(StandardResponse):
    intake: IntakeRecord


class GetIntakeGapsResponse(StandardResponse):
    gap_summary: IntakeGapSummary
    suggested_questions: list[str] = Field(default_factory=list)


class CompleteIntakeRequest(BaseModel):
    """POST /cases/{case_id}/intake/complete"""
    attorney_notes: Optional[str] = None
    force_complete: bool = False


class CompleteIntakeResponse(StandardResponse):
    intake: IntakeRecord
    unresolved_gaps: int = 0
    warnings: list[str] = Field(default_factory=list)
