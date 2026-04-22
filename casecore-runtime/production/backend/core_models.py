"""
Hardened-core truth-layer models for CaseCore (Wave 1 + Wave 2).

Source specs:
  contract/v1/data/CORE_DATA_IMPLEMENTATION_PLAN.md
  contract/v1/data/CORE_DATA_WAVE_TICKETS.md
  contract/v1/brain/MESSAGE_NORMALIZATION_SPEC.md

Design authority: PostgreSQL. Implementation portable to SQLite (current runtime).
Conventions:
  - UUIDs stored as String(36) for dialect portability.
  - Python-side timestamp defaults (matches existing models.py pattern).
  - JSON columns use SQLAlchemy's generic JSON (TEXT in SQLite, JSON in PG).
  - Never shares tablenames with legacy models.py.
    New case table is core_cases; existing cases is the legacy War Room table.

Stratum placement: ALL tables in this module are TRUTH / CANONICAL stratum.
Derived-reasoning artifacts belong in Wave 3+ and are not in this module.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)

from database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Wave 1 — Case + Intake Foundation
# ---------------------------------------------------------------------------


class CoreCase(Base):
    """Hardened truth-layer case record. Separate from legacy models.Case."""

    __tablename__ = "core_cases"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    display_name = Column(String(255), nullable=False)
    stratum = Column(String(20), nullable=False, default="truth")
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CaseStageState(Base):
    """Per-case stage state. Independent of any UI route layout."""

    __tablename__ = "case_stage_state"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_key = Column(String(100), nullable=False)
    state_value = Column(String(100), nullable=False)
    state_details = Column(JSON, nullable=True)
    entered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("core_case_id", "stage_key", name="uq_case_stage_state_key"),
    )


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interview_mode = Column(String(30), nullable=False)
    interviewer_user_id = Column(String(255), nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="in_progress")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class InterviewResponse(Base):
    __tablename__ = "interview_responses"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    interview_session_id = Column(
        String(36),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_key = Column(String(255), nullable=False)
    response_text = Column(Text, nullable=True)
    response_payload = Column(JSON, nullable=True)
    answered_by = Column(String(255), nullable=True)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_interview_responses_session_question", "interview_session_id", "question_key"),
    )


class InterviewRecording(Base):
    """Immutable after save. No updated_at."""

    __tablename__ = "interview_recordings"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    interview_session_id = Column(
        String(36),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_uri = Column(String(1024), nullable=False)
    storage_backend = Column(String(50), nullable=False)
    file_hash = Column(String(128), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    recorded_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class InterviewTranscriptSegment(Base):
    """Transcript edits are new rows (supersession). Raw audio stays untouched."""

    __tablename__ = "interview_transcript_segments"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    interview_recording_id = Column(
        String(36),
        ForeignKey("interview_recordings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interview_session_id = Column(
        String(36),
        ForeignKey("interview_sessions.id"),
        nullable=False,
        index=True,
    )
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_index = Column(Integer, nullable=False)
    start_ms = Column(Integer, nullable=True)
    end_ms = Column(Integer, nullable=True)
    text_content = Column(Text, nullable=False)
    speaker_label = Column(String(255), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    supersedes_segment_id = Column(
        String(36), ForeignKey("interview_transcript_segments.id"), nullable=True
    )
    is_current = Column(Boolean, nullable=False, default=True, index=True)
    edited_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class UploadedFile(Base):
    """Original reference is immutable; revisions go in uploaded_file_versions."""

    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name = Column(String(1024), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    sha256_hash = Column(String(64), nullable=False, index=True)
    source_type = Column(String(100), nullable=False)
    source_reference = Column(String(1024), nullable=True)
    storage_uri = Column(String(1024), nullable=False)
    storage_backend = Column(String(50), nullable=False)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    uploaded_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class UploadedFileVersion(Base):
    __tablename__ = "uploaded_file_versions"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    uploaded_file_id = Column(
        String(36),
        ForeignKey("uploaded_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    storage_uri = Column(String(1024), nullable=False)
    storage_backend = Column(String(50), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    change_note = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "uploaded_file_id", "version_number", name="uq_uploaded_file_version"
        ),
    )


class IntakeActorRecord(Base):
    """Actor as captured at intake. No forced deduplication at this layer."""

    __tablename__ = "intake_actor_records"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_type = Column(String(30), nullable=False)  # person | entity | unknown
    display_name = Column(String(512), nullable=False)
    role_context = Column(String(512), nullable=True)
    raw_input_text = Column(Text, nullable=True)
    source_reference = Column(String(1024), nullable=True)
    confidence = Column(Float, nullable=True)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class IntakeActorRelationshipInput(Base):
    __tablename__ = "intake_actor_relationship_inputs"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_a_id = Column(
        String(36), ForeignKey("intake_actor_records.id"), nullable=False, index=True
    )
    actor_b_id = Column(
        String(36), ForeignKey("intake_actor_records.id"), nullable=True, index=True
    )
    relationship_claim = Column(String(512), nullable=False)
    direction = Column(String(20), nullable=True)  # a_to_b | b_to_a | bidirectional
    source_reference = Column(String(1024), nullable=True)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntakeSummaryClient(Base):
    """Versioned by new row. Client-facing summary."""

    __tablename__ = "intake_summaries_client"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    summary_text = Column(Text, nullable=False)
    summary_payload = Column(JSON, nullable=True)
    version_number = Column(Integer, nullable=False, default=1)
    supersedes_summary_id = Column(
        String(36), ForeignKey("intake_summaries_client.id"), nullable=True
    )
    is_current = Column(Boolean, nullable=False, default=True, index=True)
    created_by = Column(String(255), nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntakeSummaryAttorney(Base):
    """Versioned by new row. Attorney legal-framing summary."""

    __tablename__ = "intake_summaries_attorney"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    summary_text = Column(Text, nullable=False)
    summary_payload = Column(JSON, nullable=True)
    version_number = Column(Integer, nullable=False, default=1)
    supersedes_summary_id = Column(
        String(36), ForeignKey("intake_summaries_attorney.id"), nullable=True
    )
    is_current = Column(Boolean, nullable=False, default=True, index=True)
    created_by = Column(String(255), nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class IntakeTimelineSeed(Base):
    """Raw event-like fragments. Link to source response/file/actor where possible."""

    __tablename__ = "intake_timeline_seeds"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seed_text = Column(Text, nullable=False)
    event_time_candidate = Column(String(255), nullable=True)
    event_time_iso = Column(DateTime, nullable=True)
    time_precision = Column(String(30), nullable=True)  # exact | approximate | unknown
    source_response_id = Column(
        String(36), ForeignKey("interview_responses.id"), nullable=True
    )
    source_file_id = Column(String(36), ForeignKey("uploaded_files.id"), nullable=True)
    related_actor_id = Column(
        String(36), ForeignKey("intake_actor_records.id"), nullable=True
    )
    uncertainty_notes = Column(Text, nullable=True)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Wave 2 — Message Normalization Persistence
# ---------------------------------------------------------------------------


class MessageSourceFile(Base):
    __tablename__ = "message_source_files"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_file_id = Column(
        String(36), ForeignKey("uploaded_files.id"), nullable=True, index=True
    )
    file_hash = Column(String(64), nullable=False, index=True)
    file_type = Column(String(100), nullable=False)  # email | sms | chat | ...
    source_system = Column(String(100), nullable=True)
    parse_status = Column(String(50), nullable=False, default="pending")
    parse_notes = Column(Text, nullable=True)
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MessageThread(Base):
    __tablename__ = "message_threads"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_thread_id = Column(String(512), nullable=True)
    thread_subject = Column(String(1024), nullable=True)
    participants = Column(JSON, nullable=True)
    first_message_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    message_count = Column(Integer, nullable=False, default=0)
    is_broken = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class NormalizedMessage(Base):
    """Immutable after save per §10."""

    __tablename__ = "normalized_messages"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_source_file_id = Column(
        String(36),
        ForeignKey("message_source_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    thread_id = Column(
        String(36), ForeignKey("message_threads.id"), nullable=True, index=True
    )
    external_message_id = Column(String(512), nullable=True)
    sender_candidate = Column(String(512), nullable=True)
    sender_confidence = Column(Float, nullable=True)
    recipient_candidates = Column(JSON, nullable=True)
    body_clean = Column(Text, nullable=False)
    body_raw_reference = Column(Text, nullable=True)
    sent_timestamp = Column(DateTime, nullable=True)
    ambiguity_flags = Column(JSON, nullable=True)
    normalized_by = Column(String(255), nullable=True)
    normalization_version = Column(String(50), nullable=False, default="v1")
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class NormalizedStatement(Base):
    """Immutable after save."""

    __tablename__ = "normalized_statements"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_message_id = Column(
        String(36),
        ForeignKey("normalized_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement_index = Column(Integer, nullable=False)
    statement_text = Column(Text, nullable=False)
    speaker_candidate = Column(String(512), nullable=True)
    speaker_confidence = Column(Float, nullable=True)
    has_pronoun_flag = Column(Boolean, nullable=False, default=False)
    pronoun_resolved = Column(Boolean, nullable=False, default=False)
    pronoun_confidence = Column(Float, nullable=True)
    signal_flags = Column(JSON, nullable=True)
    attribution_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "normalized_message_id",
            "statement_index",
            name="uq_normalized_statement_index",
        ),
    )


class QuotedBlock(Base):
    __tablename__ = "quoted_blocks"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_message_id = Column(
        String(36),
        ForeignKey("normalized_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_block_id = Column(
        String(36), ForeignKey("quoted_blocks.id"), nullable=True
    )
    depth = Column(Integer, nullable=False, default=1)
    quoted_speaker = Column(String(512), nullable=True)
    quoted_speaker_confidence = Column(Float, nullable=True)
    quoted_text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ForwardedBlock(Base):
    __tablename__ = "forwarded_blocks"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_message_id = Column(
        String(36),
        ForeignKey("normalized_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chain_index = Column(Integer, nullable=False)
    original_sender = Column(String(512), nullable=True)
    original_recipients = Column(JSON, nullable=True)
    forwarded_at = Column(DateTime, nullable=True)
    forwarded_body = Column(Text, nullable=False)
    speaker_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ReferencedActorCandidate(Base):
    __tablename__ = "referenced_actor_candidates"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_message_id = Column(
        String(36),
        ForeignKey("normalized_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_statement_id = Column(
        String(36), ForeignKey("normalized_statements.id"), nullable=True
    )
    reference_text = Column(Text, nullable=False)
    reference_kind = Column(String(50), nullable=True)  # pronoun | role | nickname | proper_name
    resolution_status = Column(String(50), nullable=False, default="unresolved")
    candidate_actor_ids = Column(JSON, nullable=True)
    chosen_actor_id = Column(
        String(36), ForeignKey("intake_actor_records.id"), nullable=True
    )
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MessageCorpus(Base):
    """Corpus-wide state for a single case (one row per case)."""

    __tablename__ = "message_corpus"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    source_file_count = Column(Integer, nullable=False, default=0)
    thread_count = Column(Integer, nullable=False, default=0)
    message_count = Column(Integer, nullable=False, default=0)
    participant_snapshot = Column(JSON, nullable=True)
    conflict_markers = Column(JSON, nullable=True)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class NormalizationQualityFlag(Base):
    __tablename__ = "normalization_quality_flags"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    normalized_message_id = Column(
        String(36),
        ForeignKey("normalized_messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    normalized_statement_id = Column(
        String(36),
        ForeignKey("normalized_statements.id", ondelete="CASCADE"),
        nullable=True,
    )
    flag_code = Column(String(100), nullable=False)
    # valid flag_code values (enforced at service layer, not DB, to stay portable):
    #   ambiguous_sender | ambiguous_recipient | unresolved_third_person |
    #   broken_thread | insufficient_message_structure
    severity = Column(String(30), nullable=False, default="warning")  # info | warning | critical
    detail_text = Column(Text, nullable=True)
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class NormalizationFailureEvent(Base):
    __tablename__ = "normalization_failure_events"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    core_case_id = Column(
        String(36),
        ForeignKey("core_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_source_file_id = Column(
        String(36),
        ForeignKey("message_source_files.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    normalized_message_id = Column(
        String(36), ForeignKey("normalized_messages.id"), nullable=True
    )
    failure_stage = Column(String(100), nullable=False)
    failure_code = Column(String(100), nullable=False)
    severity = Column(String(30), nullable=False, default="critical")
    error_detail = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Explicit export list so `from core_models import *` is predictable.
__all__ = [
    # Wave 1
    "CoreCase",
    "CaseStageState",
    "InterviewSession",
    "InterviewResponse",
    "InterviewRecording",
    "InterviewTranscriptSegment",
    "UploadedFile",
    "UploadedFileVersion",
    "IntakeActorRecord",
    "IntakeActorRelationshipInput",
    "IntakeSummaryClient",
    "IntakeSummaryAttorney",
    "IntakeTimelineSeed",
    # Wave 2
    "MessageSourceFile",
    "MessageThread",
    "NormalizedMessage",
    "NormalizedStatement",
    "QuotedBlock",
    "ForwardedBlock",
    "ReferencedActorCandidate",
    "MessageCorpus",
    "NormalizationQualityFlag",
    "NormalizationFailureEvent",
]
