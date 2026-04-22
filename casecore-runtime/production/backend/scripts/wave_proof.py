"""Wave 1 + Wave 2 runtime proof.

End-to-end script that exercises both waves against a real SQLite database
via the hardened-core services. Demonstrates:

  Wave 1 (write):
    - create core_case
    - set case_stage_state
    - start interview_session + upsert two interview_responses
    - register one uploaded_file
    - add two intake_actor_records (Alice, Bob)
    - save one intake_summary_client version

  Wave 2 (write):
    - register one message_source_file
    - create one message_thread
    - save one normalized_message
    - save two normalized_statements
    - save one referenced_actor_candidate (unresolved)
    - raise one normalization_quality_flag (ambiguous_recipient)
    - upsert message_corpus snapshot

  Read path:
    - fetch core_case
    - list actors
    - list interview_responses
    - list uploaded_files
    - list normalized_messages for the thread
    - list statements for the message
    - list unresolved quality flags
    - list unresolved referenced_actor_candidates

Usage:
    cd casecore-runtime/production/backend
    python scripts/wave_proof.py
        --db-url sqlite+aiosqlite:///./wave_proof.db

Defaults to an in-memory DB if --db-url is omitted. Exit code 0 on success,
non-zero on any failure (including an empty read).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Make the backend root importable (scripts/ is a sibling of database.py).
_HERE = Path(__file__).resolve().parent
_BACKEND_DIR = _HERE.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


def _setup(db_url: str) -> None:
    """Force DATABASE_URL before importing database.py (which builds the async
    engine at import time)."""
    os.environ["DATABASE_URL"] = db_url


def _banner(title: str) -> None:
    bar = "=" * (len(title) + 4)
    print(f"\n{bar}\n  {title}\n{bar}")


def _step(label: str, detail: str = "") -> None:
    print(f"  [write] {label}" + (f"  -> {detail}" if detail else ""))


async def run(db_url: str) -> int:
    _setup(db_url)

    # Delay imports until after DATABASE_URL is set.
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

    from database import Base
    import models  # noqa: F401  (registers legacy tables but doesn't use them)
    import core_models  # noqa: F401

    from services.intake_service import IntakeService
    from services.message_normalization_service import MessageNormalizationService

    engine = create_async_engine(db_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # ---------------- Wave 1 ----------------
    _banner("WAVE 1 — Case + Intake write")
    async with SessionLocal() as session:
        intake = IntakeService(session)

        case = await intake.create_case(
            display_name="Alice v. Bob (wave proof)", created_by="proof_script"
        )
        _step("create_case", case.id)

        await intake.set_stage_state(case.id, "intake", "in_progress")
        _step("set_stage_state", "intake=in_progress")

        sess = await intake.start_interview_session(
            core_case_id=case.id,
            interview_mode="written",
            interviewer_user_id="atty_jane",
        )
        _step("start_interview_session", sess.id)

        r1 = await intake.upsert_response(
            interview_session_id=sess.id,
            core_case_id=case.id,
            question_key="q_incident_date",
            response_text="October 2023",
        )
        r2 = await intake.upsert_response(
            interview_session_id=sess.id,
            core_case_id=case.id,
            question_key="q_damages_summary",
            response_text="Unpaid invoices of $15,000 and lost business",
        )
        _step("upsert_response x2", f"{r1.id}, {r2.id}")

        uploaded = await intake.register_uploaded_file(
            core_case_id=case.id,
            file_name="contract_alice_bob.pdf",
            sha256_hash="sha_placeholder_contract_v1",
            source_type="upload",
            storage_uri="s3://casecore-dev/contracts/alice_bob.pdf",
            storage_backend="s3",
            mime_type="application/pdf",
            file_size_bytes=412311,
            uploaded_by="atty_jane",
        )
        _step("register_uploaded_file", uploaded.id)

        alice = await intake.add_intake_actor(
            core_case_id=case.id,
            actor_type="person",
            display_name="Alice Chen",
            role_context="plaintiff",
            raw_input_text="Alice Chen (my client)",
        )
        bob = await intake.add_intake_actor(
            core_case_id=case.id,
            actor_type="person",
            display_name="Bob Martinez",
            role_context="defendant, contract counterparty",
        )
        _step("add_intake_actor x2", f"Alice={alice.id}, Bob={bob.id}")

        client_summary = await intake.save_intake_summary_client(
            core_case_id=case.id,
            summary_text=(
                "Client reports unpaid invoices from October 2023 onward. "
                "Contract was signed; counterparty stopped payment citing "
                "scope disputes."
            ),
            created_by="atty_jane",
        )
        _step("save_intake_summary_client", f"v{client_summary.version_number}")

        await session.commit()

    # ---------------- Wave 2 ----------------
    _banner("WAVE 2 — Message normalization write")
    async with SessionLocal() as session:
        mn = MessageNormalizationService(session)

        src = await mn.register_source_file(
            core_case_id=case.id,
            file_hash="sha_msg_export_v1",
            file_type="email",
            source_system="gmail",
            uploaded_file_id=uploaded.id,
            parse_status="parsed",
        )
        _step("register_source_file", src.id)

        thread = await mn.create_thread(
            core_case_id=case.id,
            external_thread_id="gmail:thr-20231015",
            thread_subject="Re: outstanding invoice",
            participants=[
                {"name": "alice@example.com", "confidence": 0.98},
                {"name": "bob@example.com", "confidence": 0.98},
            ],
        )
        _step("create_thread", thread.id)

        msg = await mn.save_normalized_message(
            core_case_id=case.id,
            message_source_file_id=src.id,
            thread_id=thread.id,
            body_clean=(
                "I never agreed to waive the $15,000. My assistant mentioned "
                "that he told you otherwise, but that was never authorized."
            ),
            sender_candidate="alice@example.com",
            sender_confidence=0.97,
            recipient_candidates=[{"name": "bob@example.com", "role": "to", "confidence": 0.95}],
            external_message_id="<gmail-id-abc123@mail.example.com>",
            normalized_by="normalizer_v1",
        )
        _step("save_normalized_message", msg.id)

        s1 = await mn.save_statement(
            core_case_id=case.id,
            normalized_message_id=msg.id,
            statement_index=0,
            statement_text="I never agreed to waive the $15,000.",
            speaker_candidate="alice@example.com",
            speaker_confidence=0.97,
        )
        s2 = await mn.save_statement(
            core_case_id=case.id,
            normalized_message_id=msg.id,
            statement_index=1,
            statement_text="My assistant mentioned that he told you otherwise, but that was never authorized.",
            speaker_candidate="alice@example.com",
            speaker_confidence=0.97,
            has_pronoun_flag=True,
            pronoun_resolved=False,
            signal_flags=["third_person_reference", "negation"],
        )
        _step("save_statement x2", f"{s1.id}, {s2.id}")

        ref = await mn.save_referenced_actor_candidate(
            core_case_id=case.id,
            normalized_message_id=msg.id,
            normalized_statement_id=s2.id,
            reference_text="my assistant",
            reference_kind="role",
            resolution_status="unresolved",
            candidate_actor_ids=[],
            confidence=0.4,
        )
        _step("save_referenced_actor_candidate (unresolved)", ref.id)

        flag = await mn.raise_quality_flag(
            core_case_id=case.id,
            flag_code="ambiguous_recipient",
            severity="warning",
            normalized_message_id=msg.id,
            detail_text="CC list included an unverified address — sender confidence OK, recipient unclear.",
        )
        _step("raise_quality_flag", f"{flag.flag_code}:{flag.id}")

        await mn.upsert_corpus_snapshot(
            core_case_id=case.id,
            source_file_count=1,
            thread_count=1,
            message_count=1,
            participant_snapshot=[
                {"name": "alice@example.com", "message_count": 1},
                {"name": "bob@example.com", "message_count": 0},
            ],
        )
        _step("upsert_corpus_snapshot")

        await session.commit()

    # ---------------- Read path ----------------
    _banner("READ PATH — queries across Wave 1 + Wave 2")
    async with SessionLocal() as session:
        intake = IntakeService(session)
        mn = MessageNormalizationService(session)

        got_case = await intake.get_case(case.id)
        assert got_case is not None, "case not found on read"
        print(f"  case             : {got_case.display_name}  id={got_case.id[:8]}…")

        stages = await intake.get_stage_states(case.id)
        print(f"  stage_states     : {[(s.stage_key, s.state_value) for s in stages]}")

        actors = await intake.list_intake_actors(case.id)
        print(f"  actors           : {[a.display_name for a in actors]}")

        responses = await intake.get_responses(sess.id)
        print(f"  responses        :")
        for r in responses:
            print(f"    - {r.question_key} = {r.response_text!r}")

        files = await intake.list_uploaded_files(case.id)
        print(f"  uploaded_files   : {[f.file_name for f in files]}")

        current_summary = await intake.get_current_client_summary(case.id)
        print(
            f"  current summary  : v{current_summary.version_number} — "
            f"{current_summary.summary_text[:60]}…"
        )

        threads = await mn.list_threads(case.id)
        print(f"  threads          : {[(t.thread_subject, t.message_count) for t in threads]}")

        messages = await mn.list_messages_for_thread(thread.id)
        print(f"  messages(thread) : {len(messages)} message(s)")
        for m in messages:
            print(f"    - from={m.sender_candidate}  conf={m.sender_confidence}")
            print(f"      body={m.body_clean[:70]}…")

        stmts = await mn.list_statements_for_message(msg.id)
        print(f"  statements(msg)  : {len(stmts)}")
        for st in stmts:
            print(f"    [{st.statement_index}] pronoun_flag={st.has_pronoun_flag} "
                  f"resolved={st.pronoun_resolved}  {st.statement_text[:55]}…")

        flags = await mn.list_unresolved_quality_flags(case.id)
        print(f"  unresolved flags : {[(f.flag_code, f.severity) for f in flags]}")

        corpus = await mn.get_corpus_snapshot(case.id)
        print(
            f"  corpus snapshot  : sources={corpus.source_file_count} "
            f"threads={corpus.thread_count} messages={corpus.message_count}"
        )

        # Hard assertions so exit code truly reflects correctness.
        assert len(actors) == 2, f"expected 2 actors, got {len(actors)}"
        assert len(responses) == 2, f"expected 2 responses, got {len(responses)}"
        assert len(files) == 1, f"expected 1 uploaded file, got {len(files)}"
        assert len(messages) == 1, f"expected 1 normalized message, got {len(messages)}"
        assert len(stmts) == 2, f"expected 2 statements, got {len(stmts)}"
        assert len(flags) == 1 and flags[0].flag_code == "ambiguous_recipient"
        assert corpus.message_count == 1

    _banner("SUCCESS")
    await engine.dispose()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--db-url",
        default="sqlite+aiosqlite:///:memory:",
        help=(
            "SQLAlchemy async URL. Default is in-memory. To persist across "
            "invocations use e.g. sqlite+aiosqlite:///./wave_proof.db"
        ),
    )
    args = ap.parse_args()
    return asyncio.run(run(args.db_url))


if __name__ == "__main__":
    raise SystemExit(main())
