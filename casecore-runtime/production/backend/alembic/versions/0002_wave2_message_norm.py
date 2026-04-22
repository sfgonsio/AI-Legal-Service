"""Wave 2: Message normalization persistence (10 tables).

Revision ID: 0002_wave2_message_norm
Revises: 0001_wave1_core_intake
Create Date: 2026-04-21

Creates the 10 truth-layer tables for Wave 2. All tables FK to core_cases
(created in Wave 1) so Wave 1 must run first.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_wave2_message_norm"
down_revision: Union[str, None] = "0001_wave1_core_intake"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. message_source_files
    op.create_table(
        "message_source_files",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_file_id",
            sa.String(length=36),
            sa.ForeignKey("uploaded_files.id"),
            nullable=True,
        ),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.Column("source_system", sa.String(length=100), nullable=True),
        sa.Column("parse_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("parse_notes", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_message_source_files_case", "message_source_files", ["core_case_id"])
    op.create_index("ix_message_source_files_uploaded", "message_source_files", ["uploaded_file_id"])
    op.create_index("ix_message_source_files_hash", "message_source_files", ["file_hash"])

    # 2. message_threads (created before normalized_messages because of thread_id FK)
    op.create_table(
        "message_threads",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_thread_id", sa.String(length=512), nullable=True),
        sa.Column("thread_subject", sa.String(length=1024), nullable=True),
        sa.Column("participants", sa.JSON(), nullable=True),
        sa.Column("first_message_at", sa.DateTime(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_broken", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_message_threads_case", "message_threads", ["core_case_id"])

    # 3. normalized_messages
    op.create_table(
        "normalized_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "message_source_file_id",
            sa.String(length=36),
            sa.ForeignKey("message_source_files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "thread_id",
            sa.String(length=36),
            sa.ForeignKey("message_threads.id"),
            nullable=True,
        ),
        sa.Column("external_message_id", sa.String(length=512), nullable=True),
        sa.Column("sender_candidate", sa.String(length=512), nullable=True),
        sa.Column("sender_confidence", sa.Float(), nullable=True),
        sa.Column("recipient_candidates", sa.JSON(), nullable=True),
        sa.Column("body_clean", sa.Text(), nullable=False),
        sa.Column("body_raw_reference", sa.Text(), nullable=True),
        sa.Column("sent_timestamp", sa.DateTime(), nullable=True),
        sa.Column("ambiguity_flags", sa.JSON(), nullable=True),
        sa.Column("normalized_by", sa.String(length=255), nullable=True),
        sa.Column("normalization_version", sa.String(length=50), nullable=False, server_default="v1"),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_normalized_messages_case", "normalized_messages", ["core_case_id"])
    op.create_index("ix_normalized_messages_source", "normalized_messages", ["message_source_file_id"])
    op.create_index("ix_normalized_messages_thread", "normalized_messages", ["thread_id"])

    # 4. normalized_statements
    op.create_table(
        "normalized_statements",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "normalized_message_id",
            sa.String(length=36),
            sa.ForeignKey("normalized_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("statement_index", sa.Integer(), nullable=False),
        sa.Column("statement_text", sa.Text(), nullable=False),
        sa.Column("speaker_candidate", sa.String(length=512), nullable=True),
        sa.Column("speaker_confidence", sa.Float(), nullable=True),
        sa.Column("has_pronoun_flag", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("pronoun_resolved", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("pronoun_confidence", sa.Float(), nullable=True),
        sa.Column("signal_flags", sa.JSON(), nullable=True),
        sa.Column("attribution_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "normalized_message_id",
            "statement_index",
            name="uq_normalized_statement_index",
        ),
    )
    op.create_index("ix_normalized_statements_case", "normalized_statements", ["core_case_id"])
    op.create_index(
        "ix_normalized_statements_message", "normalized_statements", ["normalized_message_id"]
    )

    # 5. quoted_blocks (self-ref for nesting)
    op.create_table(
        "quoted_blocks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "normalized_message_id",
            sa.String(length=36),
            sa.ForeignKey("normalized_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_block_id",
            sa.String(length=36),
            sa.ForeignKey("quoted_blocks.id"),
            nullable=True,
        ),
        sa.Column("depth", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("quoted_speaker", sa.String(length=512), nullable=True),
        sa.Column("quoted_speaker_confidence", sa.Float(), nullable=True),
        sa.Column("quoted_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_quoted_blocks_case", "quoted_blocks", ["core_case_id"])
    op.create_index("ix_quoted_blocks_message", "quoted_blocks", ["normalized_message_id"])

    # 6. forwarded_blocks
    op.create_table(
        "forwarded_blocks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "normalized_message_id",
            sa.String(length=36),
            sa.ForeignKey("normalized_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chain_index", sa.Integer(), nullable=False),
        sa.Column("original_sender", sa.String(length=512), nullable=True),
        sa.Column("original_recipients", sa.JSON(), nullable=True),
        sa.Column("forwarded_at", sa.DateTime(), nullable=True),
        sa.Column("forwarded_body", sa.Text(), nullable=False),
        sa.Column("speaker_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_forwarded_blocks_case", "forwarded_blocks", ["core_case_id"])
    op.create_index("ix_forwarded_blocks_message", "forwarded_blocks", ["normalized_message_id"])

    # 7. referenced_actor_candidates
    op.create_table(
        "referenced_actor_candidates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "normalized_message_id",
            sa.String(length=36),
            sa.ForeignKey("normalized_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "normalized_statement_id",
            sa.String(length=36),
            sa.ForeignKey("normalized_statements.id"),
            nullable=True,
        ),
        sa.Column("reference_text", sa.Text(), nullable=False),
        sa.Column("reference_kind", sa.String(length=50), nullable=True),
        sa.Column(
            "resolution_status",
            sa.String(length=50),
            nullable=False,
            server_default="unresolved",
        ),
        sa.Column("candidate_actor_ids", sa.JSON(), nullable=True),
        sa.Column(
            "chosen_actor_id",
            sa.String(length=36),
            sa.ForeignKey("intake_actor_records.id"),
            nullable=True,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_referenced_actor_candidates_case", "referenced_actor_candidates", ["core_case_id"]
    )
    op.create_index(
        "ix_referenced_actor_candidates_message",
        "referenced_actor_candidates",
        ["normalized_message_id"],
    )

    # 8. message_corpus (one row per case)
    op.create_table(
        "message_corpus",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("source_file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("thread_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("participant_snapshot", sa.JSON(), nullable=True),
        sa.Column("conflict_markers", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 9. normalization_quality_flags
    op.create_table(
        "normalization_quality_flags",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "normalized_message_id",
            sa.String(length=36),
            sa.ForeignKey("normalized_messages.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "normalized_statement_id",
            sa.String(length=36),
            sa.ForeignKey("normalized_statements.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("flag_code", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="warning"),
        sa.Column("detail_text", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_normalization_quality_flags_case", "normalization_quality_flags", ["core_case_id"]
    )
    op.create_index(
        "ix_normalization_quality_flags_message",
        "normalization_quality_flags",
        ["normalized_message_id"],
    )

    # 10. normalization_failure_events
    op.create_table(
        "normalization_failure_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "core_case_id",
            sa.String(length=36),
            sa.ForeignKey("core_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "message_source_file_id",
            sa.String(length=36),
            sa.ForeignKey("message_source_files.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "normalized_message_id",
            sa.String(length=36),
            sa.ForeignKey("normalized_messages.id"),
            nullable=True,
        ),
        sa.Column("failure_stage", sa.String(length=100), nullable=False),
        sa.Column("failure_code", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="critical"),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("stack_trace", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_normalization_failure_events_case", "normalization_failure_events", ["core_case_id"]
    )
    op.create_index(
        "ix_normalization_failure_events_source",
        "normalization_failure_events",
        ["message_source_file_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_normalization_failure_events_source", table_name="normalization_failure_events")
    op.drop_index("ix_normalization_failure_events_case", table_name="normalization_failure_events")
    op.drop_table("normalization_failure_events")

    op.drop_index("ix_normalization_quality_flags_message", table_name="normalization_quality_flags")
    op.drop_index("ix_normalization_quality_flags_case", table_name="normalization_quality_flags")
    op.drop_table("normalization_quality_flags")

    op.drop_table("message_corpus")

    op.drop_index("ix_referenced_actor_candidates_message", table_name="referenced_actor_candidates")
    op.drop_index("ix_referenced_actor_candidates_case", table_name="referenced_actor_candidates")
    op.drop_table("referenced_actor_candidates")

    op.drop_index("ix_forwarded_blocks_message", table_name="forwarded_blocks")
    op.drop_index("ix_forwarded_blocks_case", table_name="forwarded_blocks")
    op.drop_table("forwarded_blocks")

    op.drop_index("ix_quoted_blocks_message", table_name="quoted_blocks")
    op.drop_index("ix_quoted_blocks_case", table_name="quoted_blocks")
    op.drop_table("quoted_blocks")

    op.drop_index("ix_normalized_statements_message", table_name="normalized_statements")
    op.drop_index("ix_normalized_statements_case", table_name="normalized_statements")
    op.drop_table("normalized_statements")

    op.drop_index("ix_normalized_messages_thread", table_name="normalized_messages")
    op.drop_index("ix_normalized_messages_source", table_name="normalized_messages")
    op.drop_index("ix_normalized_messages_case", table_name="normalized_messages")
    op.drop_table("normalized_messages")

    op.drop_index("ix_message_threads_case", table_name="message_threads")
    op.drop_table("message_threads")

    op.drop_index("ix_message_source_files_hash", table_name="message_source_files")
    op.drop_index("ix_message_source_files_uploaded", table_name="message_source_files")
    op.drop_index("ix_message_source_files_case", table_name="message_source_files")
    op.drop_table("message_source_files")
