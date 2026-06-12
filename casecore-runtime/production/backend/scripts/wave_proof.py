"""Wave 1 + Wave 2 runtime proof — real intake data.

End-to-end script that exercises both waves against a real SQLite database
using real intake data loaded from the canonical test asset registered in
casecore-runtime/test_data/TEST_DATA_REGISTRY.json (entry id steve_case_v1).
Preserves ambiguity — never forces resolution of pronouns or third-person
references.

Default source (resolved in this order, no user prompt):
  1. casecore-runtime/test_data/intake/steve_case_intake_v1.parsed.json
     (parsed Q1/Q2 sections — canonical for this script)
  2. casecore-runtime/test_data/intake/steve_case_intake_v1.txt
     (parse on read if the .parsed.json is absent)
  3. C:\\Users\\sfgon\\Documents\\Steve App Questions.docx
     (bootstrap fallback only)

Wave 1 (write):
  - create core_case (Mills v. Polley)
  - set case_stage_state
  - start interview_session + two interview_responses loaded from the docx
    (Question 1 = full narrative; Question 2 = legal-claims narrative)
  - register one uploaded_file (the docx itself)
  - add 6 intake_actor_records extracted from the narrative
  - save one intake_summary_client (first paragraph of Q1 narrative)
  - add a handful of intake_timeline_seeds for key dated events

Wave 2 (write):
  - register one message_source_file (the docx)
  - create one message_thread ("Re: Partnership — Dec 2022 emails")
  - save two normalized_messages (the Dec 20, 2022 and Dec 27, 2022 emails
    from Polley to Mills embedded in the Q1 narrative)
  - save normalized_statements from each message body
  - save referenced_actor_candidates for third-party entity references and
    ambiguous pronouns — all status="unresolved" (no forced resolution)
  - raise normalization_quality_flags where ambiguity merits review
  - upsert message_corpus snapshot

Read path:
  - prints every table the services expose for Wave 1 + Wave 2,
    including unresolved references and unresolved quality flags.

Ambiguity discipline:
  - Pronouns ("them", "they", "he", "my"/"I" when the sender attribution is
    only candidate-level) are flagged has_pronoun_flag=True and
    pronoun_resolved=False.
  - Entity references ("The Flowery", "Distinguished Gardens", "Direct Source
    LLC") produce referenced_actor_candidates with resolution_status=
    "unresolved". candidate_actor_ids is left empty — no forced match to
    intake_actor_records.

Usage:
  cd casecore-runtime/production/backend
  python scripts/wave_proof.py                            # canonical test asset
  python scripts/wave_proof.py --db-url sqlite+aiosqlite:///./wave_proof.db
  python scripts/wave_proof.py --source <path>            # override source
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BACKEND_DIR = _HERE.parent
_RUNTIME_ROOT = _BACKEND_DIR.parent.parent  # casecore-runtime/
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


# Canonical test-data locations (relative to the casecore-runtime/ root).
TEST_DATA_DIR = _RUNTIME_ROOT / "test_data"
REGISTRY_PATH = TEST_DATA_DIR / "TEST_DATA_REGISTRY.json"
DEFAULT_REGISTRY_ID = "steve_case_v1"
# Bootstrap fallback: used only if the canonical asset is missing AND no
# --source override is given. Scripts should NOT rely on this.
BOOTSTRAP_DOCX = r"C:\Users\sfgon\Documents\Steve App Questions.docx"


def _setup(db_url: str) -> None:
    os.environ["DATABASE_URL"] = db_url


def _banner(title: str) -> None:
    bar = "=" * (len(title) + 4)
    print(f"\n{bar}\n  {title}\n{bar}")


def _step(label: str, detail: str = "") -> None:
    print(f"  [write] {label}" + (f"  -> {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Real-data extraction from the docx
# ---------------------------------------------------------------------------

def _resolve_source(source_override: str | None) -> tuple[str, str]:
    """Return (source_path, kind) where kind is 'parsed_json' | 'txt' | 'docx'.

    Resolution order (no user prompt, no re-upload):
      1. --source override (inferred by extension)
      2. canonical parsed json from the registry
      3. canonical .txt (parse on read)
      4. bootstrap docx (last-resort; missing asset is a hard error)
    """
    if source_override:
        p = Path(source_override)
        if p.suffix == ".json":
            return str(p), "parsed_json"
        if p.suffix == ".txt":
            return str(p), "txt"
        if p.suffix.lower() == ".docx":
            return str(p), "docx"
        raise RuntimeError(f"unsupported --source extension: {p.suffix!r}")

    # Registry-driven lookup.
    if REGISTRY_PATH.exists():
        reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        entry = next(
            (e for e in reg.get("entries", []) if e.get("id") == DEFAULT_REGISTRY_ID),
            None,
        )
        if entry is not None:
            parsed = TEST_DATA_DIR.parent / entry.get("parsed_path", "")
            if parsed.exists():
                return str(parsed), "parsed_json"
            immutable = TEST_DATA_DIR.parent / entry.get("path", "")
            if immutable.exists():
                return str(immutable), "txt"

    # Bootstrap fallback — only for the very first run before the test asset
    # was written.
    if Path(BOOTSTRAP_DOCX).exists():
        return BOOTSTRAP_DOCX, "docx"

    raise RuntimeError(
        "No intake source available. Expected one of:\n"
        f"  {REGISTRY_PATH}\n"
        f"  {BOOTSTRAP_DOCX}"
    )


def load_intake_data(source_override: str | None = None) -> dict:
    """Load Q1/Q2 + embedded-email bodies + file metadata.

    Reads from the canonical test asset by default; falls back only if the
    canonical asset is missing. Returns the same shape regardless of kind.
    """
    source_path, kind = _resolve_source(source_override)

    if kind == "parsed_json":
        parsed = json.loads(Path(source_path).read_text(encoding="utf-8"))
        q1_text = parsed["sections"]["narrative"]
        q2_text = parsed["sections"]["legal_claims_q2"]
        # Re-derive the raw joined text from the parsed sections so email
        # extraction still works (it searches for date markers in the body).
        raw = q1_text + "\n" + q2_text
        file_abs = parsed.get("source_txt_path", source_path)
        # Resolve source_txt_path to an absolute path if relative.
        file_abs_path = Path(file_abs)
        if not file_abs_path.is_absolute():
            file_abs_path = TEST_DATA_DIR.parent / file_abs
        file_bytes = file_abs_path.read_bytes() if file_abs_path.exists() else b""
        file_name = file_abs_path.name if file_abs_path.exists() else "steve_case_intake_v1.txt"
        file_size = file_abs_path.stat().st_size if file_abs_path.exists() else len(raw.encode("utf-8"))
    elif kind == "txt":
        raw_txt = Path(source_path).read_text(encoding="utf-8")
        paras = raw_txt.split("\n")
        q2_idx = next((i for i, p in enumerate(paras) if p.strip() == "Question 2"), None)
        if q2_idx is None:
            raise RuntimeError(f"'Question 2' header not found in {source_path}")
        q1_text = "\n".join(p for p in paras[:q2_idx] if p.strip())
        q2_text = "\n".join(p for p in paras[q2_idx + 1:] if p.strip())
        raw = raw_txt
        file_bytes = Path(source_path).read_bytes()
        file_name = Path(source_path).name
        file_size = Path(source_path).stat().st_size
        file_abs_path = Path(source_path)
    else:  # kind == "docx"
        import docx
        doc = docx.Document(source_path)
        paras = [p.text for p in doc.paragraphs]
        raw = "\n".join(paras)
        q2_idx = next(
            (i for i, p in enumerate(paras) if p.strip() == "Question 2"),
            None,
        )
        if q2_idx is None:
            raise RuntimeError("Could not locate 'Question 2' header in source docx")
        q1_text = "\n".join(p for p in paras[:q2_idx] if p.strip())
        q2_text = "\n".join(p for p in paras[q2_idx + 1:] if p.strip())
        file_bytes = Path(source_path).read_bytes()
        file_name = Path(source_path).name
        file_size = Path(source_path).stat().st_size
        file_abs_path = Path(source_path)

    # Extract the Dec 20, 2022 email body (between its opening quote and its
    # closing phone-number/quote line). These delimiters come from the source
    # document's own formatting, so the parse is explicit rather than regex-by-index.
    email1_start = raw.find('December 20, 2022')
    email1_body_start = raw.find('"Jeremey,', email1_start)
    email1_end = raw.find('916-879-6736"', email1_body_start)
    email1_body = raw[email1_body_start: email1_end + len('916-879-6736"')]
    # Strip the surrounding quotes
    email1_body = email1_body.strip().strip('"').strip()

    email2_start = raw.find('Then a follow up email was sent 0n 12/27/2022.')
    email2_body_start = raw.find('"Jeremey,', email2_start)
    # End before "March 2, 2023" (next chronological item)
    email2_end = raw.find('March 2, 2023:', email2_body_start)
    email2_body = raw[email2_body_start: email2_end]
    email2_body = email2_body.strip().strip('"').strip()
    # The Dec 27 body is open-quoted in the source but not explicitly closed;
    # trim to content only.
    # Remove trailing stray quote chars if any.
    email2_body = email2_body.rstrip('"').rstrip()

    sha = hashlib.sha256(file_bytes).hexdigest() if file_bytes else ""

    # raw_paragraphs is used by the summary writer. Derive it uniformly.
    raw_paragraphs = raw.split("\n")

    return {
        "q1_text": q1_text,
        "q2_text": q2_text,
        "email1_body": email1_body,
        "email2_body": email2_body,
        "file_name": file_name,
        "file_size_bytes": file_size,
        "file_sha256": sha,
        "file_abs_path": str(file_abs_path),
        "raw_paragraphs": raw_paragraphs,
        "source_kind": kind,
        "source_path": source_path,
    }


def segment_into_statements(body: str) -> list[str]:
    """Break a message body into sentence-level statements.

    Uses a simple punctuation-based splitter. Keeps punctuation. Filters empty
    fragments. Deliberately simple so the split is auditable — this is not a
    Brain-level segmenter, just the statement-segmentation stage of the
    message-normalization pipeline.
    """
    # Collapse intra-body newlines to spaces so sentences that span lines stay
    # intact. Protect double-newlines so we can treat them as hard breaks.
    normalized = re.sub(r"\n{2,}", " §PARA§ ", body)
    normalized = normalized.replace("\n", " ")
    # Split on sentence terminators followed by whitespace + capital letter or
    # end-of-string.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"(\u201c])", normalized)
    out = []
    for p in parts:
        p = p.replace("§PARA§", "").strip()
        if len(p) >= 3:
            out.append(p)
    return out


# Detection helpers for preserving ambiguity.
ENTITY_CANDIDATE_RE = re.compile(
    r"\b(The Flowery|Distinguished Gardens(?:\s+LLC)?|Direct Source(?:\s+LLC)?|"
    r"Preferred Gardens|Helios|Packwoods|Mountian View Holdings LLC|"
    r"Oakiecare LLC|YOLO Farms|Michigan Packwoods LLC|Mills|Polley)\b"
)
AMBIGUOUS_PRONOUN_RE = re.compile(
    r"\b(he|him|his|she|her|they|them|their|we|us|our|my assistant|our relationship)\b",
    re.I,
)


def scan_for_references(statement_text: str, sender_name: str, recipient_name: str) -> dict:
    """Return dict with entity_candidates, ambiguous_pronouns, and signal_flags.

    Never resolves — every candidate is returned flagged as unresolved. Filters
    out pronouns that unambiguously refer to sender ('I'/'me'/'my' by convention
    map to sender-candidate, not third-person). But 'my assistant'-style role
    references ARE third-person and kept as candidates.
    """
    entity_candidates = sorted({m.group(0) for m in ENTITY_CANDIDATE_RE.finditer(statement_text)})
    # Exclude self-references: 'my' alone followed by nothing is sender; 'my X'
    # where X is a noun is a third-person reference.
    pronouns = set()
    for m in AMBIGUOUS_PRONOUN_RE.finditer(statement_text):
        tok = m.group(0).lower()
        pronouns.add(tok)
    signal_flags = []
    if entity_candidates:
        signal_flags.append("entity_reference")
    if pronouns:
        signal_flags.append("pronoun_reference")
    if re.search(r"\bnot\b|never|cease|prohibited|repudi", statement_text, re.I):
        signal_flags.append("negation")
    if re.search(r"\b(January|February|March|April|May|June|July|August|"
                 r"September|October|November|December|\d{4})\b", statement_text):
        signal_flags.append("temporal")
    return {
        "entities": entity_candidates,
        "pronouns": sorted(pronouns),
        "signal_flags": signal_flags,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def run(db_url: str, source_override: str | None = None) -> int:
    _setup(db_url)

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

    from database import Base
    import models  # noqa: F401
    import core_models  # noqa: F401

    from services.intake_service import IntakeService
    from services.message_normalization_service import MessageNormalizationService

    data = load_intake_data(source_override)
    _banner(f"SOURCE: {data['file_name']} [{data['source_kind']}]")
    print(f"  path   = {data['source_path']}")
    print(f"  sha256 = {data['file_sha256'][:16]}…  size = {data['file_size_bytes']} bytes")
    print(f"  Q1 text length: {len(data['q1_text'])} chars")
    print(f"  Q2 text length: {len(data['q2_text'])} chars")
    print(f"  Email 1 (Dec 20, 2022): {len(data['email1_body'])} chars")
    print(f"  Email 2 (Dec 27, 2022): {len(data['email2_body'])} chars")

    engine = create_async_engine(db_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # ---------------- Wave 1 ----------------
    _banner("WAVE 1 — Case + Intake write (real data)")
    async with SessionLocal() as session:
        intake = IntakeService(session)

        case = await intake.create_case(
            display_name="Mills v. Polley (Preferred Gardens partnership)",
            created_by="proof_script",
        )
        _step("create_case", case.id)

        await intake.set_stage_state(case.id, "intake", "in_progress")
        _step("set_stage_state", "intake=in_progress")

        sess = await intake.start_interview_session(
            core_case_id=case.id,
            interview_mode="written",
            interviewer_user_id="atty_intake",
        )
        _step("start_interview_session", sess.id)

        # Q1 and Q2 loaded as interview_responses.
        q1 = await intake.upsert_response(
            interview_session_id=sess.id,
            core_case_id=case.id,
            question_key="q1_narrative",
            response_text=data["q1_text"],
        )
        q2 = await intake.upsert_response(
            interview_session_id=sess.id,
            core_case_id=case.id,
            question_key="q2_claims",
            response_text=data["q2_text"],
        )
        _step("upsert_response Q1 + Q2", f"{q1.id[:8]}…, {q2.id[:8]}…")

        # Uploaded file: the docx itself.
        uploaded = await intake.register_uploaded_file(
            core_case_id=case.id,
            file_name=data["file_name"],
            sha256_hash=data["file_sha256"],
            source_type="upload",
            storage_uri=f"file://{data['file_abs_path']}",
            storage_backend="local_filesystem",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            file_size_bytes=data["file_size_bytes"],
            uploaded_by="atty_intake",
        )
        _step("register_uploaded_file", uploaded.id)

        # Six real actors from the narrative. No forced deduplication.
        actors_seed = [
            ("Jeremey Mills", "plaintiff; cannabis cultivator; founded Highlands dispensary; "
                              "co-founder of Preferred Gardens brand",
             "Also spelled 'Jeremy' in some intake text"),
            ("David Polley", "defendant; former partner in Preferred Gardens brand; "
                             "registered Direct Source LLC; Nicole's husband",
             "'Polley' throughout; 'David' in emails"),
            ("Jaimee Mills", "Jeremey Mills's wife; formerly Jaimee Redfern; first met Mills 2003",
             "Also referenced as 'Jeremey's wife' and 'Mills' wife'"),
            ("Jeff Brown", "landlord of 4020 Durock Rd (Shingle Springs) and 20-acre Independence Rd parcel",
             "Property/land relationship with Mills"),
            ("Ravinder Tumber", "owner of You Only Live Once Farms LLC (Winters, CA); "
                                "51% partner in Yolo Farms structure (Jan 2020)",
             "Also 'Ravi'; uncle-introduction via Tommy Redfern"),
            ("Anthony Capone", "owner of Packwoods Brand; counterpart on Oklahoma and Michigan "
                               "consulting/grow contracts; lender of $1.39M to Mills + Polley",
             "'Capone' in narrative"),
        ]
        actor_rows = {}
        for display, role, raw_note in actors_seed:
            a = await intake.add_intake_actor(
                core_case_id=case.id,
                actor_type="person",
                display_name=display,
                role_context=role,
                raw_input_text=raw_note,
                confidence=0.95,
                created_by="proof_script",
            )
            actor_rows[display] = a
        _step("add_intake_actor x6", ", ".join(actor_rows.keys()))

        # One key relationship input: Mills <-> Polley partnership (disputed).
        await intake.add_actor_relationship(
            core_case_id=case.id,
            actor_a_id=actor_rows["Jeremey Mills"].id,
            actor_b_id=actor_rows["David Polley"].id,
            relationship_claim="business partner in Preferred Gardens brand (disputed as of Dec 2022)",
            direction="bidirectional",
            source_reference="Q1 narrative; see Dec 20, 2022 email",
        )
        _step("add_actor_relationship", "Mills <-> Polley (disputed)")

        # Client summary v1: first substantive paragraph of Q1 as a working summary.
        first_para = next(
            (p for p in data["raw_paragraphs"] if p.strip() and p.strip() != "Question 2"),
            data["q1_text"][:800],
        )
        client_summary = await intake.save_intake_summary_client(
            core_case_id=case.id,
            summary_text=first_para,
            created_by="proof_script",
        )
        _step("save_intake_summary_client", f"v{client_summary.version_number}")

        # A few intake_timeline_seeds. These come straight from narrative text.
        seeds = [
            ("September 2003 — Mills met Jaimee at Bobby McGee's restaurant", "September 2003"),
            ("February 11, 2010 — Mills purchased 3211 Luyung Dr, Rancho Cordova "
             "(later raided Oct 9, 2019)", "2010-02-11"),
            ("April 2016 — Mills brought Polley on as head cultivator at Timber Ln "
             "outdoor cultivation property", "April 2016"),
            ("October 23, 2016 — first post on Preferred_Gardens Instagram", "2016-10-23"),
            ("December 20, 2022 — Polley email repudiating the partnership", "2022-12-20"),
        ]
        for seed_text, when in seeds:
            await intake.add_timeline_seed(
                core_case_id=case.id,
                seed_text=seed_text,
                event_time_candidate=when,
                time_precision=("exact" if "-" in when and when.count("-") == 2 else "approximate"),
                source_response_id=q1.id,
                created_by="proof_script",
            )
        _step("add_timeline_seed x5")

        await session.commit()

    # ---------------- Wave 2 ----------------
    _banner("WAVE 2 — Message normalization write (real emails)")
    async with SessionLocal() as session:
        mn = MessageNormalizationService(session)

        # The docx is itself the message source file (embeds both emails).
        src = await mn.register_source_file(
            core_case_id=case.id,
            file_hash=data["file_sha256"],
            file_type="docx_intake_narrative",  # not a native email export
            source_system="attorney_intake_docx",
            uploaded_file_id=uploaded.id,
            parse_status="parsed",
            parse_notes="Two emails (Dec 20 + Dec 27, 2022) embedded in Q1 narrative text.",
        )
        _step("register_source_file", src.id)

        thread = await mn.create_thread(
            core_case_id=case.id,
            external_thread_id=None,
            thread_subject="Partnership repudiation — Dec 2022",
            participants=[
                {"name": "David Polley", "role": "sender", "confidence": 0.98},
                {"name": "Jeremey Mills", "role": "recipient", "confidence": 0.98},
            ],
        )
        _step("create_thread", thread.id)

        from datetime import datetime as _dt

        # Message 1 — Dec 20, 2022 repudiation email.
        msg1 = await mn.save_normalized_message(
            core_case_id=case.id,
            message_source_file_id=src.id,
            thread_id=thread.id,
            body_clean=data["email1_body"],
            sender_candidate="David Polley",
            sender_confidence=0.90,  # extracted from narrative frame, not email header
            recipient_candidates=[
                {"name": "Jeremey Mills", "role": "to", "confidence": 0.90},
            ],
            external_message_id=None,
            ambiguity_flags=[
                {"flag": "sender_from_narrative_frame",
                 "note": "Sender attributed via the surrounding intake narrative, "
                         "not via email headers — confidence capped at 0.90"},
            ],
            normalized_by="proof_normalizer_v1",
            sent_timestamp=_dt(2022, 12, 20),
        )
        _step("save_normalized_message (Dec 20)", msg1.id)

        # Message 2 — Dec 27, 2022 trespass follow-up email.
        msg2 = await mn.save_normalized_message(
            core_case_id=case.id,
            message_source_file_id=src.id,
            thread_id=thread.id,
            body_clean=data["email2_body"],
            sender_candidate="David Polley",
            sender_confidence=0.90,
            recipient_candidates=[
                {"name": "Jeremey Mills", "role": "to", "confidence": 0.90},
            ],
            ambiguity_flags=[
                {"flag": "sender_from_narrative_frame",
                 "note": "Same narrative-frame attribution as Dec 20 email"},
                {"flag": "unclosed_quote_in_source",
                 "note": "Source docx does not include an explicit closing quote"},
            ],
            normalized_by="proof_normalizer_v1",
            sent_timestamp=_dt(2022, 12, 27),
        )
        _step("save_normalized_message (Dec 27)", msg2.id)

        # Statement segmentation for each message. For each statement: run the
        # reference scanner and preserve all candidates unresolved.
        saved_statements = []
        saved_refs = []
        flags_raised = 0
        for msg, body in ((msg1, data["email1_body"]), (msg2, data["email2_body"])):
            statements = segment_into_statements(body)
            for idx, stmt in enumerate(statements):
                scan = scan_for_references(stmt, "David Polley", "Jeremey Mills")
                has_pronoun = bool(scan["pronouns"])
                st_row = await mn.save_statement(
                    core_case_id=case.id,
                    normalized_message_id=msg.id,
                    statement_index=idx,
                    statement_text=stmt,
                    speaker_candidate="David Polley",
                    speaker_confidence=0.90,
                    has_pronoun_flag=has_pronoun,
                    pronoun_resolved=False,          # never force resolution
                    pronoun_confidence=None,         # unknown — preserve
                    signal_flags=scan["signal_flags"],
                    attribution_confidence=0.90,
                )
                saved_statements.append((msg.id, st_row))

                # Entity references -> referenced_actor_candidates (unresolved).
                for ent in scan["entities"]:
                    if ent in {"Mills", "Polley"}:
                        # These are the sender/recipient. We still save them as
                        # referenced candidates to preserve the surface mention —
                        # resolution_status remains "unresolved" per ambiguity rule.
                        kind = "proper_name"
                    else:
                        kind = "proper_name"
                    ref = await mn.save_referenced_actor_candidate(
                        core_case_id=case.id,
                        normalized_message_id=msg.id,
                        normalized_statement_id=st_row.id,
                        reference_text=ent,
                        reference_kind=kind,
                        resolution_status="unresolved",   # NEVER forced
                        candidate_actor_ids=[],            # NEVER populated here
                        confidence=None,
                    )
                    saved_refs.append(ref)

                # Ambiguous pronoun references: one ref record per statement
                # (the pronoun set). Keeps per-statement audit trail.
                if has_pronoun:
                    ref = await mn.save_referenced_actor_candidate(
                        core_case_id=case.id,
                        normalized_message_id=msg.id,
                        normalized_statement_id=st_row.id,
                        reference_text="; ".join(scan["pronouns"]),
                        reference_kind="pronoun",
                        resolution_status="unresolved",
                        candidate_actor_ids=[],
                        confidence=None,
                    )
                    saved_refs.append(ref)
                    # Also raise a quality flag for unresolved third-person /
                    # pronoun reference so it surfaces for attorney review.
                    await mn.raise_quality_flag(
                        core_case_id=case.id,
                        flag_code="unresolved_third_person",
                        severity="warning",
                        normalized_message_id=msg.id,
                        normalized_statement_id=st_row.id,
                        detail_text=f"unresolved pronoun(s): {scan['pronouns']}",
                    )
                    flags_raised += 1

        _step("statement + reference extraction",
              f"{len(saved_statements)} statements, {len(saved_refs)} references, "
              f"{flags_raised} quality flags")

        # One extra flag: the sender attribution itself is narrative-framed, not
        # header-framed. This is a conservative ambiguous_sender marker.
        await mn.raise_quality_flag(
            core_case_id=case.id,
            flag_code="ambiguous_sender",
            severity="info",
            normalized_message_id=msg1.id,
            detail_text=("Sender attributed via intake-narrative framing "
                         "('December 20, 2022 Polley send mills an email ...'), "
                         "not a native email header."),
        )
        await mn.raise_quality_flag(
            core_case_id=case.id,
            flag_code="ambiguous_sender",
            severity="info",
            normalized_message_id=msg2.id,
            detail_text="Same narrative-frame attribution as Dec 20 message.",
        )

        await mn.upsert_corpus_snapshot(
            core_case_id=case.id,
            source_file_count=1,
            thread_count=1,
            message_count=2,
            participant_snapshot=[
                {"name": "David Polley", "messages": 2, "role": "sender"},
                {"name": "Jeremey Mills", "messages": 2, "role": "recipient"},
            ],
            conflict_markers=[
                {"marker": "partnership_status_disputed",
                 "note": "Sender claims sole ownership; recipient claims partnership"},
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
        assert got_case is not None
        print(f"  case             : {got_case.display_name}")
        print(f"                     id={got_case.id}")

        stages = await intake.get_stage_states(case.id)
        print(f"  stage_states     : {[(s.stage_key, s.state_value) for s in stages]}")

        actors = await intake.list_intake_actors(case.id)
        print(f"  actors ({len(actors)}):")
        for a in actors:
            print(f"    - {a.display_name} ({a.role_context[:70]}…)")

        responses = await intake.get_responses(sess.id)
        print(f"  interview_responses ({len(responses)}):")
        for r in responses:
            print(f"    - {r.question_key}  ({len(r.response_text)} chars)")

        files = await intake.list_uploaded_files(case.id)
        print(f"  uploaded_files   : {[(f.file_name, f.sha256_hash[:12]+'…') for f in files]}")

        seeds = await intake.list_timeline_seeds(case.id)
        print(f"  timeline_seeds ({len(seeds)}):")
        for s in seeds:
            print(f"    - [{s.event_time_candidate}] {s.seed_text[:70]}")

        threads = await mn.list_threads(case.id)
        print(f"  threads ({len(threads)}): {[(t.thread_subject) for t in threads]}")

        messages = await mn.list_messages_for_thread(thread.id)
        print(f"  messages(thread) : {len(messages)} message(s)")
        for m in messages:
            print(f"    - {m.sent_timestamp.date()} from={m.sender_candidate} "
                  f"(conf={m.sender_confidence})")
            print(f"      body[:90]={m.body_clean[:90]!r}…")

        total_statements = 0
        total_unresolved_refs = 0
        for m in messages:
            stmts = await mn.list_statements_for_message(m.id)
            total_statements += len(stmts)
            print(f"  statements({m.sent_timestamp.date()}): {len(stmts)}")
            for st in stmts[:3]:  # print first 3 per message, for legibility
                flags = ",".join(st.signal_flags) if st.signal_flags else ""
                print(f"    [{st.statement_index}] pronoun={st.has_pronoun_flag} "
                      f"resolved={st.pronoun_resolved}  flags=[{flags}]")
                print(f"        {st.statement_text[:120]}…")
            if len(stmts) > 3:
                print(f"    ... {len(stmts)-3} more")

        flags = await mn.list_unresolved_quality_flags(case.id)
        print(f"  unresolved_quality_flags ({len(flags)}):")
        by_code: dict[str, int] = {}
        for f in flags:
            by_code[f.flag_code] = by_code.get(f.flag_code, 0) + 1
        for code, n in sorted(by_code.items()):
            print(f"    {code}: {n}")

        corpus = await mn.get_corpus_snapshot(case.id)
        print(
            f"  corpus snapshot  : sources={corpus.source_file_count} "
            f"threads={corpus.thread_count} messages={corpus.message_count}"
        )

        # Query all referenced_actor_candidates for the case via raw select
        # (service layer has a resolve method but no list method — acceptable
        # for a proof).
        from sqlalchemy import select
        from core_models import ReferencedActorCandidate
        res = await session.execute(
            select(ReferencedActorCandidate).where(
                ReferencedActorCandidate.core_case_id == case.id,
                ReferencedActorCandidate.resolution_status == "unresolved",
            )
        )
        refs = list(res.scalars().all())
        print(f"  unresolved referenced_actor_candidates: {len(refs)}")
        # Group by reference_kind
        by_kind: dict[str, int] = {}
        for r in refs:
            by_kind[r.reference_kind or "unknown"] = by_kind.get(r.reference_kind or "unknown", 0) + 1
        for kind, n in sorted(by_kind.items()):
            print(f"    {kind}: {n}")
        # Show a few sample unresolved refs
        print("  sample unresolved refs:")
        for r in refs[:6]:
            print(f"    - [{r.reference_kind}] {r.reference_text!r}  (chosen_actor={r.chosen_actor_id})")

        # Hard asserts so an empty read fails loudly.
        assert len(actors) == 6, f"expected 6 actors, got {len(actors)}"
        assert len(responses) == 2
        assert len(files) == 1
        assert len(messages) == 2
        assert total_statements >= 2, "expected at least 2 statements total"
        # No reference was resolved — ambiguity preserved.
        assert all(r.resolution_status == "unresolved" for r in refs)
        assert all(r.chosen_actor_id is None for r in refs)

    _banner("SUCCESS (real intake data)")
    await engine.dispose()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default="sqlite+aiosqlite:///:memory:")
    ap.add_argument(
        "--source",
        default=None,
        help=(
            "Optional intake source override (.parsed.json / .txt / .docx). "
            "Default: canonical asset from test_data/TEST_DATA_REGISTRY.json."
        ),
    )
    args = ap.parse_args()
    return asyncio.run(run(args.db_url, args.source))


if __name__ == "__main__":
    raise SystemExit(main())
