"""
Pydantic schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ Case Schemas ============

class CaseCreate(BaseModel):
    name: str
    court: Optional[str] = None
    plaintiff: str
    defendant: str


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    court: Optional[str] = None
    plaintiff: Optional[str] = None
    defendant: Optional[str] = None
    status: Optional[str] = None


class CaseResponse(BaseModel):
    id: int
    name: str
    court: Optional[str]
    plaintiff: str
    defendant: str
    status: str
    created_at: datetime
    save_state: str = "DRAFT"
    last_saved_at: Optional[datetime] = None
    last_submitted_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    processing_finished_at: Optional[datetime] = None
    review_required_count: int = 0
    current_analysis_run_id: Optional[str] = None

    class Config:
        from_attributes = True


class CaseDetailResponse(CaseResponse):
    documents: List["DocumentResponse"] = []
    coas: List["COAResponse"] = []
    weapons: List["WeaponResponse"] = []
    strategies: List["StrategyResponse"] = []


# ============ Document Schemas ============

class DocumentCreate(BaseModel):
    case_id: int
    filename: str
    folder: Optional[str] = None
    file_type: Optional[str] = None
    text_content: Optional[str] = None
    char_count: int = 0
    sha256_hash: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    case_id: int
    filename: str
    folder: Optional[str]
    file_type: Optional[str]
    char_count: int
    byte_size: int = 0
    sha256_hash: Optional[str]
    storage_path: Optional[str] = None
    archive_id: Optional[int] = None
    archive_relative_path: Optional[str] = None
    ingest_phase: str = "uploaded"
    ingest_error_detail: Optional[str] = None
    extraction_status: str = "NOT_ATTEMPTED"
    extraction_method: Optional[str] = None
    extraction_confidence: float = 0.0
    is_scanned_pdf: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    text_content: Optional[str]


# ============ Upload / Ingest Schemas ============

class UploadedDocumentResult(BaseModel):
    document_id: int
    filename: str
    folder: Optional[str]
    file_type: Optional[str]
    byte_size: int
    sha256_hash: Optional[str]
    archive_id: Optional[int] = None
    archive_relative_path: Optional[str] = None
    ingest_phase: str
    error_detail: Optional[str] = None


class UploadBatchResponse(BaseModel):
    case_id: int
    accepted_count: int
    rejected_count: int
    archive_id: Optional[int] = None
    documents: List[UploadedDocumentResult]
    errors: List[str] = Field(default_factory=list)


class IngestStatusDocument(BaseModel):
    id: int
    filename: str
    folder: Optional[str]
    file_type: Optional[str]
    ingest_phase: str
    ingest_started_at: Optional[datetime]
    ingest_finished_at: Optional[datetime]
    error_detail: Optional[str] = None
    actor_mention_count: int = 0
    # Extraction reliability (mirrors Document fields for UI convenience)
    extraction_status: str = "NOT_ATTEMPTED"
    extraction_method: Optional[str] = None
    extraction_confidence: float = 0.0
    is_scanned_pdf: bool = False


class IngestStatusResponse(BaseModel):
    case_id: int
    phase_counts: Dict[str, int]
    success_count: int
    failure_count: int
    in_flight_count: int
    documents: List[IngestStatusDocument]


class UploadArchiveResponse(BaseModel):
    id: int
    case_id: int
    original_filename: str
    sha256_hash: Optional[str]
    byte_size: int
    entry_count: int
    uploaded_at: datetime
    uploaded_by_actor_id: Optional[str]

    class Config:
        from_attributes = True


# ============ Actor Schemas ============

class ActorMentionResponse(BaseModel):
    id: int
    actor_id: int
    document_id: Optional[int] = None
    interview_id: Optional[int] = None
    source_kind: str = "DOCUMENT"
    snippet: Optional[str]
    offset_start: Optional[int]
    offset_end: Optional[int]
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class ActorResponse(BaseModel):
    id: int
    case_id: int
    display_name: str
    canonical_name: str
    entity_type: str
    resolution_state: str
    role_hint: Optional[str]
    mention_count: int
    first_seen_document_id: Optional[int]
    last_seen_document_id: Optional[int]
    source: str = "MANUAL"
    source_interview_id: Optional[int] = None
    merged_into_actor_id: Optional[int] = None
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActorCreateRequest(BaseModel):
    case_id: int
    display_name: str
    canonical_name: Optional[str] = None
    entity_type: str = "PERSON"
    resolution_state: str = "RESOLVED"  # user-created -> RESOLVED by default
    role_hint: Optional[str] = None
    notes: Optional[str] = None
    actor_id: Optional[str] = None  # attorney id for audit


class ActorMergeRequest(BaseModel):
    source_actor_ids: List[int]
    target_actor_id: int
    actor_id: Optional[str] = None


class ActorMergeResponse(BaseModel):
    target_actor_id: int
    merged_actor_ids: List[int]
    moved_mentions: int


class ActorsGroupedResponse(BaseModel):
    case_id: int
    counts: Dict[str, int]
    resolved: List[ActorResponse]
    candidate: List[ActorResponse]
    ambiguous: List[ActorResponse]
    organizations: List[ActorResponse]


class ActorUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    canonical_name: Optional[str] = None
    entity_type: Optional[str] = None
    resolution_state: Optional[str] = None
    role_hint: Optional[str] = None
    notes: Optional[str] = None
    actor_id: Optional[str] = None  # attorney id for audit


# ============ Upload UX Schemas ============

class UploadConfigResponse(BaseModel):
    """Advertised limits + supported types for client-side pre-validation."""
    max_file_bytes: int
    max_archive_bytes: int
    max_archive_uncompressed_bytes: int
    max_archive_entries: int
    supported_extensions: List[str]
    # extension -> bucket label used by the UI (text|email|html|pdf|docx|image|archive|binary)
    extension_buckets: Dict[str, str]
    skipped_path_substrings: List[str]


class CheckHashesRequest(BaseModel):
    sha256_list: List[str]


class HashCheckHit(BaseModel):
    sha256_hash: str
    document_id: int
    filename: str
    folder: Optional[str]
    ingest_phase: str


class CheckHashesResponse(BaseModel):
    case_id: int
    duplicates: List[HashCheckHit]


# ============ Interview Schemas ============

class InterviewQuestionResponse(BaseModel):
    id: int
    question_key: str
    prompt: str
    order_index: int
    completion_kind: str
    answer_text: Optional[str]
    answered: bool
    answered_at: Optional[datetime]

    class Config:
        from_attributes = True


class InterviewQuestionUpdate(BaseModel):
    answer_text: Optional[str] = None


class InterviewResponse(BaseModel):
    id: int
    case_id: int
    mode: str
    narrative_text: Optional[str]
    processing_state: str
    last_error_detail: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    processed_at: Optional[datetime]
    questions: List[InterviewQuestionResponse] = []

    class Config:
        from_attributes = True


class InterviewCreateRequest(BaseModel):
    case_id: int
    mode: str = "GUIDED_QUESTIONS"


class InterviewModeSwitchRequest(BaseModel):
    mode: str  # GUIDED_QUESTIONS | FREEFORM_NARRATIVE


class InterviewNarrativeUpdate(BaseModel):
    narrative_text: str


class InterviewCompleteRequest(BaseModel):
    actor_id: Optional[str] = None


class TimelineActorRef(BaseModel):
    id: int
    display_name: str
    role_hint: Optional[str] = None


class TimelineEventLegalMappingResponse(BaseModel):
    legal_element_type: str          # COA_ELEMENT | BURDEN_OF_PRODUCTION | BURDEN_OF_PERSUASION | REMEDY | EVIDENCE_ADMISSIBILITY | PROCEDURAL
    element_reference: Optional[str] = None  # e.g. CACI_303, EVID_1220
    element_label: str
    confidence: float
    rationale: Optional[str] = None
    supporting_evidence_refs: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TimelineStrategyFlags(BaseModel):
    deposition_target: bool = False
    interrogatory_target: bool = False
    document_request_target: bool = False


class TimelineEventResponse(BaseModel):
    event_id: str
    case_id: int
    timestamp: Optional[datetime] = None
    raw_date_text: Optional[str] = None
    date_precision: str
    summary: str
    event_type: str
    source: str
    source_document_id: Optional[int] = None
    source_interview_id: Optional[int] = None
    text_offset_start: Optional[int] = None
    text_offset_end: Optional[int] = None
    snippet: Optional[str] = None
    actor_ids: List[int] = Field(default_factory=list)
    actors: List[TimelineActorRef] = Field(default_factory=list)
    confidence: float
    # Legal layer (heuristic hints; NOT grounded analysis)
    claim_relation: str = "NEUTRAL"
    strategy: TimelineStrategyFlags = Field(default_factory=TimelineStrategyFlags)
    strategy_rationale: Optional[str] = None
    legal_mappings: List[TimelineEventLegalMappingResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TimelineDateGroup(BaseModel):
    """A group key for the UI: date string or 'UNKNOWN'."""
    key: str                                # YYYY-MM-DD, YYYY-MM, YYYY, or "UNKNOWN"
    label: str                              # human-readable label
    precision: str                          # DAY | MONTH | YEAR | UNKNOWN
    events: List[TimelineEventResponse]


class TimelineResponse(BaseModel):
    case_id: int
    total: int
    counts_by_source: Dict[str, int]
    counts_by_type: Dict[str, int]
    known_count: int
    unknown_count: int
    groups: List[TimelineDateGroup]
    last_built_at: Optional[datetime] = None


class TimelineBuildRequest(BaseModel):
    actor_id: Optional[str] = None          # attorney id for audit
    replace: bool = True                    # rebuild from scratch (default)


class TimelineBuildResponse(BaseModel):
    case_id: int
    events_created: int
    events_removed: int
    documents_scanned: int
    interviews_scanned: int
    duration_ms: int


class InterviewProgressResponse(BaseModel):
    interview_id: int
    mode: str
    processing_state: str
    # For GUIDED_QUESTIONS: reflects real completion logic (not just field existence)
    answered_count: int
    total_count: int
    completion_pct: float
    # For FREEFORM_NARRATIVE: whether narrative has been marked complete
    narrative_started: bool
    narrative_complete: bool
    display: str  # short human-readable status string for the UI


# ============ COA Schemas ============

class COACreate(BaseModel):
    case_id: int
    name: str
    caci_ref: Optional[str] = None
    strength: float = 0.0
    evidence_count: int = 0
    coverage_pct: float = 0.0
    status: str = "pending"


class BurdenElementResponse(BaseModel):
    id: int
    element_id: str
    description: Optional[str]
    strength: float
    supporting_docs: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ResolvedAuthorityBlock(BaseModel):
    """Tri-signal authority block returned by the Brain resolver.

    Downstream surfaces (COA, burden, remedy, complaint, case-to-authority, Library)
    MUST render all three signals and never read provisional records directly.
    """
    certified: Dict[str, Any] = Field(
        default_factory=lambda: {"present": False, "authority_id": None, "record_ref": None}
    )
    provisional_candidate: Dict[str, Any] = Field(
        default_factory=lambda: {
            "caci_id": None,
            "record_id": None,
            "confidence": None,
            "status": None,
        }
    )
    case_decision: Dict[str, Any] = Field(
        default_factory=lambda: {
            "state": "PENDING_REVIEW",
            "decision_id": None,
            "replacement_authority_id": None,
        }
    )
    effective_grounding: str = "PROPOSED"  # GROUNDED | GROUNDED_VIA_REPLACEMENT | PROPOSED | NONE
    display_badge: str = "provisional-candidate"
    decision_id: Optional[str] = None
    pinned_record_id: Optional[str] = None
    requires_attorney_review: bool = True


class COAResponse(BaseModel):
    id: int
    case_id: int
    name: str
    caci_ref: Optional[str]
    strength: float
    evidence_count: int
    coverage_pct: float
    status: str
    created_at: datetime
    authority: Optional[ResolvedAuthorityBlock] = None

    class Config:
        from_attributes = True


class COADetailResponse(COAResponse):
    burden_elements: List[BurdenElementResponse] = []


# ============ Weapon Schemas ============

class WeaponCreate(BaseModel):
    case_id: int
    category: str
    coa_ref: Optional[str] = None
    caci: Optional[str] = None
    element: Optional[str] = None
    strategy: Optional[str] = None
    strategy_type: Optional[str] = None
    question: Optional[str] = None
    strengthens_jeremy: Optional[str] = None
    weakens_david: Optional[str] = None
    perjury_push: Optional[str] = None
    evidence_score: float = 0.0
    perjury_trap: bool = False
    docs_json: Optional[Dict[str, Any]] = None
    opp_prediction: Optional[str] = None
    depo_strategy: Optional[str] = None
    long_game: Optional[str] = None
    responses_json: Optional[Dict[str, Any]] = None
    attorney_question: Optional[str] = None
    attorney_notes: Optional[str] = None
    status: str = "pending"


class WeaponUpdate(BaseModel):
    question: Optional[str] = None
    strengthens_jeremy: Optional[str] = None
    weakens_david: Optional[str] = None
    perjury_push: Optional[str] = None
    attorney_question: Optional[str] = None
    attorney_notes: Optional[str] = None
    status: Optional[str] = None


class WeaponResponse(BaseModel):
    id: int
    case_id: int
    category: str
    coa_ref: Optional[str]
    caci: Optional[str]
    element: Optional[str]
    strategy: Optional[str]
    strategy_type: Optional[str]
    evidence_score: float
    perjury_trap: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class WeaponDetailResponse(WeaponResponse):
    question: Optional[str]
    strengthens_jeremy: Optional[str]
    weakens_david: Optional[str]
    perjury_push: Optional[str]
    docs_json: Optional[Dict[str, Any]]
    opp_prediction: Optional[str]
    depo_strategy: Optional[str]
    long_game: Optional[str]
    responses_json: Optional[Dict[str, Any]]
    attorney_question: Optional[str]
    attorney_notes: Optional[str]


# ============ Strategy Schemas ============

class StrategyCreate(BaseModel):
    case_id: int
    name: str
    emoji: Optional[str] = None
    weapons_json: Optional[Dict[str, Any]] = None
    rationale: Optional[str] = None
    value_score: float = 0.0
    depo_impact: float = 0.0
    trial_impact: float = 0.0
    phases_json: Optional[Dict[str, Any]] = None


class StrategyResponse(BaseModel):
    id: int
    case_id: int
    name: str
    emoji: Optional[str]
    value_score: float
    depo_impact: float
    trial_impact: float
    created_at: datetime

    class Config:
        from_attributes = True


class StrategyDetailResponse(StrategyResponse):
    weapons_json: Optional[Dict[str, Any]]
    rationale: Optional[str]
    phases_json: Optional[Dict[str, Any]]
    weapons: List[WeaponResponse] = []


# ============ Perjury Path Schemas ============

class PerjuryPathCreate(BaseModel):
    case_id: int
    name: str
    desc: Optional[str] = None
    weapons_json: Optional[Dict[str, Any]] = None
    logic: Optional[str] = None
    trap_springs: Optional[str] = None


class PerjuryPathResponse(BaseModel):
    id: int
    case_id: int
    name: str
    desc: Optional[str]
    weapons_json: Optional[Dict[str, Any]]
    logic: Optional[str]
    trap_springs: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Deposition Schemas ============

class DepositionSessionCreate(BaseModel):
    case_id: int
    witness_name: Optional[str] = None


class DepositionSessionResponse(BaseModel):
    id: int
    case_id: int
    witness_name: Optional[str]
    started_at: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DepositionTranscriptUpdate(BaseModel):
    transcript_text: str


# ============ Attorney Edit Schemas ============

class AttorneyEditCreate(BaseModel):
    weapon_id: int
    field_name: str
    original_value: Optional[str] = None
    edited_value: Optional[str] = None


class AttorneyEditResponse(BaseModel):
    id: int
    weapon_id: int
    field_name: str
    original_value: Optional[str]
    edited_value: Optional[str]
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ============ Simulation Schemas ============

class SimulateResponse(BaseModel):
    """Response from opponent simulation"""
    david_says: str
    counter: str
    delta: str
    perjury_evidence: Optional[str] = None


class SimulationRequest(BaseModel):
    weapon_id: int
    scenario: Optional[str] = None


# ============ Case Authority Decision Schemas ============

class ReplacementAuthority(BaseModel):
    authority_type: str  # CACI | STATUTE | CASE_LAW | CERTIFIED_CACI | REGULATION | OTHER
    authority_id: str
    record_ref: Optional[str] = None
    reason: str


class CaseAuthorityDecisionCreate(BaseModel):
    case_id: int
    caci_id: str
    state: str  # PENDING_REVIEW | ACCEPTED | REJECTED | REPLACED
    pinned_record_id: Optional[str] = None
    replacement: Optional[ReplacementAuthority] = None
    decided_by_actor_type: str = "ATTORNEY"
    decided_by_actor_id: str
    decided_by_role: Optional[str] = None
    rationale: Optional[str] = None
    source_event: Optional[str] = None


class CaseAuthorityDecisionResponse(BaseModel):
    id: int
    decision_id: str
    case_id: int
    caci_id: str
    state: str
    pinned_record_id: Optional[str]
    replacement: Optional[Dict[str, Any]] = None
    decided_by_actor_type: str
    decided_by_actor_id: str
    decided_by_role: Optional[str]
    decided_at: datetime
    rationale: Optional[str]
    supersedes_decision_id: Optional[str]
    superseded_by_decision_id: Optional[str]
    audit_hash: str
    source_event: Optional[str]

    class Config:
        from_attributes = True


class ProvisionalCaciSummary(BaseModel):
    """Library display state for provisional CACI candidates."""
    caci_id: str
    record_id: str
    title: str
    status: str  # PROVISIONAL | BLOCKED_UNTRUSTED | SUPERSEDED
    confidence_overall: float
    canonical: bool = False
    replaceable: bool = True


class CaseToAuthorityRow(BaseModel):
    """One row in the case-to-authority mapping view."""
    caci_id: str
    authority: ResolvedAuthorityBlock


class ResolveRequest(BaseModel):
    case_id: int
    caci_id: str


# ============ Case Lifecycle Schemas ============

class SaveDraftRequest(BaseModel):
    name: Optional[str] = None
    court: Optional[str] = None
    plaintiff: Optional[str] = None
    defendant: Optional[str] = None
    actor_id: str = "attorney:unknown"
    actor_type: str = "ATTORNEY"
    return_to_dashboard: bool = False
    reason: Optional[str] = None


class MarkReadyRequest(BaseModel):
    actor_id: str
    actor_type: str = "ATTORNEY"
    reason: Optional[str] = None


class SubmitForAnalysisRequest(BaseModel):
    actor_id: str
    actor_type: str = "ATTORNEY"
    role: Optional[str] = None


class ReturnToIntakeRequest(BaseModel):
    actor_id: str
    actor_type: str = "ATTORNEY"
    reason: str


class AnalysisRunResponse(BaseModel):
    id: int
    run_id: str
    case_id: int
    state: str
    triggered_by_actor_id: str
    triggered_by_actor_type: str
    triggered_at: datetime
    completed_at: Optional[datetime]
    coa_count: int
    review_required_count: int
    recompute_event_ids: Optional[List[int]] = None
    error_detail: Optional[str] = None

    class Config:
        from_attributes = True


class CaseProgressResponse(BaseModel):
    case_id: int
    save_state: str
    last_saved_at: Optional[datetime]
    last_submitted_at: Optional[datetime]
    processing_started_at: Optional[datetime]
    processing_finished_at: Optional[datetime]
    review_required_count: int
    current_analysis_run: Optional[AnalysisRunResponse] = None
    gated_surfaces: List[str] = Field(default_factory=list)
    last_error_detail: Optional[str] = None


class CaseStateEventResponse(BaseModel):
    id: int
    case_id: int
    from_state: Optional[str]
    to_state: str
    actor_id: str
    actor_type: str
    reason: Optional[str]
    at: datetime

    class Config:
        from_attributes = True


class StateGatedErrorResponse(BaseModel):
    detail: str
    save_state: str
    required_states: List[str]
    message: str


# Update forward references
CaseDetailResponse.model_rebuild()
StrategyDetailResponse.model_rebuild()
