"""X-T5 — Messy-path intake seed case.

Seeds ONE deliberately ambiguous / internally-conflicting synthetic matter and
asserts the INTAKE layer FAILS SAFELY: it preserves every ambiguity and conflict
as-given and never silently merges, dedups, resolves, or "guesses."

This is the repo-reproducible gate-completion proof for the messy path
(no PII, no external assets). Acceptance (X-T5): the system preserves ambiguity
instead of guessing.

Matter: "Doe Partnership Dispute" — same-looking actors that may or may not be the
same person, contradictory relationship claims, conflicting event dates, a
low-confidence parse, and a self-contradicting client account.
"""
from __future__ import annotations

import pytest

from services.intake_service import IntakeService

pytestmark = pytest.mark.asyncio


async def _seed_messy(svc: IntakeService) -> dict:
    case = await svc.create_case(
        display_name="Doe Partnership Dispute (ambiguous parties)",
        created_by="seed_messy",
    )
    await svc.set_stage_state(
        case.id, "intake", "in_progress",
        state_details={"completeness": 0.4, "open_questions": 5},
    )

    sess = await svc.start_interview_session(
        core_case_id=case.id, interview_mode="audio", interviewer_user_id="atty_b"
    )
    q1 = await svc.upsert_response(
        interview_session_id=sess.id, core_case_id=case.id, question_key="q1_narrative",
        response_text=(
            "There was a J. Mercer involved, and also a Jordan Mercer — the client "
            "is not sure if they are the same person. The deal closed sometime in "
            "spring, maybe March or maybe May."
        ),
        answered_by="client",
    )

    # Two actors that LOOK like the same person. Intake must NOT auto-merge them.
    a_short = await svc.add_intake_actor(
        core_case_id=case.id, actor_type="person", display_name="J. Mercer",
        role_context="possible partner (per email signature)",
        raw_input_text="J. Mercer", confidence=0.5, created_by="seed_messy",
    )
    a_full = await svc.add_intake_actor(
        core_case_id=case.id, actor_type="person", display_name="Jordan Mercer",
        role_context="possible partner (per verbal account)",
        raw_input_text="Jordan Mercer", confidence=0.5, created_by="seed_messy",
    )
    # An actor of genuinely unknown type and very low confidence.
    a_unknown = await svc.add_intake_actor(
        core_case_id=case.id, actor_type="unknown", display_name="\"The Group\"",
        role_context="unclear — entity or collective?", confidence=0.2,
        created_by="seed_messy",
    )

    # Contradictory relationship claims about the SAME pair. Both must persist.
    await svc.add_actor_relationship(
        core_case_id=case.id, actor_a_id=a_short.id, actor_b_id=a_full.id,
        relationship_claim="are the SAME person (client's later guess)",
        direction="bidirectional", source_reference="q1_narrative",
    )
    await svc.add_actor_relationship(
        core_case_id=case.id, actor_a_id=a_short.id, actor_b_id=a_full.id,
        relationship_claim="are DIFFERENT people (client's initial account)",
        direction="bidirectional", source_reference="q1_narrative",
    )

    # Conflicting dates for the SAME event — preserve both, flag uncertainty.
    await svc.add_timeline_seed(
        core_case_id=case.id, seed_text="Deal closed", event_time_candidate="2023-03",
        time_precision="approximate", source_response_id=q1.id,
        uncertainty_notes="Client said 'maybe March'; conflicts with the May seed.",
        created_by="seed_messy",
    )
    await svc.add_timeline_seed(
        core_case_id=case.id, seed_text="Deal closed", event_time_candidate="2023-05",
        time_precision="approximate", source_response_id=q1.id,
        uncertainty_notes="Client said 'maybe May'; conflicts with the March seed.",
        created_by="seed_messy",
    )

    # Self-contradicting client summary across two versions — both retained.
    await svc.save_intake_summary_client(
        core_case_id=case.id, summary_text="Client says there was a written partnership agreement.",
        created_by="seed_messy",
    )
    v2 = await svc.save_intake_summary_client(
        core_case_id=case.id,
        summary_text="Client now says the partnership was only verbal — no written agreement.",
        created_by="seed_messy",
    )

    await svc.session.commit()
    return {
        "case_id": case.id,
        "actor_short_id": a_short.id,
        "actor_full_id": a_full.id,
        "actor_unknown_id": a_unknown.id,
        "client_summary_v2_id": v2.id,
    }


async def test_messy_actors_are_not_auto_deduped(async_session):
    """Same-looking actors stay as distinct rows; nothing is merged."""
    svc = IntakeService(async_session)
    ids = await _seed_messy(svc)

    actors = await svc.list_intake_actors(ids["case_id"])
    # All three actors persist as separate rows — no silent dedup of the Mercers.
    assert len(actors) == 3
    ids_present = {a.id for a in actors}
    assert ids["actor_short_id"] in ids_present
    assert ids["actor_full_id"] in ids_present
    # The unknown-type actor is preserved with its declared type, not coerced.
    unknown = next(a for a in actors if a.id == ids["actor_unknown_id"])
    assert unknown.actor_type == "unknown"
    # Low-confidence values are retained verbatim (not normalized away).
    assert {a.confidence for a in actors} == {0.5, 0.2}


async def test_messy_conflicting_claims_and_dates_are_preserved(async_session):
    """Contradictory relationship claims and conflicting dates both persist."""
    from core_models import IntakeActorRelationshipInput
    from sqlalchemy import select

    svc = IntakeService(async_session)
    ids = await _seed_messy(svc)
    case_id = ids["case_id"]

    rels = (
        await async_session.execute(
            select(IntakeActorRelationshipInput).where(
                IntakeActorRelationshipInput.core_case_id == case_id
            )
        )
    ).scalars().all()
    # BOTH the "same person" and "different people" claims survive — no resolution.
    claims = {r.relationship_claim for r in rels}
    assert any("SAME person" in c for c in claims)
    assert any("DIFFERENT people" in c for c in claims)
    assert len(rels) == 2

    # Conflicting dates for the same event are both kept, with uncertainty intact.
    seeds = await svc.list_timeline_seeds(case_id)
    deal_seeds = [s for s in seeds if s.seed_text == "Deal closed"]
    assert len(deal_seeds) == 2
    assert {s.event_time_candidate for s in deal_seeds} == {"2023-03", "2023-05"}
    assert all(s.time_precision == "approximate" for s in deal_seeds)
    assert all(s.uncertainty_notes for s in deal_seeds)  # uncertainty preserved


async def test_messy_summary_contradiction_is_retained_not_overwritten(async_session):
    """Self-contradicting summaries: latest is current, prior preserved (no data loss)."""
    from core_models import IntakeSummaryClient
    from sqlalchemy import select

    svc = IntakeService(async_session)
    ids = await _seed_messy(svc)

    all_summaries = (
        await async_session.execute(
            select(IntakeSummaryClient).where(
                IntakeSummaryClient.core_case_id == ids["case_id"]
            )
        )
    ).scalars().all()
    # Both the "written agreement" and "verbal only" versions are retained.
    assert len(all_summaries) == 2
    current = [s for s in all_summaries if s.is_current]
    assert len(current) == 1
    assert current[0].id == ids["client_summary_v2_id"]
    # The contradicting earlier account is NOT destroyed — it's still queryable.
    prior = [s for s in all_summaries if not s.is_current]
    assert len(prior) == 1
    assert "written partnership agreement" in prior[0].summary_text
