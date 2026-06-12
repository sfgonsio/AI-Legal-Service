"""Wave 1 read/write tests for IntakeService."""
from __future__ import annotations

import pytest

from services.intake_service import IntakeService


@pytest.mark.asyncio
async def test_case_create_and_read(async_session):
    svc = IntakeService(async_session)
    case = await svc.create_case(display_name="Jeremy v. David", created_by="atty1")
    await async_session.commit()

    assert case.id is not None
    assert case.stratum == "truth"

    got = await svc.get_case(case.id)
    assert got is not None
    assert got.display_name == "Jeremy v. David"


@pytest.mark.asyncio
async def test_stage_state_upsert_is_queryable(async_session):
    svc = IntakeService(async_session)
    case = await svc.create_case("Golden path")
    row1 = await svc.set_stage_state(case.id, "intake", "in_progress")
    row2 = await svc.set_stage_state(case.id, "intake", "complete", {"responses": 12})
    await async_session.commit()

    assert row1.id == row2.id  # upsert keeps row identity
    assert row2.state_value == "complete"
    assert row2.state_details == {"responses": 12}

    states = await svc.get_stage_states(case.id)
    assert len(states) == 1


@pytest.mark.asyncio
async def test_interview_responses_persist_and_upsert(async_session):
    svc = IntakeService(async_session)
    case = await svc.create_case("Refresh test")
    sess = await svc.start_interview_session(
        case.id, interview_mode="written", interviewer_user_id="atty1"
    )
    r1 = await svc.upsert_response(
        sess.id, case.id, "q_incident_date", response_text="2023-09-01"
    )
    # simulate client refresh: same key, updated value
    r2 = await svc.upsert_response(
        sess.id, case.id, "q_incident_date", response_text="2023-09-02"
    )
    r3 = await svc.upsert_response(
        sess.id, case.id, "q_damages", response_text="$15k medical"
    )
    await async_session.commit()

    assert r1.id == r2.id  # upsert by (session, question_key)
    assert r1.id != r3.id
    responses = await svc.get_responses(sess.id)
    assert len(responses) == 2
    by_key = {r.question_key: r.response_text for r in responses}
    assert by_key["q_incident_date"] == "2023-09-02"


@pytest.mark.asyncio
async def test_recording_immutable_and_transcript_supersession(async_session):
    svc = IntakeService(async_session)
    case = await svc.create_case("Audio test")
    sess = await svc.start_interview_session(case.id, interview_mode="audio")
    rec = await svc.record_interview_audio(
        interview_session_id=sess.id,
        core_case_id=case.id,
        storage_uri="s3://bucket/rec.wav",
        storage_backend="s3",
        file_hash="abc123",
        duration_seconds=1800,
    )
    seg1 = await svc.save_transcript_segment(
        interview_recording_id=rec.id,
        interview_session_id=sess.id,
        core_case_id=case.id,
        segment_index=0,
        text_content="Initial transcription text.",
    )
    seg2 = await svc.save_transcript_segment(
        interview_recording_id=rec.id,
        interview_session_id=sess.id,
        core_case_id=case.id,
        segment_index=0,
        text_content="Edited transcription text.",
        supersedes_segment_id=seg1.id,
        edited_by="atty1",
    )
    await async_session.commit()

    # The recording row is unchanged — immutability by convention, enforced by
    # the service (no update_* methods).
    assert rec.storage_uri == "s3://bucket/rec.wav"

    # Supersession: seg1 flipped to is_current=False, seg2 points back to seg1.
    await async_session.refresh(seg1)
    assert seg1.is_current is False
    assert seg1.version == 1
    assert seg2.is_current is True
    assert seg2.version == 2
    assert seg2.supersedes_segment_id == seg1.id
    # seg1's content is preserved, never overwritten.
    assert seg1.text_content == "Initial transcription text."


@pytest.mark.asyncio
async def test_uploaded_files_and_versions(async_session):
    svc = IntakeService(async_session)
    case = await svc.create_case("Files test")
    f = await svc.register_uploaded_file(
        core_case_id=case.id,
        file_name="contract.pdf",
        sha256_hash="hash-v1",
        source_type="upload",
        storage_uri="s3://bucket/contract.pdf",
        storage_backend="s3",
        mime_type="application/pdf",
        file_size_bytes=12345,
    )
    v2 = await svc.add_file_version(
        uploaded_file_id=f.id,
        core_case_id=case.id,
        version_number=2,
        sha256_hash="hash-v2",
        storage_uri="s3://bucket/contract_v2.pdf",
        storage_backend="s3",
        change_note="attorney redacted signature",
    )
    await async_session.commit()

    files = await svc.list_uploaded_files(case.id)
    assert len(files) == 1
    assert files[0].sha256_hash == "hash-v1"  # original untouched
    assert v2.version_number == 2


@pytest.mark.asyncio
async def test_actors_and_relationships_persist(async_session):
    svc = IntakeService(async_session)
    case = await svc.create_case("Actors test")
    alice = await svc.add_intake_actor(
        case.id, actor_type="person", display_name="Alice", role_context="plaintiff"
    )
    bob = await svc.add_intake_actor(
        case.id, actor_type="person", display_name="Bob", role_context="defendant"
    )
    rel = await svc.add_actor_relationship(
        case.id,
        actor_a_id=alice.id,
        actor_b_id=bob.id,
        relationship_claim="former spouse",
        direction="bidirectional",
    )
    await async_session.commit()

    actors = await svc.list_intake_actors(case.id)
    assert {a.display_name for a in actors} == {"Alice", "Bob"}
    assert rel.actor_a_id == alice.id and rel.actor_b_id == bob.id


@pytest.mark.asyncio
async def test_intake_summary_versioning(async_session):
    svc = IntakeService(async_session)
    case = await svc.create_case("Summary test")

    v1 = await svc.save_intake_summary_client(
        case.id, summary_text="v1 narrative", created_by="client"
    )
    v2 = await svc.save_intake_summary_client(
        case.id, summary_text="v2 narrative revised", created_by="client"
    )
    # Attorney summary is independent of client summary.
    av1 = await svc.save_intake_summary_attorney(
        case.id, summary_text="attorney legal framing v1", created_by="atty1"
    )
    await async_session.commit()

    await async_session.refresh(v1)
    assert v1.is_current is False
    assert v1.version_number == 1
    assert v2.is_current is True
    assert v2.version_number == 2
    assert v2.supersedes_summary_id == v1.id

    current_client = await svc.get_current_client_summary(case.id)
    current_attorney = await svc.get_current_attorney_summary(case.id)
    assert current_client is not None and current_client.id == v2.id
    assert current_attorney is not None and current_attorney.id == av1.id


@pytest.mark.asyncio
async def test_timeline_seeds_linked_to_sources(async_session):
    from datetime import datetime as _dt

    svc = IntakeService(async_session)
    case = await svc.create_case("Timeline test")
    sess = await svc.start_interview_session(case.id, interview_mode="written")
    resp = await svc.upsert_response(
        sess.id, case.id, "q_incident", response_text="They met in June"
    )
    alice = await svc.add_intake_actor(case.id, "person", "Alice")

    seed = await svc.add_timeline_seed(
        core_case_id=case.id,
        seed_text="They met",
        event_time_candidate="June 2023",
        event_time_iso=_dt(2023, 6, 1),
        time_precision="approximate",
        source_response_id=resp.id,
        related_actor_id=alice.id,
        uncertainty_notes="month is approximate per client",
    )
    await async_session.commit()

    seeds = await svc.list_timeline_seeds(case.id)
    assert len(seeds) == 1
    assert seeds[0].source_response_id == resp.id
    assert seeds[0].related_actor_id == alice.id
    assert seeds[0].time_precision == "approximate"
