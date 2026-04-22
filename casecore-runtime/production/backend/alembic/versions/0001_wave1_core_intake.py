"""Wave 1: Case + intake foundation (core_cases + 12 child tables).

Revision ID: 0001_wave1_core_intake
Revises:
Create Date: 2026-04-21

Creates the 13 truth-layer tables for Wave 1 of the core data plan.
All new tables; does not touch legacy models.py tables (including the legacy
`cases` table, which remains unchanged).

Portability notes:
  - UUIDs stored as CHAR(36). Portable across SQLite and PostgreSQL.
  - Timestamps use plain DATETIME; Python-side defaults are applied by the ORM.
  - JSON columns use sa.JSON (TEXT in SQLite, JSON in PG — JSONB deferred).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_wave1_core_intake"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. core_cases (root of Wave 1 FK tree)
    op.create_table(
        "core_cases",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("stratum", sa.String(length=20), nullable=False, server_default="truth"),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 2. case_stage_state
    op.create_table(
        "case_stage_state",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage_key", sa.String(length=100), nullable=False),
        sa.Column("state_value", sa.String(length=100), nullable=False),
        sa.Column("state_details", sa.JSON(), nullable=True),
        sa.Column("entered_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("core_case_id", "stage_key", name="uq_case_stage_state_key"),
    )
    op.create_index("ix_case_stage_state_core_case_id", "case_stage_state", ["core_case_id"])

    # 3. uploaded_files (comes before interview_responses because timeline seeds FK to both)
    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("source_reference", sa.String(length=1024), nullable=True),
        sa.Column("storage_uri", sa.String(length=1024), nullable=False),
        sa.Column("storage_backend", sa.String(length=50), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_uploaded_files_core_case_id", "uploaded_files", ["core_case_id"])
    op.create_index("ix_uploaded_files_sha256_hash", "uploaded_files", ["sha256_hash"])

    # 4. interview_sessions
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("interview_mode", sa.String(length=30), nullable=False),
        sa.Column("interviewer_user_id", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="in_progress"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_interview_sessions_core_case_id", "interview_sessions", ["core_case_id"])

    # 5. interview_responses
    op.create_table(
        "interview_responses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "interview_session_id",
            sa.String(length=36),
            sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_key", sa.String(length=255), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("answered_by", sa.String(length=255), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_interview_responses_interview_session_id",
        "interview_responses",
        ["interview_session_id"],
    )
    op.create_index("ix_interview_responses_core_case_id", "interview_responses", ["core_case_id"])
    op.create_index(
        "ix_interview_responses_session_question",
        "interview_responses",
        ["interview_session_id", "question_key"],
    )

    # 6. interview_recordings (immutable)
    op.create_table(
        "interview_recordings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "interview_session_id",
            sa.String(length=36),
            sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_uri", sa.String(length=1024), nullable=False),
        sa.Column("storage_backend", sa.String(length=50), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_interview_recordings_interview_session_id",
        "interview_recordings",
        ["interview_session_id"],
    )
    op.create_index(
        "ix_interview_recordings_core_case_id", "interview_recordings", ["core_case_id"]
    )

    # 7. interview_transcript_segments (self-referential; uses string FK forward ref)
    op.create_table(
        "interview_transcript_segments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "interview_recording_id",
            sa.String(length=36),
            sa.ForeignKey("interview_recordings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "interview_session_id",
            sa.String(length=36),
            sa.ForeignKey("interview_sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=True),
        sa.Column("end_ms", sa.Integer(), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("speaker_label", sa.String(length=255), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "supersedes_segment_id",
            sa.String(length=36),
            sa.ForeignKey("interview_transcript_segments.id"),
            nullable=True,
        ),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("edited_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_interview_transcript_segments_recording",
        "interview_transcript_segments",
        ["interview_recording_id"],
    )
    op.create_index(
        "ix_interview_transcript_segments_session",
        "interview_transcript_segments",
        ["interview_session_id"],
    )
    op.create_index(
        "ix_interview_transcript_segments_case",
        "interview_transcript_segments",
        ["core_case_id"],
    )
    op.create_index(
        "ix_interview_transcript_segments_is_current",
        "interview_transcript_segments",
        ["is_current"],
    )

    # 8. uploaded_file_versions
    op.create_table(
        "uploaded_file_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "uploaded_file_id",
            sa.String(length=36),
            sa.ForeignKey("uploaded_files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_uri", sa.String(length=1024), nullable=False),
        sa.Column("storage_backend", sa.String(length=50), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "uploaded_file_id", "version_number", name="uq_uploaded_file_version"
        ),
    )
    op.create_index(
        "ix_uploaded_file_versions_file", "uploaded_file_versions", ["uploaded_file_id"]
    )
    op.create_index(
        "ix_uploaded_file_versions_case", "uploaded_file_versions", ["core_case_id"]
    )

    # 9. intake_actor_records
    op.create_table(
        "intake_actor_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor_type", sa.String(length=30), nullable=False),
        sa.Column("display_name", sa.String(length=512), nullable=False),
        sa.Column("role_context", sa.String(length=512), nullable=True),
        sa.Column("raw_input_text", sa.Text(), nullable=True),
        sa.Column("source_reference", sa.String(length=1024), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_intake_actor_records_core_case_id", "intake_actor_records", ["core_case_id"]
    )

    # 10. intake_actor_relationship_inputs
    op.create_table(
        "intake_actor_relationship_inputs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_a_id",
            sa.String(length=36),
            sa.ForeignKey("intake_actor_records.id"),
            nullable=False,
        ),
        sa.Column(
            "actor_b_id",
            sa.String(length=36),
            sa.ForeignKey("intake_actor_records.id"),
            nullable=True,
        ),
        sa.Column("relationship_claim", sa.String(length=512), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=True),
        sa.Column("source_reference", sa.String(length=1024), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_intake_actor_relationship_inputs_case",
        "intake_actor_relationship_inputs",
        ["core_case_id"],
    )
    op.create_index(
        "ix_intake_actor_relationship_inputs_actor_a",
        "intake_actor_relationship_inputs",
        ["actor_a_id"],
    )
    op.create_index(
        "ix_intake_actor_relationship_inputs_actor_b",
        "intake_actor_relationship_inputs",
        ["actor_b_id"],
    )

    # 11. intake_summaries_client (versioned, self-ref supersedes)
    op.create_table(
        "intake_summaries_client",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("summary_payload", sa.JSON(), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "supersedes_summary_id",
            sa.String(length=36),
            sa.ForeignKey("intake_summaries_client.id"),
            nullable=True,
        ),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_intake_summaries_client_case", "intake_summaries_client", ["core_case_id"]
    )
    op.create_index(
        "ix_intake_summaries_client_is_current", "intake_summaries_client", ["is_current"]
    )

    # 12. intake_summaries_attorney (versioned, self-ref supersedes)
    op.create_table(
        "intake_summaries_attorney",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("summary_payload", sa.JSON(), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "supersedes_summary_id",
            sa.String(length=36),
            sa.ForeignKey("intake_summaries_attorney.id"),
            nullable=True,
        ),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_intake_summaries_attorney_case", "intake_summaries_attorney", ["core_case_id"]
    )
    op.create_index(
        "ix_intake_summaries_attorney_is_current",
        "intake_summaries_attorney",
        ["is_current"],
    )

    # 13. intake_timeline_seeds (FKs to interview_responses, uploaded_files, intake_actor_records)
    op.create_table(
        "intake_timeline_seeds",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seed_text", sa.Text(), nullable=False),
        sa.Column("event_time_candidate", sa.String(length=255), nullable=True),
        sa.Column("event_time_iso", sa.DateTime(), nullable=True),
        sa.Column("time_precision", sa.String(length=30), nullable=True),
        sa.Column(
            "source_response_id",
            sa.String(length=36),
            sa.ForeignKey("interview_responses.id"),
            nullable=True,
        ),
        sa.Column(
            "source_file_id",
            sa.String(length=36),
            sa.ForeignKey("uploaded_files.id"),
            nullable=True,
        ),
        sa.Column(
            "related_actor_id",
            sa.String(length=36),
            sa.ForeignKey("intake_actor_records.id"),
            nullable=True,
        ),
        sa.Column("uncertainty_notes", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_intake_timeline_seeds_case", "intake_timeline_seeds", ["core_case_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_intake_timeline_seeds_case", table_name="intake_timeline_seeds")
    op.drop_table("intake_timeline_seeds")

    op.drop_index("ix_intake_summaries_attorney_is_current", table_name="intake_summaries_attorney")
    op.drop_index("ix_intake_summaries_attorney_case", table_name="intake_summaries_attorney")
    op.drop_table("intake_summaries_attorney")

    op.drop_index("ix_intake_summaries_client_is_current", table_name="intake_summaries_client")
    op.drop_index("ix_intake_summaries_client_case", table_name="intake_summaries_client")
    op.drop_table("intake_summaries_client")

    op.drop_index("ix_intake_actor_relationship_inputs_actor_b", table_name="intake_actor_relationship_inputs")
    op.drop_index("ix_intake_actor_relationship_inputs_actor_a", table_name="intake_actor_relationship_inputs")
    op.drop_index("ix_intake_actor_relationship_inputs_case", table_name="intake_actor_relationship_inputs")
    op.drop_table("intake_actor_relationship_inputs")

    op.drop_index("ix_intake_actor_records_core_case_id", table_name="intake_actor_records")
    op.drop_table("intake_actor_records")

    op.drop_index("ix_uploaded_file_versions_case", table_name="uploaded_file_versions")
    op.drop_index("ix_uploaded_file_versions_file", table_name="uploaded_file_versions")
    op.drop_table("uploaded_file_versions")

    op.drop_index("ix_interview_transcript_segments_is_current", table_name="interview_transcript_segments")
    op.drop_index("ix_interview_transcript_segments_case", table_name="interview_transcript_segments")
    op.drop_index("ix_interview_transcript_segments_session", table_name="interview_transcript_segments")
    op.drop_index("ix_interview_transcript_segments_recording", table_name="interview_transcript_segments")
    op.drop_table("interview_transcript_segments")

    op.drop_index("ix_interview_recordings_core_case_id", table_name="interview_recordings")
    op.drop_index("ix_interview_recordings_interview_session_id", table_name="interview_recordings")
    op.drop_table("interview_recordings")

    op.drop_index("ix_interview_responses_session_question", table_name="interview_responses")
    op.drop_index("ix_interview_responses_core_case_id", table_name="interview_responses")
    op.drop_index("ix_interview_responses_interview_session_id", table_name="interview_responses")
    op.drop_table("interview_responses")

    op.drop_index("ix_interview_sessions_core_case_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")

    op.drop_index("ix_uploaded_files_sha256_hash", table_name="uploaded_files")
    op.drop_index("ix_uploaded_files_core_case_id", table_name="uploaded_files")
    op.drop_table("uploaded_files")

    op.drop_index("ix_case_stage_state_core_case_id", table_name="case_stage_state")
    op.drop_table("case_stage_state")

    op.drop_table("core_cases")
