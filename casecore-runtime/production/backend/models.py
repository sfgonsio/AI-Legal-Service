"""
SQLAlchemy ORM models for CaseCore
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    court = Column(String(255), nullable=True)
    plaintiff = Column(String(255), nullable=False)
    defendant = Column(String(255), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Case save / analysis lifecycle ---
    # State machine — see contract/v1/programs/program_CASE_SAVE_LIFECYCLE.md
    save_state = Column(String(40), nullable=False, default="DRAFT", index=True)
    last_saved_at = Column(DateTime, nullable=True)
    last_submitted_at = Column(DateTime, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    processing_finished_at = Column(DateTime, nullable=True)
    review_required_count = Column(Integer, nullable=False, default=0)
    current_analysis_run_id = Column(String(64), nullable=True)
    last_error_detail = Column(Text, nullable=True)

    # Relationships
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    coas = relationship("COA", back_populates="case", cascade="all, delete-orphan")
    weapons = relationship("Weapon", back_populates="case", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="case", cascade="all, delete-orphan")
    perjury_paths = relationship("PerjuryPath", back_populates="case", cascade="all, delete-orphan")
    deposition_sessions = relationship("DepositionSession", back_populates="case", cascade="all, delete-orphan")
    authority_decisions = relationship("CaseAuthorityDecision", back_populates="case", cascade="all, delete-orphan")
    recompute_events = relationship("RecomputeEvent", back_populates="case", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="case", cascade="all, delete-orphan")
    state_events = relationship("CaseStateEvent", back_populates="case", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    folder = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    text_content = Column(Text, nullable=True)
    char_count = Column(Integer, default=0)
    byte_size = Column(Integer, default=0)
    # sha256 of bytes; previously unique but re-uploads of identical bytes into
    # different cases are legitimate, so relaxed to non-unique and indexed.
    sha256_hash = Column(String(64), nullable=True, index=True)
    storage_path = Column(String(500), nullable=True)
    archive_id = Column(Integer, ForeignKey("upload_archives.id"), nullable=True, index=True)
    archive_relative_path = Column(String(500), nullable=True)
    # Ingest pipeline state (NOT analysis state)
    ingest_phase = Column(String(40), nullable=False, default="uploaded", index=True)
    ingest_started_at = Column(DateTime, nullable=True)
    ingest_finished_at = Column(DateTime, nullable=True)
    ingest_error_detail = Column(Text, nullable=True)
    # Extraction reliability fields (populated by content_extractors / ingest_pipeline).
    #   extraction_status: TEXT_EXTRACTION_COMPLETE | OCR_REQUIRED | OCR_NOT_AVAILABLE
    #                    | EXTRACTION_FAILED | UNSUPPORTED_TYPE | NOT_ATTEMPTED
    #   extraction_method: plain | email | html-basic | pypdf | python-docx | preseeded | none
    #   extraction_confidence: 0.0 .. 1.0 (0 when unknown / skipped)
    #   is_scanned_pdf: heuristic flag set when PDF yields ~0 text / page
    extraction_status = Column(String(40), nullable=False, default="NOT_ATTEMPTED")
    extraction_method = Column(String(40), nullable=True)
    extraction_confidence = Column(Float, nullable=False, default=0.0)
    is_scanned_pdf = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="documents")
    archive = relationship("UploadArchive", back_populates="documents")
    ingest_events = relationship("IngestEvent", back_populates="document", cascade="all, delete-orphan")
    actor_mentions = relationship("ActorMention", back_populates="document", cascade="all, delete-orphan")


class COA(Base):
    __tablename__ = "coas"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    caci_ref = Column(String(50), nullable=True)
    # Authority grounding (populated by Brain resolver; never read directly from provisional store).
    # Snapshot of the (decision_id, pinned_record_id) used at last resolution.
    authority_decision_id = Column(String(64), nullable=True)
    authority_pinned_record_id = Column(String(64), nullable=True)
    authority_effective_grounding = Column(String(40), nullable=True)
    strength = Column(Float, default=0.0)
    evidence_count = Column(Integer, default=0)
    coverage_pct = Column(Float, default=0.0)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="coas")
    burden_elements = relationship("BurdenElement", back_populates="coa", cascade="all, delete-orphan")


class BurdenElement(Base):
    __tablename__ = "burden_elements"

    id = Column(Integer, primary_key=True, index=True)
    coa_id = Column(Integer, ForeignKey("coas.id"), nullable=False)
    element_id = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    strength = Column(Float, default=0.0)
    supporting_docs = Column(JSON, nullable=True)

    # Relationships
    coa = relationship("COA", back_populates="burden_elements")


class Weapon(Base):
    __tablename__ = "weapons"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    category = Column(String(50), nullable=False)  # DISCOVER, UNCOVER, WEAPONIZE
    coa_ref = Column(String(255), nullable=True)
    caci = Column(String(50), nullable=True)
    element = Column(String(255), nullable=True)
    strategy = Column(String(255), nullable=True)
    strategy_type = Column(String(50), nullable=True)
    question = Column(Text, nullable=True)
    strengthens_jeremy = Column(Text, nullable=True)
    weakens_david = Column(Text, nullable=True)
    perjury_push = Column(Text, nullable=True)
    evidence_score = Column(Float, default=0.0)
    perjury_trap = Column(Boolean, default=False)
    docs_json = Column(JSON, nullable=True)
    opp_prediction = Column(Text, nullable=True)
    depo_strategy = Column(Text, nullable=True)
    long_game = Column(Text, nullable=True)
    responses_json = Column(JSON, nullable=True)
    attorney_question = Column(Text, nullable=True)
    attorney_notes = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="weapons")
    attorney_edits = relationship("AttorneyEdit", back_populates="weapon", cascade="all, delete-orphan")


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    emoji = Column(String(10), nullable=True)
    weapons_json = Column(JSON, nullable=True)
    rationale = Column(Text, nullable=True)
    value_score = Column(Float, default=0.0)
    depo_impact = Column(Float, default=0.0)
    trial_impact = Column(Float, default=0.0)
    phases_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="strategies")


class PerjuryPath(Base):
    __tablename__ = "perjury_paths"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    desc = Column(Text, nullable=True)
    weapons_json = Column(JSON, nullable=True)
    logic = Column(Text, nullable=True)
    trap_springs = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="perjury_paths")


class AttorneyEdit(Base):
    __tablename__ = "attorney_edits"

    id = Column(Integer, primary_key=True, index=True)
    weapon_id = Column(Integer, ForeignKey("weapons.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    original_value = Column(Text, nullable=True)
    edited_value = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    weapon = relationship("Weapon", back_populates="attorney_edits")


class DepositionSession(Base):
    __tablename__ = "deposition_sessions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    witness_name = Column(String(255), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="active")
    transcript_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="deposition_sessions")


# ============ Case-Scoped Authority Governance ============

class CaseAuthorityDecision(Base):
    """
    Append-only per-case, per-CACI attorney decision.
    Reversals/revisions are NEW rows with supersedes_decision_id set.
    See contract/v1/programs/program_CASE_AUTHORITY_DECISION.md
    """
    __tablename__ = "case_authority_decisions"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String(64), nullable=False, unique=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    caci_id = Column(String(50), nullable=False, index=True)
    state = Column(String(32), nullable=False)  # PENDING_REVIEW | ACCEPTED | REJECTED | REPLACED
    pinned_record_id = Column(String(64), nullable=True)
    replacement_json = Column(JSON, nullable=True)  # {authority_type, authority_id, record_ref, reason}
    decided_by_actor_type = Column(String(32), nullable=False, default="SYSTEM")
    decided_by_actor_id = Column(String(128), nullable=False, default="system")
    decided_by_role = Column(String(64), nullable=True)
    decided_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    rationale = Column(Text, nullable=True)
    supersedes_decision_id = Column(String(64), nullable=True, index=True)
    superseded_by_decision_id = Column(String(64), nullable=True, index=True)
    audit_hash = Column(String(128), nullable=False, default="")
    source_event = Column(String(255), nullable=True)

    case = relationship("Case", back_populates="authority_decisions")


class RecomputeEvent(Base):
    """
    Audit trail for downstream recompute triggered by case authority decision changes.
    """
    __tablename__ = "recompute_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    triggered_by_decision_id = Column(String(64), nullable=True, index=True)
    caci_id = Column(String(50), nullable=True)
    scope_json = Column(JSON, nullable=True)  # which downstream surfaces recomputed
    status = Column(String(32), nullable=False, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="recompute_events")


class AnalysisRun(Base):
    """
    Append-only record of each Submit for Legal Analysis invocation.
    See contract/v1/programs/program_ANALYSIS_TRIGGER.md.
    """
    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), nullable=False, unique=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    state = Column(String(32), nullable=False, default="PENDING")  # PENDING|RUNNING|COMPLETED|FAILED
    triggered_by_actor_id = Column(String(128), nullable=False)
    triggered_by_actor_type = Column(String(32), nullable=False, default="ATTORNEY")
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    coa_count = Column(Integer, nullable=False, default=0)
    review_required_count = Column(Integer, nullable=False, default=0)
    recompute_event_ids = Column(JSON, nullable=True)
    error_detail = Column(Text, nullable=True)
    # Full analysis blob: {coas, burdens, remedies, complaint, evidence_map,
    # stats, provenance}. Authority references are grounded in the Legal
    # Library corpus (body_status=IMPORTED) — no hallucinated citations.
    result_json = Column(JSON, nullable=True)

    case = relationship("Case", back_populates="analysis_runs")


class UploadArchive(Base):
    """
    A .zip archive uploaded to a case. Server extracts entries server-side into
    Document rows that reference this archive via Document.archive_id.
    """
    __tablename__ = "upload_archives"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    sha256_hash = Column(String(64), nullable=True, index=True)
    byte_size = Column(Integer, default=0)
    entry_count = Column(Integer, default=0)
    storage_path = Column(String(500), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by_actor_id = Column(String(128), nullable=True)

    documents = relationship("Document", back_populates="archive")


class IngestEvent(Base):
    """
    Append-only phase-transition audit for a document's ingest pipeline.
    """
    __tablename__ = "ingest_events"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    case_id = Column(Integer, nullable=False, index=True)
    from_phase = Column(String(40), nullable=True)
    to_phase = Column(String(40), nullable=False)
    error_detail = Column(Text, nullable=True)
    at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="ingest_events")


class Actor(Base):
    """
    A person or organization surfaced from case evidence.
    Seeded from Case fields on first save, and extended by rule-based
    extraction during ingest and interview processing.
    Not an analytical artifact.
    """
    __tablename__ = "actors"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(32), nullable=False, default="PERSON")  # PERSON|ORGANIZATION|UNKNOWN
    resolution_state = Column(String(32), nullable=False, default="CANDIDATE")  # RESOLVED|CANDIDATE|AMBIGUOUS
    role_hint = Column(String(64), nullable=True)  # plaintiff|defendant|court|witness|attorney|unknown
    mention_count = Column(Integer, default=0)
    first_seen_document_id = Column(Integer, nullable=True)
    last_seen_document_id = Column(Integer, nullable=True)
    # Provenance of first creation: SEED | INGEST | INTERVIEW | MANUAL
    source = Column(String(32), nullable=False, default="MANUAL")
    source_interview_id = Column(Integer, nullable=True, index=True)
    merged_into_actor_id = Column(Integer, ForeignKey("actors.id"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    mentions = relationship("ActorMention", back_populates="actor", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("case_id", "canonical_name", name="uq_actor_case_canonical"),
    )


class ActorMention(Base):
    """
    A single occurrence of an actor in a document OR an interview.
    Enables attorney drill-down and disambiguation.

    Exactly one of (document_id, interview_id) is set per mention.
    """
    __tablename__ = "actor_mentions"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("actors.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=True, index=True)
    source_kind = Column(String(32), nullable=False, default="DOCUMENT")  # DOCUMENT | INTERVIEW
    snippet = Column(Text, nullable=True)
    offset_start = Column(Integer, nullable=True)
    offset_end = Column(Integer, nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    actor = relationship("Actor", back_populates="mentions")
    document = relationship("Document", back_populates="actor_mentions")


class Interview(Base):
    """
    Per-case intake interview. Two modes:
      GUIDED_QUESTIONS: answers stored as InterviewQuestion rows
      FREEFORM_NARRATIVE: narrative_text holds a single block
    User explicitly marks complete, which triggers actor extraction (NOT analysis).
    """
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    mode = Column(String(32), nullable=False, default="GUIDED_QUESTIONS")  # GUIDED_QUESTIONS | FREEFORM_NARRATIVE
    narrative_text = Column(Text, nullable=True)  # freeform mode
    processing_state = Column(String(32), nullable=False, default="draft")  # draft | saved | processing | actors_identified | complete | failed
    last_error_detail = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    """
    One guided-mode question + answer. Order preserved via `order_index`.
    completion_kind encodes how we decide a question is answered:
      TEXT: any non-empty trimmed answer of >= MIN length
      DATE: any non-empty answer
      YESNO: answered == True
      LONG_TEXT: answer_text length >= configured min
    """
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False, index=True)
    question_key = Column(String(64), nullable=False)
    prompt = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    completion_kind = Column(String(32), nullable=False, default="TEXT")  # TEXT|LONG_TEXT|DATE|YESNO
    answer_text = Column(Text, nullable=True)
    answered = Column(Boolean, default=False)
    answered_at = Column(DateTime, nullable=True)

    interview = relationship("Interview", back_populates="questions")


class TimelineEvent(Base):
    """
    A single event extracted from case evidence (interview narrative, interview
    Q&A, or a document's normalized text). Built OUTSIDE the ingest pipeline
    via brain.timeline_builder — triggered on demand by
    POST /timeline/{case_id}/build.

    Never drives legal analysis. Actor links are by id (no cross-case leaks).

    Legal-layer extension (rule-based, pre-analysis):
      - claim_relation: SUPPORTS | WEAKENS | CONTRADICTS | NEUTRAL (heuristic)
      - strategy flags: deposition / interrogatory / document-request targets
      - legal_mappings relationship -> TimelineEventLegalMapping rows
    These are hints for attorneys, NOT grounded legal conclusions. Grounding
    remains behind Submit for Legal Analysis (SR-11 / SR-12).
    """
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), nullable=False, unique=True, index=True)  # uuid
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)

    # Normalized timestamp: first day-of occurrence, UTC midnight. NULL when unknown.
    timestamp = Column(DateTime, nullable=True, index=True)
    raw_date_text = Column(String(255), nullable=True)
    date_precision = Column(String(16), nullable=False, default="UNKNOWN")
    # DAY | MONTH | YEAR | UNKNOWN

    summary = Column(Text, nullable=False)
    event_type = Column(String(32), nullable=False, default="OTHER")
    # COMMUNICATION | MEETING | PAYMENT | FILING | NOTICE | AGREEMENT | BREACH | TRANSACTION | OTHER

    source = Column(String(16), nullable=False)  # INTERVIEW | INGEST
    source_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    source_interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=True, index=True)
    text_offset_start = Column(Integer, nullable=True)
    text_offset_end = Column(Integer, nullable=True)
    snippet = Column(Text, nullable=True)

    # JSON list of actor_ids referenced by this event.
    actor_ids = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)

    # --- Legal layer (heuristic, pre-analysis, not grounded) ---
    claim_relation = Column(String(16), nullable=False, default="NEUTRAL")
    # SUPPORTS | WEAKENS | CONTRADICTS | NEUTRAL
    deposition_target = Column(Boolean, nullable=False, default=False)
    interrogatory_target = Column(Boolean, nullable=False, default=False)
    document_request_target = Column(Boolean, nullable=False, default=False)
    strategy_rationale = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    legal_mappings = relationship(
        "TimelineEventLegalMapping",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class TimelineEventLegalMapping(Base):
    """
    Heuristic mapping of a TimelineEvent onto potential legal elements. These
    are CANDIDATE mappings (pre-analysis), analogous to CANDIDATE actors. The
    authoritative grounded-authority view still comes from the Brain resolver
    during Submit for Legal Analysis.

    element_reference uses Legal Library record ids where possible
    (e.g. "CACI_303", "CACI_1900", "EVID_1220"), or a plain-text label when
    no structured reference exists.
    """
    __tablename__ = "timeline_event_legal_mappings"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("timeline_events.id"), nullable=False, index=True)
    legal_element_type = Column(String(40), nullable=False)
    # COA_ELEMENT | BURDEN_OF_PRODUCTION | BURDEN_OF_PERSUASION
    # | REMEDY | EVIDENCE_ADMISSIBILITY | PROCEDURAL
    element_reference = Column(String(80), nullable=True)
    element_label = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    rationale = Column(Text, nullable=True)
    supporting_evidence_refs = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("TimelineEvent", back_populates="legal_mappings")


class CaseStateEvent(Base):
    """
    Append-only audit of every case save_state transition.
    """
    __tablename__ = "case_state_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    from_state = Column(String(40), nullable=True)
    to_state = Column(String(40), nullable=False)
    actor_id = Column(String(128), nullable=False, default="system")
    actor_type = Column(String(32), nullable=False, default="SYSTEM")
    reason = Column(Text, nullable=True)
    at = Column(DateTime, nullable=False, default=datetime.utcnow)

    case = relationship("Case", back_populates="state_events")
