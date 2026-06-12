"""Wave 1 persistence service — case creation and intake.

Owns writes and reads for:
  core_cases, case_stage_state,
  interview_sessions, interview_responses,
  interview_recordings, interview_transcript_segments,
  uploaded_files, uploaded_file_versions,
  intake_actor_records, intake_actor_relationship_inputs,
  intake_summaries_client, intake_summaries_attorney,
  intake_timeline_seeds.

Design notes:
  - No transaction management here. Callers open/commit sessions.
  - Summaries are versioned by new row (supersession). `save_intake_summary_*`
    automatically flips is_current=False on the prior current row.
  - Transcript segment edits also use the supersession pattern.
  - Upsert for interview_responses is keyed by (interview_session_id, question_key)
    so that client refresh/navigation does not create duplicate rows.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core_models import (
    CoreCase,
    CaseStageState,
    IntakeActorRecord,
    IntakeActorRelationshipInput,
    IntakeSummaryAttorney,
    IntakeSummaryClient,
    IntakeTimelineSeed,
    InterviewRecording,
    InterviewResponse,
    InterviewSession,
    InterviewTranscriptSegment,
    UploadedFile,
    UploadedFileVersion,
)


class IntakeService:
    """Wave 1 persistence service."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- cases ---------------------------------------------------------------

    async def create_case(
        self, display_name: str, created_by: Optional[str] = None
    ) -> CoreCase:
        case = CoreCase(display_name=display_name, created_by=created_by)
        self.session.add(case)
        await self.session.flush()
        return case

    async def get_case(self, core_case_id: str) -> Optional[CoreCase]:
        return await self.session.get(CoreCase, core_case_id)

    # -- stage state ---------------------------------------------------------

    async def set_stage_state(
        self,
        core_case_id: str,
        stage_key: str,
        state_value: str,
        state_details: Optional[dict] = None,
    ) -> CaseStageState:
        """Insert-or-update the stage row for (case, stage_key)."""
        result = await self.session.execute(
            select(CaseStageState).where(
                CaseStageState.core_case_id == core_case_id,
                CaseStageState.stage_key == stage_key,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.state_value = state_value
            existing.state_details = state_details
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        row = CaseStageState(
            core_case_id=core_case_id,
            stage_key=stage_key,
            state_value=state_value,
            state_details=state_details,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_stage_states(self, core_case_id: str) -> list[CaseStageState]:
        result = await self.session.execute(
            select(CaseStageState).where(CaseStageState.core_case_id == core_case_id)
        )
        return list(result.scalars().all())

    # -- interview sessions + responses --------------------------------------

    async def start_interview_session(
        self,
        core_case_id: str,
        interview_mode: str,
        interviewer_user_id: Optional[str] = None,
    ) -> InterviewSession:
        s = InterviewSession(
            core_case_id=core_case_id,
            interview_mode=interview_mode,
            interviewer_user_id=interviewer_user_id,
        )
        self.session.add(s)
        await self.session.flush()
        return s

    async def end_interview_session(self, interview_session_id: str) -> None:
        await self.session.execute(
            update(InterviewSession)
            .where(InterviewSession.id == interview_session_id)
            .values(ended_at=datetime.utcnow(), status="completed")
        )
        await self.session.flush()

    async def upsert_response(
        self,
        interview_session_id: str,
        core_case_id: str,
        question_key: str,
        response_text: Optional[str] = None,
        response_payload: Optional[dict] = None,
        answered_by: Optional[str] = None,
    ) -> InterviewResponse:
        """Upsert by (interview_session_id, question_key). Preserves refresh safety."""
        result = await self.session.execute(
            select(InterviewResponse).where(
                InterviewResponse.interview_session_id == interview_session_id,
                InterviewResponse.question_key == question_key,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.response_text = response_text
            existing.response_payload = response_payload
            existing.answered_by = answered_by
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        row = InterviewResponse(
            interview_session_id=interview_session_id,
            core_case_id=core_case_id,
            question_key=question_key,
            response_text=response_text,
            response_payload=response_payload,
            answered_by=answered_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_responses(self, interview_session_id: str) -> list[InterviewResponse]:
        result = await self.session.execute(
            select(InterviewResponse).where(
                InterviewResponse.interview_session_id == interview_session_id
            )
        )
        return list(result.scalars().all())

    # -- recordings ----------------------------------------------------------

    async def record_interview_audio(
        self,
        interview_session_id: str,
        core_case_id: str,
        storage_uri: str,
        storage_backend: str,
        file_hash: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        mime_type: Optional[str] = None,
        recorded_by: Optional[str] = None,
    ) -> InterviewRecording:
        row = InterviewRecording(
            interview_session_id=interview_session_id,
            core_case_id=core_case_id,
            storage_uri=storage_uri,
            storage_backend=storage_backend,
            file_hash=file_hash,
            duration_seconds=duration_seconds,
            mime_type=mime_type,
            recorded_by=recorded_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def save_transcript_segment(
        self,
        interview_recording_id: str,
        interview_session_id: str,
        core_case_id: str,
        segment_index: int,
        text_content: str,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        speaker_label: Optional[str] = None,
        supersedes_segment_id: Optional[str] = None,
        edited_by: Optional[str] = None,
    ) -> InterviewTranscriptSegment:
        """Insert a transcript segment.

        If `supersedes_segment_id` is provided, the prior row is flipped to
        is_current=False. The prior row is never mutated in content terms.
        """
        version = 1
        if supersedes_segment_id:
            prior = await self.session.get(
                InterviewTranscriptSegment, supersedes_segment_id
            )
            if prior is not None:
                version = prior.version + 1
                prior.is_current = False
        row = InterviewTranscriptSegment(
            interview_recording_id=interview_recording_id,
            interview_session_id=interview_session_id,
            core_case_id=core_case_id,
            segment_index=segment_index,
            text_content=text_content,
            start_ms=start_ms,
            end_ms=end_ms,
            speaker_label=speaker_label,
            version=version,
            supersedes_segment_id=supersedes_segment_id,
            is_current=True,
            edited_by=edited_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    # -- uploaded files ------------------------------------------------------

    async def register_uploaded_file(
        self,
        core_case_id: str,
        file_name: str,
        sha256_hash: str,
        source_type: str,
        storage_uri: str,
        storage_backend: str,
        mime_type: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        source_reference: Optional[str] = None,
        uploaded_by: Optional[str] = None,
    ) -> UploadedFile:
        row = UploadedFile(
            core_case_id=core_case_id,
            file_name=file_name,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            sha256_hash=sha256_hash,
            source_type=source_type,
            source_reference=source_reference,
            storage_uri=storage_uri,
            storage_backend=storage_backend,
            uploaded_by=uploaded_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def add_file_version(
        self,
        uploaded_file_id: str,
        core_case_id: str,
        version_number: int,
        sha256_hash: str,
        storage_uri: str,
        storage_backend: str,
        file_size_bytes: Optional[int] = None,
        change_note: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> UploadedFileVersion:
        row = UploadedFileVersion(
            uploaded_file_id=uploaded_file_id,
            core_case_id=core_case_id,
            version_number=version_number,
            sha256_hash=sha256_hash,
            storage_uri=storage_uri,
            storage_backend=storage_backend,
            file_size_bytes=file_size_bytes,
            change_note=change_note,
            created_by=created_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_uploaded_files(self, core_case_id: str) -> list[UploadedFile]:
        result = await self.session.execute(
            select(UploadedFile).where(UploadedFile.core_case_id == core_case_id)
        )
        return list(result.scalars().all())

    # -- actors + relationship inputs ---------------------------------------

    async def add_intake_actor(
        self,
        core_case_id: str,
        actor_type: str,
        display_name: str,
        role_context: Optional[str] = None,
        raw_input_text: Optional[str] = None,
        source_reference: Optional[str] = None,
        confidence: Optional[float] = None,
        created_by: Optional[str] = None,
    ) -> IntakeActorRecord:
        row = IntakeActorRecord(
            core_case_id=core_case_id,
            actor_type=actor_type,
            display_name=display_name,
            role_context=role_context,
            raw_input_text=raw_input_text,
            source_reference=source_reference,
            confidence=confidence,
            created_by=created_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def add_actor_relationship(
        self,
        core_case_id: str,
        actor_a_id: str,
        relationship_claim: str,
        actor_b_id: Optional[str] = None,
        direction: Optional[str] = None,
        source_reference: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> IntakeActorRelationshipInput:
        row = IntakeActorRelationshipInput(
            core_case_id=core_case_id,
            actor_a_id=actor_a_id,
            actor_b_id=actor_b_id,
            relationship_claim=relationship_claim,
            direction=direction,
            source_reference=source_reference,
            created_by=created_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_intake_actors(self, core_case_id: str) -> list[IntakeActorRecord]:
        result = await self.session.execute(
            select(IntakeActorRecord).where(IntakeActorRecord.core_case_id == core_case_id)
        )
        return list(result.scalars().all())

    # -- summaries (versioned) ----------------------------------------------

    async def save_intake_summary_client(
        self,
        core_case_id: str,
        summary_text: str,
        summary_payload: Optional[dict] = None,
        created_by: Optional[str] = None,
    ) -> IntakeSummaryClient:
        """Append a new version; flips previous current row to is_current=False."""
        prior_result = await self.session.execute(
            select(IntakeSummaryClient).where(
                IntakeSummaryClient.core_case_id == core_case_id,
                IntakeSummaryClient.is_current.is_(True),
            )
        )
        prior = prior_result.scalar_one_or_none()
        new_version = 1
        supersedes_id = None
        if prior is not None:
            prior.is_current = False
            new_version = prior.version_number + 1
            supersedes_id = prior.id
        row = IntakeSummaryClient(
            core_case_id=core_case_id,
            summary_text=summary_text,
            summary_payload=summary_payload,
            version_number=new_version,
            supersedes_summary_id=supersedes_id,
            is_current=True,
            created_by=created_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def save_intake_summary_attorney(
        self,
        core_case_id: str,
        summary_text: str,
        summary_payload: Optional[dict] = None,
        created_by: Optional[str] = None,
    ) -> IntakeSummaryAttorney:
        prior_result = await self.session.execute(
            select(IntakeSummaryAttorney).where(
                IntakeSummaryAttorney.core_case_id == core_case_id,
                IntakeSummaryAttorney.is_current.is_(True),
            )
        )
        prior = prior_result.scalar_one_or_none()
        new_version = 1
        supersedes_id = None
        if prior is not None:
            prior.is_current = False
            new_version = prior.version_number + 1
            supersedes_id = prior.id
        row = IntakeSummaryAttorney(
            core_case_id=core_case_id,
            summary_text=summary_text,
            summary_payload=summary_payload,
            version_number=new_version,
            supersedes_summary_id=supersedes_id,
            is_current=True,
            created_by=created_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_current_client_summary(
        self, core_case_id: str
    ) -> Optional[IntakeSummaryClient]:
        result = await self.session.execute(
            select(IntakeSummaryClient).where(
                IntakeSummaryClient.core_case_id == core_case_id,
                IntakeSummaryClient.is_current.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_current_attorney_summary(
        self, core_case_id: str
    ) -> Optional[IntakeSummaryAttorney]:
        result = await self.session.execute(
            select(IntakeSummaryAttorney).where(
                IntakeSummaryAttorney.core_case_id == core_case_id,
                IntakeSummaryAttorney.is_current.is_(True),
            )
        )
        return result.scalar_one_or_none()

    # -- timeline seeds ------------------------------------------------------

    async def add_timeline_seed(
        self,
        core_case_id: str,
        seed_text: str,
        event_time_candidate: Optional[str] = None,
        event_time_iso: Optional[datetime] = None,
        time_precision: Optional[str] = None,
        source_response_id: Optional[str] = None,
        source_file_id: Optional[str] = None,
        related_actor_id: Optional[str] = None,
        uncertainty_notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> IntakeTimelineSeed:
        row = IntakeTimelineSeed(
            core_case_id=core_case_id,
            seed_text=seed_text,
            event_time_candidate=event_time_candidate,
            event_time_iso=event_time_iso,
            time_precision=time_precision,
            source_response_id=source_response_id,
            source_file_id=source_file_id,
            related_actor_id=related_actor_id,
            uncertainty_notes=uncertainty_notes,
            created_by=created_by,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_timeline_seeds(self, core_case_id: str) -> list[IntakeTimelineSeed]:
        result = await self.session.execute(
            select(IntakeTimelineSeed).where(
                IntakeTimelineSeed.core_case_id == core_case_id
            )
        )
        return list(result.scalars().all())
