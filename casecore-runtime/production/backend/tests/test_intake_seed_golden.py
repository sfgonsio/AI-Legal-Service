"""X-T4 — Golden-path intake seed case.

Seeds ONE coherent, internally-consistent synthetic matter across all 13 Wave 1
INTAKE tables, then reads everything back and asserts end-to-end coherence.

This is the repo-reproducible gate-completion proof for the golden path: fully
synthetic (no PII, no external assets), so it runs in CI. It complements
scripts/wave_proof.py, which exercises real intake data from a local (gitignored)
asset and therefore cannot run on a clean checkout.

Matter: "Rivera v. Hartwell Logistics" — a clean, unambiguous wrongful-termination
contract dispute. Every actor, date, and claim is consistent; nothing is left
ambiguous. Acceptance (X-T4): end-to-end read/write sanity across the wave.
"""
from __future__ import annotations

import hashlib

import pytest

from services.intake_service import IntakeService

pytestmark = pytest.mark.asyncio


async def _seed_golden(svc: IntakeService) -> dict:
    """Write a coherent matter across every Wave 1 table. Returns key ids."""
    case = await svc.create_case(
        display_name="Rivera v. Hartwell Logistics (wrongful termination)",
        created_by="seed_golden",
    )

    # Stage progression: intake opened, then completed — coherent transition.
    await svc.set_stage_state(case.id, "intake", "in_progress")
    await svc.set_stage_state(
        case.id, "intake", "completed", state_details={"completeness": 1.0}
    )

    # Interview session with two answered questions.
    sess = await svc.start_interview_session(
        core_case_id=case.id, interview_mode="written", interviewer_user_id="atty_a"
    )
    q1 = await svc.upsert_response(
        interview_session_id=sess.id,
        core_case_id=case.id,
        question_key="q1_narrative",
        response_text=(
            "Maria Rivera worked as a dispatch coordinator for Hartwell Logistics "
            "from 2019 until she was terminated on 2023-03-15."
        ),
        answered_by="maria_rivera",
    )
    await svc.upsert_response(
        interview_session_id=sess.id,
        core_case_id=case.id,
        question_key="q2_claims",
        response_text="Claims: breach of written employment contract; unpaid commissions.",
        answered_by="maria_rivera",
    )
    await svc.end_interview_session(sess.id)

    # Uploaded file + a second version (e.g., re-scanned contract).
    contract_bytes_v1 = b"EMPLOYMENT AGREEMENT v1 - Rivera/Hartwell"
    up = await svc.register_uploaded_file(
        core_case_id=case.id,
        file_name="employment_agreement.pdf",
        sha256_hash=hashlib.sha256(contract_bytes_v1).hexdigest(),
        source_type="upload",
        storage_uri="file:///cases/rivera/employment_agreement.pdf",
        storage_backend="local_filesystem",
        mime_type="application/pdf",
        file_size_bytes=len(contract_bytes_v1),
        uploaded_by="atty_a",
    )
    contract_bytes_v2 = b"EMPLOYMENT AGREEMENT v2 - Rivera/Hartwell - rescanned"
    await svc.add_file_version(
        uploaded_file_id=up.id,
        core_case_id=case.id,
        version_number=2,
        sha256_hash=hashlib.sha256(contract_bytes_v2).hexdigest(),
        storage_uri="file:///cases/rivera/employment_agreement_v2.pdf",
        storage_backend="local_filesystem",
        file_size_bytes=len(contract_bytes_v2),
        change_note="Higher-resolution rescan of pages 2-3.",
        created_by="atty_a",
    )

    # Recording + transcript segment, then a corrected (superseding) segment.
    rec = await svc.record_interview_audio(
        interview_session_id=sess.id,
        core_case_id=case.id,
        storage_uri="file:///cases/rivera/intake_call.wav",
        storage_backend="local_filesystem",
        file_hash="deadbeef",
        duration_seconds=600,
        mime_type="audio/wav",
        recorded_by="atty_a",
    )
    seg = await svc.save_transcript_segment(
        interview_recording_id=rec.id,
        interview_session_id=sess.id,
        core_case_id=case.id,
        segment_index=0,
        text_content="I was terminated on March 15th.",
        speaker_label="Maria Rivera",
    )
    corrected = await svc.save_transcript_segment(
        interview_recording_id=rec.id,
        interview_session_id=sess.id,
        core_case_id=case.id,
        segment_index=0,
        text_content="I was terminated on March 15, 2023.",
        speaker_label="Maria Rivera",
        supersedes_segment_id=seg.id,
        edited_by="atty_a",
    )

    # Actors: plaintiff (person), defendant (entity), one witness — all distinct.
    plaintiff = await svc.add_intake_actor(
        core_case_id=case.id, actor_type="person", display_name="Maria Rivera",
        role_context="plaintiff; former dispatch coordinator", confidence=1.0,
        created_by="seed_golden",
    )
    defendant = await svc.add_intake_actor(
        core_case_id=case.id, actor_type="entity", display_name="Hartwell Logistics, Inc.",
        role_context="defendant; former employer", confidence=1.0, created_by="seed_golden",
    )
    await svc.add_intake_actor(
        core_case_id=case.id, actor_type="person", display_name="Devon Park",
        role_context="witness; co-worker", confidence=0.9, created_by="seed_golden",
    )
    await svc.add_actor_relationship(
        core_case_id=case.id,
        actor_a_id=plaintiff.id,
        actor_b_id=defendant.id,
        relationship_claim="employed by, under written contract 2019-2023",
        direction="a_to_b",
        source_reference="q1_narrative",
    )

    # Client + attorney summaries (distinct strata), client summary revised once.
    await svc.save_intake_summary_client(
        core_case_id=case.id, summary_text="Client says she was fired without cause.",
        created_by="seed_golden",
    )
    client_v2 = await svc.save_intake_summary_client(
        core_case_id=case.id,
        summary_text="Client terminated 2023-03-15; alleges breach of written contract.",
        created_by="seed_golden",
    )
    await svc.save_intake_summary_attorney(
        core_case_id=case.id,
        summary_text="Viable breach-of-contract claim; verify commission schedule.",
        created_by="atty_a",
    )

    # Timeline seeds — consistent, source-linked dates.
    for text, when, prec in [
        ("Rivera hired as dispatch coordinator", "2019-06-01", "exact"),
        ("Written employment agreement signed", "2019-06-01", "exact"),
        ("Rivera terminated", "2023-03-15", "exact"),
    ]:
        await svc.add_timeline_seed(
            core_case_id=case.id, seed_text=text, event_time_candidate=when,
            time_precision=prec, source_response_id=q1.id, related_actor_id=plaintiff.id,
            created_by="seed_golden",
        )

    await svc.session.commit()
    return {
        "case_id": case.id,
        "session_id": sess.id,
        "uploaded_file_id": up.id,
        "orig_segment_id": seg.id,
        "current_segment_id": corrected.id,
        "client_summary_v2_id": client_v2.id,
    }


async def test_golden_path_seed_reads_back_coherently(async_session):
    svc = IntakeService(async_session)
    ids = await _seed_golden(svc)
    case_id = ids["case_id"]

    # Case + stage state.
    case = await svc.get_case(case_id)
    assert case is not None and case.display_name.startswith("Rivera v. Hartwell")
    stages = await svc.get_stage_states(case_id)
    assert len(stages) == 1  # upsert keyed by (case, stage_key) — one intake row
    assert stages[0].state_value == "completed"

    # Interview responses survived and are linked.
    responses = await svc.get_responses(ids["session_id"])
    assert {r.question_key for r in responses} == {"q1_narrative", "q2_claims"}

    # Uploaded file present; version chain intact.
    files = await svc.list_uploaded_files(case_id)
    assert len(files) == 1 and files[0].id == ids["uploaded_file_id"]

    # Actors distinct, relationship recorded.
    actors = await svc.list_intake_actors(case_id)
    assert len(actors) == 3
    assert {a.actor_type for a in actors} == {"person", "entity"}

    # Latest summaries are the current ones; prior preserved (versioning).
    client_cur = await svc.get_current_client_summary(case_id)
    assert client_cur is not None
    assert client_cur.id == ids["client_summary_v2_id"]
    assert client_cur.version_number == 2 and client_cur.is_current is True
    atty_cur = await svc.get_current_attorney_summary(case_id)
    assert atty_cur is not None and atty_cur.is_current is True

    # Timeline seeds all coherent and source-linked.
    seeds = await svc.list_timeline_seeds(case_id)
    assert len(seeds) == 3
    assert all(s.source_response_id is not None for s in seeds)
    assert all(s.time_precision == "exact" for s in seeds)


async def test_golden_path_transcript_supersession_is_clean(async_session):
    """The corrected transcript segment supersedes the original non-destructively."""
    from core_models import InterviewTranscriptSegment
    from sqlalchemy import select

    svc = IntakeService(async_session)
    ids = await _seed_golden(svc)

    rows = (
        await async_session.execute(
            select(InterviewTranscriptSegment).where(
                InterviewTranscriptSegment.core_case_id == ids["case_id"]
            )
        )
    ).scalars().all()
    by_id = {r.id: r for r in rows}

    # Both rows exist — the original is preserved, not mutated away.
    assert ids["orig_segment_id"] in by_id
    assert ids["current_segment_id"] in by_id
    orig = by_id[ids["orig_segment_id"]]
    current = by_id[ids["current_segment_id"]]

    assert orig.is_current is False  # superseded
    assert current.is_current is True  # the live version
    assert current.version == 2
    assert current.supersedes_segment_id == orig.id
    # Original text is untouched (non-destructive edit).
    assert orig.text_content == "I was terminated on March 15th."
