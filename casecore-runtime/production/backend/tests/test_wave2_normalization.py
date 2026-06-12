"""Wave 2 read/write tests for MessageNormalizationService."""
from __future__ import annotations

import pytest

from services.intake_service import IntakeService
from services.message_normalization_service import (
    CANONICAL_FLAG_CODES,
    MessageNormalizationService,
)


async def _make_case(session):
    return await IntakeService(session).create_case("W2 test case")


@pytest.mark.asyncio
async def test_source_file_and_parse_status(async_session):
    case = await _make_case(async_session)
    mn = MessageNormalizationService(async_session)
    src = await mn.register_source_file(
        core_case_id=case.id,
        file_hash="sha1",
        file_type="email",
        source_system="gmail",
    )
    await mn.set_source_file_parse_status(src.id, parse_status="parsed")
    await async_session.commit()

    await async_session.refresh(src)
    assert src.parse_status == "parsed"


@pytest.mark.asyncio
async def test_message_persistence_with_thread_and_statements(async_session):
    case = await _make_case(async_session)
    mn = MessageNormalizationService(async_session)

    src = await mn.register_source_file(case.id, "sha", "email")
    thread = await mn.create_thread(
        case.id, external_thread_id="gmail-thread-1", thread_subject="Re: settlement"
    )
    msg = await mn.save_normalized_message(
        core_case_id=case.id,
        message_source_file_id=src.id,
        body_clean="I never agreed to $10,000. She told me $5,000.",
        thread_id=thread.id,
        sender_candidate="alice@example.com",
        sender_confidence=0.95,
        recipient_candidates=[{"name": "bob@example.com", "role": "to"}],
    )
    s1 = await mn.save_statement(
        core_case_id=case.id,
        normalized_message_id=msg.id,
        statement_index=0,
        statement_text="I never agreed to $10,000.",
        speaker_candidate="alice@example.com",
        speaker_confidence=0.95,
    )
    s2 = await mn.save_statement(
        core_case_id=case.id,
        normalized_message_id=msg.id,
        statement_index=1,
        statement_text="She told me $5,000.",
        speaker_candidate="alice@example.com",
        has_pronoun_flag=True,
        pronoun_resolved=False,
    )
    await async_session.commit()

    msgs = await mn.list_messages_for_thread(thread.id)
    assert len(msgs) == 1
    stmts = await mn.list_statements_for_message(msg.id)
    assert [s.statement_index for s in stmts] == [0, 1]
    # Pronoun flag on the second statement is preserved and unresolved.
    assert stmts[1].has_pronoun_flag is True
    assert stmts[1].pronoun_resolved is False


@pytest.mark.asyncio
async def test_quoted_and_forwarded_not_attributed_to_current_sender(async_session):
    case = await _make_case(async_session)
    mn = MessageNormalizationService(async_session)
    src = await mn.register_source_file(case.id, "sha", "email")
    msg = await mn.save_normalized_message(
        core_case_id=case.id,
        message_source_file_id=src.id,
        body_clean="See below.",
        sender_candidate="bob@example.com",
    )
    q = await mn.save_quoted_block(
        core_case_id=case.id,
        normalized_message_id=msg.id,
        quoted_text="I disagree with that assessment.",
        quoted_speaker="alice@example.com",
        quoted_speaker_confidence=0.9,
        depth=1,
    )
    fwd = await mn.save_forwarded_block(
        core_case_id=case.id,
        normalized_message_id=msg.id,
        chain_index=0,
        forwarded_body="Original memo body",
        original_sender="carol@example.com",
        original_recipients=[{"name": "dave@example.com", "role": "to"}],
    )
    await async_session.commit()

    # Core invariant: quoted/forwarded speakers are NOT equal to the
    # current message sender.
    assert q.quoted_speaker != msg.sender_candidate
    assert fwd.original_sender != msg.sender_candidate


@pytest.mark.asyncio
async def test_referenced_actor_and_resolution(async_session):
    intake = IntakeService(async_session)
    case = await intake.create_case("Ref actor test")
    alice = await intake.add_intake_actor(case.id, "person", "Alice")
    mn = MessageNormalizationService(async_session)
    src = await mn.register_source_file(case.id, "sha", "email")
    msg = await mn.save_normalized_message(
        core_case_id=case.id,
        message_source_file_id=src.id,
        body_clean="My boss said it was fine.",
        sender_candidate="bob@example.com",
    )
    ref = await mn.save_referenced_actor_candidate(
        core_case_id=case.id,
        normalized_message_id=msg.id,
        reference_text="my boss",
        reference_kind="role",
        candidate_actor_ids=[alice.id],
        confidence=0.6,
    )
    assert ref.resolution_status == "unresolved"
    assert ref.chosen_actor_id is None

    # Attorney resolves to Alice.
    resolved = await mn.resolve_referenced_actor(ref.id, alice.id, confidence=0.9)
    await async_session.commit()
    assert resolved.resolution_status == "resolved"
    assert resolved.chosen_actor_id == alice.id


@pytest.mark.asyncio
async def test_corpus_snapshot_upsert(async_session):
    case = await _make_case(async_session)
    mn = MessageNormalizationService(async_session)
    c1 = await mn.upsert_corpus_snapshot(
        core_case_id=case.id,
        source_file_count=1,
        thread_count=2,
        message_count=5,
        participant_snapshot=[{"name": "alice", "count": 3}],
    )
    c2 = await mn.upsert_corpus_snapshot(
        core_case_id=case.id,
        source_file_count=2,
        thread_count=3,
        message_count=12,
    )
    await async_session.commit()

    assert c1.id == c2.id  # same row, updated
    snap = await mn.get_corpus_snapshot(case.id)
    assert snap.message_count == 12
    assert snap.thread_count == 3


@pytest.mark.asyncio
async def test_quality_flag_canonical_codes_and_resolution(async_session):
    case = await _make_case(async_session)
    mn = MessageNormalizationService(async_session)
    # Canonical code accepted
    f = await mn.raise_quality_flag(
        core_case_id=case.id,
        flag_code="ambiguous_sender",
        severity="warning",
        detail_text="From header unparseable",
    )
    await mn.resolve_quality_flag(f.id, resolved_by="atty1")
    await async_session.commit()
    await async_session.refresh(f)
    assert f.resolved is True
    assert f.resolved_by == "atty1"

    # Non-canonical code rejected
    with pytest.raises(ValueError):
        await mn.raise_quality_flag(core_case_id=case.id, flag_code="bogus_code")


@pytest.mark.asyncio
async def test_failure_event_persists_stage_and_code(async_session):
    case = await _make_case(async_session)
    mn = MessageNormalizationService(async_session)
    src = await mn.register_source_file(case.id, "sha", "email")
    ev = await mn.record_failure_event(
        core_case_id=case.id,
        failure_stage="header_parsing",
        failure_code="missing_from_header",
        severity="critical",
        message_source_file_id=src.id,
        error_detail="No From: field present",
    )
    await async_session.commit()
    assert ev.failure_stage == "header_parsing"
    assert ev.failure_code == "missing_from_header"


def test_canonical_flag_codes_frozen():
    # Regression guard against accidental mutation of the canonical set.
    assert "ambiguous_sender" in CANONICAL_FLAG_CODES
    assert "insufficient_message_structure" in CANONICAL_FLAG_CODES
    assert len(CANONICAL_FLAG_CODES) == 5
