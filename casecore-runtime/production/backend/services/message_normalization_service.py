"""Wave 2 persistence service — message normalization.

Owns writes and reads for:
  message_source_files, message_threads,
  normalized_messages, normalized_statements,
  quoted_blocks, forwarded_blocks,
  referenced_actor_candidates,
  message_corpus,
  normalization_quality_flags,
  normalization_failure_events.

Design notes:
  - normalized_messages and normalized_statements are IMMUTABLE after save
    per CORE_DATA_IMPLEMENTATION_PLAN §10. This service does not expose
    update methods for them.
  - message_corpus is one-row-per-case. `upsert_corpus_snapshot` updates in
    place; it represents aggregate counts, not historical state.
  - flag_code must be one of the canonical normalization quality codes:
      ambiguous_sender | ambiguous_recipient | unresolved_third_person |
      broken_thread | insufficient_message_structure
    The value is asserted at call time to keep the DB column dialect-portable.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_models import (
    ForwardedBlock,
    MessageCorpus,
    MessageSourceFile,
    MessageThread,
    NormalizationFailureEvent,
    NormalizationQualityFlag,
    NormalizedMessage,
    NormalizedStatement,
    QuotedBlock,
    ReferencedActorCandidate,
)

CANONICAL_FLAG_CODES = frozenset(
    {
        "ambiguous_sender",
        "ambiguous_recipient",
        "unresolved_third_person",
        "broken_thread",
        "insufficient_message_structure",
    }
)


class MessageNormalizationService:
    """Wave 2 persistence service."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- source files --------------------------------------------------------

    async def register_source_file(
        self,
        core_case_id: str,
        file_hash: str,
        file_type: str,
        source_system: Optional[str] = None,
        uploaded_file_id: Optional[str] = None,
        parse_status: str = "pending",
        parse_notes: Optional[str] = None,
    ) -> MessageSourceFile:
        row = MessageSourceFile(
            core_case_id=core_case_id,
            uploaded_file_id=uploaded_file_id,
            file_hash=file_hash,
            file_type=file_type,
            source_system=source_system,
            parse_status=parse_status,
            parse_notes=parse_notes,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def set_source_file_parse_status(
        self, source_file_id: str, parse_status: str, parse_notes: Optional[str] = None
    ) -> None:
        row = await self.session.get(MessageSourceFile, source_file_id)
        if row is None:
            raise ValueError(f"unknown message_source_file id: {source_file_id}")
        row.parse_status = parse_status
        row.parse_notes = parse_notes
        row.updated_at = datetime.utcnow()
        await self.session.flush()

    # -- threads -------------------------------------------------------------

    async def create_thread(
        self,
        core_case_id: str,
        external_thread_id: Optional[str] = None,
        thread_subject: Optional[str] = None,
        participants: Optional[list] = None,
    ) -> MessageThread:
        row = MessageThread(
            core_case_id=core_case_id,
            external_thread_id=external_thread_id,
            thread_subject=thread_subject,
            participants=participants,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def mark_thread_broken(self, thread_id: str, broken: bool = True) -> None:
        row = await self.session.get(MessageThread, thread_id)
        if row is None:
            raise ValueError(f"unknown thread id: {thread_id}")
        row.is_broken = broken
        row.updated_at = datetime.utcnow()
        await self.session.flush()

    async def list_threads(self, core_case_id: str) -> list[MessageThread]:
        result = await self.session.execute(
            select(MessageThread).where(MessageThread.core_case_id == core_case_id)
        )
        return list(result.scalars().all())

    # -- normalized messages / statements (immutable) ------------------------

    async def save_normalized_message(
        self,
        core_case_id: str,
        message_source_file_id: str,
        body_clean: str,
        thread_id: Optional[str] = None,
        external_message_id: Optional[str] = None,
        sender_candidate: Optional[str] = None,
        sender_confidence: Optional[float] = None,
        recipient_candidates: Optional[list] = None,
        body_raw_reference: Optional[str] = None,
        sent_timestamp: Optional[datetime] = None,
        ambiguity_flags: Optional[list] = None,
        normalized_by: Optional[str] = None,
        normalization_version: str = "v1",
    ) -> NormalizedMessage:
        row = NormalizedMessage(
            core_case_id=core_case_id,
            message_source_file_id=message_source_file_id,
            thread_id=thread_id,
            external_message_id=external_message_id,
            sender_candidate=sender_candidate,
            sender_confidence=sender_confidence,
            recipient_candidates=recipient_candidates,
            body_clean=body_clean,
            body_raw_reference=body_raw_reference,
            sent_timestamp=sent_timestamp,
            ambiguity_flags=ambiguity_flags,
            normalized_by=normalized_by,
            normalization_version=normalization_version,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def save_statement(
        self,
        core_case_id: str,
        normalized_message_id: str,
        statement_index: int,
        statement_text: str,
        speaker_candidate: Optional[str] = None,
        speaker_confidence: Optional[float] = None,
        has_pronoun_flag: bool = False,
        pronoun_resolved: bool = False,
        pronoun_confidence: Optional[float] = None,
        signal_flags: Optional[list] = None,
        attribution_confidence: Optional[float] = None,
    ) -> NormalizedStatement:
        row = NormalizedStatement(
            core_case_id=core_case_id,
            normalized_message_id=normalized_message_id,
            statement_index=statement_index,
            statement_text=statement_text,
            speaker_candidate=speaker_candidate,
            speaker_confidence=speaker_confidence,
            has_pronoun_flag=has_pronoun_flag,
            pronoun_resolved=pronoun_resolved,
            pronoun_confidence=pronoun_confidence,
            signal_flags=signal_flags,
            attribution_confidence=attribution_confidence,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_messages_for_thread(self, thread_id: str) -> list[NormalizedMessage]:
        result = await self.session.execute(
            select(NormalizedMessage).where(NormalizedMessage.thread_id == thread_id)
        )
        return list(result.scalars().all())

    async def list_statements_for_message(
        self, normalized_message_id: str
    ) -> list[NormalizedStatement]:
        result = await self.session.execute(
            select(NormalizedStatement)
            .where(NormalizedStatement.normalized_message_id == normalized_message_id)
            .order_by(NormalizedStatement.statement_index)
        )
        return list(result.scalars().all())

    # -- quoted / forwarded blocks ------------------------------------------

    async def save_quoted_block(
        self,
        core_case_id: str,
        normalized_message_id: str,
        quoted_text: str,
        quoted_speaker: Optional[str] = None,
        quoted_speaker_confidence: Optional[float] = None,
        parent_block_id: Optional[str] = None,
        depth: int = 1,
    ) -> QuotedBlock:
        row = QuotedBlock(
            core_case_id=core_case_id,
            normalized_message_id=normalized_message_id,
            parent_block_id=parent_block_id,
            depth=depth,
            quoted_speaker=quoted_speaker,
            quoted_speaker_confidence=quoted_speaker_confidence,
            quoted_text=quoted_text,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def save_forwarded_block(
        self,
        core_case_id: str,
        normalized_message_id: str,
        chain_index: int,
        forwarded_body: str,
        original_sender: Optional[str] = None,
        original_recipients: Optional[list] = None,
        forwarded_at: Optional[datetime] = None,
        speaker_confidence: Optional[float] = None,
    ) -> ForwardedBlock:
        row = ForwardedBlock(
            core_case_id=core_case_id,
            normalized_message_id=normalized_message_id,
            chain_index=chain_index,
            original_sender=original_sender,
            original_recipients=original_recipients,
            forwarded_at=forwarded_at,
            forwarded_body=forwarded_body,
            speaker_confidence=speaker_confidence,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    # -- referenced actor candidates ----------------------------------------

    async def save_referenced_actor_candidate(
        self,
        core_case_id: str,
        normalized_message_id: str,
        reference_text: str,
        reference_kind: Optional[str] = None,
        normalized_statement_id: Optional[str] = None,
        resolution_status: str = "unresolved",
        candidate_actor_ids: Optional[list] = None,
        chosen_actor_id: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> ReferencedActorCandidate:
        row = ReferencedActorCandidate(
            core_case_id=core_case_id,
            normalized_message_id=normalized_message_id,
            normalized_statement_id=normalized_statement_id,
            reference_text=reference_text,
            reference_kind=reference_kind,
            resolution_status=resolution_status,
            candidate_actor_ids=candidate_actor_ids,
            chosen_actor_id=chosen_actor_id,
            confidence=confidence,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def resolve_referenced_actor(
        self, referenced_actor_id: str, chosen_actor_id: str, confidence: Optional[float] = None
    ) -> ReferencedActorCandidate:
        row = await self.session.get(ReferencedActorCandidate, referenced_actor_id)
        if row is None:
            raise ValueError(f"unknown referenced_actor_candidate id: {referenced_actor_id}")
        row.chosen_actor_id = chosen_actor_id
        row.resolution_status = "resolved"
        row.confidence = confidence
        row.updated_at = datetime.utcnow()
        await self.session.flush()
        return row

    # -- corpus snapshot ----------------------------------------------------

    async def upsert_corpus_snapshot(
        self,
        core_case_id: str,
        source_file_count: int,
        thread_count: int,
        message_count: int,
        participant_snapshot: Optional[list] = None,
        conflict_markers: Optional[list] = None,
    ) -> MessageCorpus:
        result = await self.session.execute(
            select(MessageCorpus).where(MessageCorpus.core_case_id == core_case_id)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.source_file_count = source_file_count
            existing.thread_count = thread_count
            existing.message_count = message_count
            existing.participant_snapshot = participant_snapshot
            existing.conflict_markers = conflict_markers
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        row = MessageCorpus(
            core_case_id=core_case_id,
            source_file_count=source_file_count,
            thread_count=thread_count,
            message_count=message_count,
            participant_snapshot=participant_snapshot,
            conflict_markers=conflict_markers,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_corpus_snapshot(self, core_case_id: str) -> Optional[MessageCorpus]:
        result = await self.session.execute(
            select(MessageCorpus).where(MessageCorpus.core_case_id == core_case_id)
        )
        return result.scalar_one_or_none()

    # -- quality flags + failure events -------------------------------------

    async def raise_quality_flag(
        self,
        core_case_id: str,
        flag_code: str,
        severity: str = "warning",
        normalized_message_id: Optional[str] = None,
        normalized_statement_id: Optional[str] = None,
        detail_text: Optional[str] = None,
    ) -> NormalizationQualityFlag:
        if flag_code not in CANONICAL_FLAG_CODES:
            raise ValueError(
                f"flag_code {flag_code!r} is not one of the canonical codes: "
                f"{sorted(CANONICAL_FLAG_CODES)}"
            )
        row = NormalizationQualityFlag(
            core_case_id=core_case_id,
            normalized_message_id=normalized_message_id,
            normalized_statement_id=normalized_statement_id,
            flag_code=flag_code,
            severity=severity,
            detail_text=detail_text,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def resolve_quality_flag(
        self, flag_id: str, resolved_by: Optional[str] = None
    ) -> None:
        row = await self.session.get(NormalizationQualityFlag, flag_id)
        if row is None:
            raise ValueError(f"unknown quality flag id: {flag_id}")
        row.resolved = True
        row.resolved_at = datetime.utcnow()
        row.resolved_by = resolved_by
        await self.session.flush()

    async def list_unresolved_quality_flags(
        self, core_case_id: str
    ) -> list[NormalizationQualityFlag]:
        result = await self.session.execute(
            select(NormalizationQualityFlag).where(
                NormalizationQualityFlag.core_case_id == core_case_id,
                NormalizationQualityFlag.resolved.is_(False),
            )
        )
        return list(result.scalars().all())

    async def record_failure_event(
        self,
        core_case_id: str,
        failure_stage: str,
        failure_code: str,
        severity: str = "critical",
        message_source_file_id: Optional[str] = None,
        normalized_message_id: Optional[str] = None,
        error_detail: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> NormalizationFailureEvent:
        row = NormalizationFailureEvent(
            core_case_id=core_case_id,
            message_source_file_id=message_source_file_id,
            normalized_message_id=normalized_message_id,
            failure_stage=failure_stage,
            failure_code=failure_code,
            severity=severity,
            error_detail=error_detail,
            stack_trace=stack_trace,
        )
        self.session.add(row)
        await self.session.flush()
        return row
