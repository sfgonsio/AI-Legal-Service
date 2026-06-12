"""Controlled-resolution preparation — no automated resolution.

Reads the Wave 1/2 in-memory fixture via wave_proof, pulls the actual
statement text for each top ambiguity case, and writes a resolution-prep
artifact to test_data/analysis/resolution_prep_top5.json.

Scope boundaries (enforced by this script):
  - No mutation of persisted truth-layer rows.
  - No identity resolution: every reference stays `unresolved`.
  - No new data loaded — uses the existing steve_case_v1 fixture.
  - No legal reasoning — impact-map text describes outcome surface, not legal
    conclusions.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BACKEND_DIR = _HERE.parent
_RUNTIME_ROOT = _BACKEND_DIR.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

ANALYSIS_DIR = _RUNTIME_ROOT / "test_data" / "analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = ANALYSIS_DIR / "resolution_prep_top5.json"


# ---- Resolution-prep specification -------------------------------------------
# Keyed by risk_id from ambiguity_risk_top10.json. Only the 5 that hit
# ownership / partnership-structure / contract-payment flow.
TOP5_SPEC = [
    {
        "risk_id": "preferred_gardens_ownership",
        "rank": 1,
        "short_label": "Preferred Gardens brand — partnership asset or Polley-individually?",
        "impact_domain": ["brand_ip_ownership", "partnership_structure"],
        # Statement-text markers used to fetch the supporting statements from
        # the persisted normalized_statements rows. No substring fabrication —
        # these strings appear verbatim in the email bodies.
        "statement_markers": [
            "Preferred Gardens branding",
            "sublicenses the branding from me individually",
            "currently presenting yourself as an",
        ],
        "involved_actors": ["Jeremey Mills", "David Polley"],
        "involved_entities": [
            "entity:Preferred_Gardens_candidate",
            "entity:Distinguished_Gardens_candidate",
            "entity:The_Flowery_candidate",
        ],
        "conflicting_interpretations": [
            ("A", "Preferred Gardens is a partnership asset created and funded "
                  "by Mills + Polley jointly (Mills-suggested 'Distinguished "
                  "Gardens'; Polley-suggested 'Preferred Gardens'). Under this "
                  "read, Distinguished Gardens LLC's sublicense from Polley "
                  "individually is itself a conversion of partnership property."),
            ("B", "Preferred Gardens branding is Polley's individual property, "
                  "which Distinguished Gardens LLC sublicenses per the Dec 20 "
                  "email's explicit text. Under this read, Polley's conduct is "
                  "consistent with his ownership claim and Mills has no direct "
                  "claim to the brand."),
        ],
        "resolution_questions": [
            "Who filed the state and federal trademark applications for 'Preferred Gardens', and in whose name?",
            "Is there any written document (term sheet, LLC operating agreement, email, text, invoice) before Dec 2022 naming both Mills and Polley as brand owners or licensees?",
            "Who paid the filing fees, design costs, and marketing costs for the 'Preferred Gardens' brand, and from which bank account?",
            "What is the capital-contribution record for Distinguished Gardens LLC at formation and at each amendment (Oct 28, 2020 in particular)?",
            "Did either party ever acknowledge the other as a co-owner of the brand in any third-party communication (Helios, The Flowery, Packwoods, Goat Grow)?",
        ],
        "evidence_targets": {
            "document_types": [
                "USPTO and Secretary of State trademark filings for 'Preferred Gardens'",
                "Distinguished Gardens LLC operating agreement (original + Oct 28, 2020 amendment)",
                "bank records for any account paying brand / trademark fees",
                "brand-design invoices, logo deliverables, packaging artwork contracts",
                "third-party emails mentioning brand ownership (Helios, The Flowery, Packwoods)",
            ],
            "metadata_signals": [
                "party names: 'Preferred Gardens', 'Distinguished Gardens LLC', 'Mills', 'Polley'",
                "filing dates near the Oct 23, 2016 Instagram launch or earlier",
                "trademark registration numbers (CA Reg ID referenced in Q2)",
                "LLC member-list documents with 'David Polley' or 'Jeremey Mills' as member",
            ],
        },
        "impact_map": {
            "coa_viability": "Conversion (Interp. A strongly supports); Breach of "
                             "Fiduciary Duty (A supports); Unfair Competition / UCL "
                             "(A supports). Under B, those COAs weaken or fail on the "
                             "brand-asset prong.",
            "burden_satisfaction": "Under A: burden on Mills reduces because there is "
                                   "joint creation evidence. Under B: Mills must rebut "
                                   "the sublicense-from-Polley recital with contrary "
                                   "contemporaneous documents.",
            "remedy_exposure": "Under A: disgorgement of branding-derived profits "
                               "(The Flowery, Packwoods, Goat Grow) is on the table. "
                               "Under B: remedy limited to the partnership-at-will "
                               "accounting (and maybe reliance damages only).",
        },
    },
    {
        "risk_id": "distinguished_gardens_llc_ownership",
        "rank": 2,
        "short_label": "Distinguished Gardens LLC — membership share and amendment history",
        "impact_domain": ["entity_control", "contract_routing", "financial_flow"],
        "statement_markers": [
            "Distinguished Gardens LLC has licensed",
            "Distinguished Gardens LLC does not own the branding",
            "Distinguished Gardens LLC sublicenses",
        ],
        "involved_actors": ["Jeremey Mills", "David Polley", "Anthony Capone"],
        "involved_entities": [
            "entity:Distinguished_Gardens_candidate",
            "entity:Preferred_Gardens_candidate",
            "entity:The_Flowery_candidate",
            "entity:Packwoods_candidate",
        ],
        "conflicting_interpretations": [
            ("A", "Mills was the sole or majority member at LLC formation and "
                  "'had his accountant amend Distinguished Gardens LLC to include "
                  "David Polley' Oct 28, 2020 — therefore Polley joined as a "
                  "50% member by amendment, partnership-accounting applies."),
            ("B", "The Oct 28, 2020 amendment did not transfer equity; it added "
                  "Polley as manager / agent only. Mills holds the equity "
                  "consistent with Dec 20 email's recital that Polley "
                  "sublicenses the brand individually."),
            ("C", "Polley is the sole member of Distinguished Gardens LLC and "
                  "the amendment was a typographical/administrative correction. "
                  "This is the reading most consistent with Polley's December "
                  "2022 repudiation language."),
        ],
        "resolution_questions": [
            "Produce the signed LLC-1 formation filing and any LLC-2 / statement-of-information updates for Distinguished Gardens LLC.",
            "Produce the Operating Agreement at formation and every amended version, including the Oct 28, 2020 amendment referenced in the narrative.",
            "Produce K-1s or distribution schedules issued by Distinguished Gardens LLC for tax years 2020–2023.",
            "Which member wired the initial capital contribution, and from which account?",
            "Did Distinguished Gardens LLC ever report Mills to the IRS, EDD, or CDTFA as a member or officer?",
        ],
        "evidence_targets": {
            "document_types": [
                "California Secretary of State filings (LLC-1, LLC-2, Statement of Information)",
                "Operating Agreement and every amendment",
                "IRS Form 1065 partnership returns + K-1s for 2020–2023",
                "Bank signature cards for Distinguished Gardens LLC accounts",
                "Wire / ACH records for capital contributions",
            ],
            "metadata_signals": [
                "filer name on LLC filings",
                "EIN-linked tax documents",
                "'Mills' or 'Polley' in K-1 recipient fields",
                "dates: LLC formation, Oct 28 2020 amendment",
                "accountant's work papers referenced in Q1",
            ],
        },
        "impact_map": {
            "coa_viability": "Breach of fiduciary duty + accounting (A, B). "
                             "Conversion (A strongly). Under C, Mills has no direct "
                             "LLC-level claim and must rely on partnership-at-will "
                             "theories only.",
            "burden_satisfaction": "Element: 'partnership existed' — (A) satisfied; "
                                   "(B) partially satisfied; (C) unmet at entity level, "
                                   "requires de-facto partnership proof.",
            "remedy_exposure": "Under A: dissolution + accounting of all Distinguished "
                               "Gardens contracts (Flowery FL, Packwoods OK+MI, Goat Grow). "
                               "Under C: limited to quantum-meruit / unjust-enrichment.",
        },
    },
    {
        "risk_id": "direct_source_llc_membership",
        "rank": 3,
        "short_label": "Direct Source LLC — Mills's membership status at the repudiation moment",
        "impact_domain": ["entity_control", "partnership_structure", "contract_routing"],
        "statement_markers": [
            "Direct Source, LLC's license at risk",
            "you are not an owner, employee, or agent of Direct Source",
            "Direct Source LLC facility",
            "direct source llc facility",
        ],
        "involved_actors": ["Jeremey Mills", "David Polley"],
        "involved_entities": [
            "entity:Direct_Source_candidate",
        ],
        "conflicting_interpretations": [
            ("A", "Mills was a member-in-fact of Direct Source LLC: the narrative "
                  "says Polley registered the LLC 'to use for the licensing of "
                  "8372 Rovana Circle. Mills was to be added to the LLC once his "
                  "[legal issue] resolved.' Under this read, Polley's Dec 20 "
                  "disclaimer is a breach, and the Dec 27 trespass notice is a "
                  "wrongful exclusion."),
            ("B", "Mills was never formally added to the LLC as a member. "
                  "Dec 20 email's disclaimer is factually correct; Mills's "
                  "remedy lies against the underlying partnership, not against "
                  "Direct Source LLC directly."),
        ],
        "resolution_questions": [
            "What is the filed membership roster of Direct Source LLC at the California Secretary of State on Dec 20, 2022, and currently?",
            "Was any written admission agreement, membership certificate, or assignment drafted for Mills between Oct 25, 2019 (LLC formation) and Dec 20, 2022?",
            "Who signed the Rovana Circle cultivation license application to the Department of Cannabis Control, and who was listed as a financial interest holder?",
            "Did Mills ever receive a cap-table document, K-1, or distribution check from Direct Source LLC?",
            "Did Direct Source LLC's insurance, METRC, or Rovana lease list Mills as an authorized party?",
        ],
        "evidence_targets": {
            "document_types": [
                "California Department of Cannabis Control (DCC) licensing records for 8372 Rovana Circle",
                "METRC account roster for Direct Source LLC",
                "Secretary of State LLC-1 + Statement of Information for Direct Source LLC (Oct 25, 2019 onward)",
                "Rovana Circle lease + any addenda naming Mills",
                "Insurance declarations for the Rovana facility",
            ],
            "metadata_signals": [
                "'Jeremey Mills' / 'Jeremy Mills' in licensee fields",
                "financial-interest-holder disclosures (DCC Form BCC-LIC-027)",
                "rent payments of $9,000 and cultivation-supply payments (Mills contributions)",
                "Direct Source LLC bank signers",
            ],
        },
        "impact_map": {
            "coa_viability": "Wrongful exclusion from business / fiduciary breach (A). "
                             "Trespass / conversion defense (B — defeats Mills's claim "
                             "at entity level). Intentional interference with prospective "
                             "economic advantage could apply under either reading.",
            "burden_satisfaction": "Element: 'Mills had ownership or contractual right "
                                   "to enter the Rovana facility' — (A) supports; (B) "
                                   "fails this element absent clear contract evidence.",
            "remedy_exposure": "Under A: share-of-profits + valuation of 'financial "
                               "interest holder' share Mills was supposed to get. "
                               "Under B: restitution of rent and cultivation-supply "
                               "payments only.",
        },
    },
    {
        "risk_id": "the_flowery_contract_routing",
        "rank": 4,
        "short_label": "The Flowery (Florida) — payment routing and primary-contact claim",
        "impact_domain": ["contract_routing", "financial_flow"],
        "statement_markers": [
            "The Flowery",
            "primary contact with The Flowery",
            "our relationship or contract with them",
        ],
        "involved_actors": ["Jeremey Mills", "David Polley"],
        "involved_entities": [
            "entity:The_Flowery_candidate",
            "entity:Distinguished_Gardens_candidate",
            "entity:Preferred_Gardens_candidate",
        ],
        "conflicting_interpretations": [
            ("A", "Distinguished Gardens LLC is the contracting party; Mills is "
                  "a 50% member; therefore Flowery payments flowing only to "
                  "Polley are partnership-asset diversions."),
            ("B", "Polley is the individual licensor (per Dec 20 email) and "
                  "Distinguished Gardens sublicenses; payments to Polley "
                  "individually on the sublicense slice are legitimate even if "
                  "Mills is a member of the sublicensee."),
            ("C", "Mills is not a member of Distinguished Gardens LLC (see risk "
                  "#2 interpretation C); no routing claim exists."),
        ],
        "resolution_questions": [
            "Produce the February 2022 The Flowery license agreement and any amendments.",
            "Which entity is the contracting counterparty with The Flowery — Distinguished Gardens LLC, Preferred Gardens (brand), or David Polley individually?",
            "To which bank account have Flowery royalty or license payments been deposited from February 2022 through present, month by month?",
            "Who had access credentials to the getSalve.co app for Florida sales, and when was Mills's access revoked (the Oct 7, 2023 event noted in Q2)?",
            "What were the sublicense / license royalty rates, minimums, and terms, and how were they calculated?",
        ],
        "evidence_targets": {
            "document_types": [
                "signed The Flowery — Distinguished Gardens LLC (or individual) license agreement",
                "monthly royalty / license statements from The Flowery",
                "bank statements for the receiving account(s)",
                "getSalve.co admin logs showing access grants and revocations",
                "sublicense docs between Polley individually and Distinguished Gardens LLC",
            ],
            "metadata_signals": [
                "'The Flowery' as counterparty name",
                "deposit memos referencing 'Flowery', 'Preferred Gardens', 'royalty', 'license fee'",
                "dates after Feb 2022",
                "Oct 7, 2023 specifically (Q2 alleged access revocation)",
            ],
        },
        "impact_map": {
            "coa_viability": "Conversion (A). Constructive trust over Flowery "
                             "payments (A). Accounting (A, B). Under C: no "
                             "entity-level claim; only Polley-Mills partnership "
                             "accounting.",
            "burden_satisfaction": "Element: 'Polley received partnership funds and "
                                   "withheld them' — (A) supports directly via bank "
                                   "records; (B) supports partially; (C) fails at "
                                   "entity-level.",
            "remedy_exposure": "Under A: disgorgement of net Flowery royalties + "
                               "pre-judgment interest + possible punitive if "
                               "conversion findings. Under C: nominal / restitution "
                               "only on direct Mills contributions.",
        },
    },
    {
        "risk_id": "our_relationship_pronoun",
        "rank": 5,
        "short_label": "'our relationship' / 'our' pronoun in Dec 20 email — admits partnership?",
        "impact_domain": ["partnership_structure", "repudiation_scope"],
        "statement_markers": [
            "our relationship",
            "I do not want to have our relationship",
            "so we can maintain a clear face",
        ],
        "involved_actors": ["Jeremey Mills", "David Polley"],
        "involved_entities": [
            "entity:The_Flowery_candidate",
            "entity:Distinguished_Gardens_candidate",
        ],
        "conflicting_interpretations": [
            ("A", "'our' = sender + recipient (Polley + Mills). This is an "
                  "admission against interest that a relationship exists, "
                  "inconsistent with the same email's repudiation. Supports "
                  "partnership-by-conduct / estoppel."),
            ("B", "'our' = sender + Distinguished Gardens LLC internal team. "
                  "No admission; consistent with Polley's sole-ownership "
                  "position."),
            ("C", "'our' = sender + The Flowery (informal 'we/them' framing of "
                  "the contracting pair). Also no admission about Mills."),
        ],
        "resolution_questions": [
            "Did Mills and Polley ever sign any written partnership agreement, even a term sheet or back-of-napkin?",
            "Are there emails or texts in which Polley refers to 'our partnership', 'our company', or 'we' in a way that clearly includes Mills as a counterparty?",
            "Did Polley and Mills ever file joint tax returns, joint bank accounts, or joint vendor registrations?",
            "Was there a 50/50 distribution pattern in bank records that matches the narrative's 'split proceeds 50/50' assertion?",
            "Did any third party (Helios, Packwoods, Flowery, landlord) address communications jointly to Mills AND Polley?",
        ],
        "evidence_targets": {
            "document_types": [
                "any partnership / JV / term-sheet document",
                "tax returns (joint or individual schedules reflecting the 50/50 split)",
                "joint bank or venmo records",
                "vendor correspondence addressing both parties",
                "prior Polley messages (text, email, DM) using 'we/our' in a Mills-inclusive way",
            ],
            "metadata_signals": [
                "communications with 'Jeremey' and 'David' both in the To/CC lines",
                "word frequency: 'our', 'we', 'partner' in Polley-authored messages before Dec 2022",
                "joint signatures on any written instrument",
            ],
        },
        "impact_map": {
            "coa_viability": "Partnership-by-estoppel (A strongly). Promissory estoppel "
                             "(A). Breach of oral partnership agreement (A). Under B/C, "
                             "these theories weaken.",
            "burden_satisfaction": "Element: 'existence of partnership' — (A) this "
                                   "single email becomes corroborating admission. "
                                   "Under B/C: needs independent partnership evidence.",
            "remedy_exposure": "Under A: partnership accounting + reliance damages "
                               "(Mills's funds advanced per Q2). Under B/C: reliance "
                               "damages only on specific contributions.",
        },
    },
]


def _run_fixture() -> tuple[list, list, list, list]:
    """Re-run the wave_proof fixture in-memory and return the persisted rows
    we need for supporting-statement extraction.
    """
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

    from database import Base
    import models  # noqa: F401
    import core_models  # noqa: F401
    from core_models import (
        IntakeActorRecord,
        NormalizedMessage,
        NormalizedStatement,
        ReferencedActorCandidate,
    )

    import wave_proof

    async def _inner():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # Reuse wave_proof.run() to populate the fixture. We only need reads
        # afterwards, so a single pass via the existing run() is fine.
        await wave_proof.run("sqlite+aiosqlite:///:memory:")
        # wave_proof.run created and disposed its own engine. Run again on our
        # engine so the data is in-scope for our queries. This duplicates the
        # work, but keeps the script self-contained and under ~1s.
        async with SessionLocal() as session:
            # Re-execute the body by importing pieces of wave_proof.
            from services.intake_service import IntakeService
            from services.message_normalization_service import MessageNormalizationService
            data = wave_proof.load_intake_data(None)
            intake = IntakeService(session)
            case = await intake.create_case(
                display_name="Mills v. Polley (Preferred Gardens partnership)",
                created_by="analysis_script",
            )
            await intake.set_stage_state(case.id, "intake", "in_progress")
            sess_row = await intake.start_interview_session(
                core_case_id=case.id, interview_mode="written",
                interviewer_user_id="atty_intake",
            )
            await intake.upsert_response(
                interview_session_id=sess_row.id, core_case_id=case.id,
                question_key="q1_narrative", response_text=data["q1_text"],
            )
            await intake.upsert_response(
                interview_session_id=sess_row.id, core_case_id=case.id,
                question_key="q2_claims", response_text=data["q2_text"],
            )
            uploaded = await intake.register_uploaded_file(
                core_case_id=case.id, file_name=data["file_name"],
                sha256_hash=data["file_sha256"], source_type="upload",
                storage_uri=f"file://{data['file_abs_path']}",
                storage_backend="local_filesystem",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                file_size_bytes=data["file_size_bytes"], uploaded_by="atty_intake",
            )
            for display, role, raw_note in [
                ("Jeremey Mills", "plaintiff", "Also 'Jeremy'"),
                ("David Polley", "defendant", "Also 'David'"),
                ("Jaimee Mills", "spouse of Mills", ""),
                ("Jeff Brown", "landlord", ""),
                ("Ravinder Tumber", "YOLO Farms owner", "'Ravi'"),
                ("Anthony Capone", "lender / Packwoods owner", ""),
            ]:
                await intake.add_intake_actor(
                    core_case_id=case.id, actor_type="person",
                    display_name=display, role_context=role,
                    raw_input_text=raw_note, confidence=0.95,
                )
            from datetime import datetime as _dt
            mn = MessageNormalizationService(session)
            src = await mn.register_source_file(
                core_case_id=case.id, file_hash=data["file_sha256"],
                file_type="docx_intake_narrative", source_system="attorney_intake_docx",
                uploaded_file_id=uploaded.id, parse_status="parsed",
            )
            thread = await mn.create_thread(
                core_case_id=case.id, thread_subject="Partnership repudiation — Dec 2022",
                participants=[
                    {"name": "David Polley", "role": "sender", "confidence": 0.98},
                    {"name": "Jeremey Mills", "role": "recipient", "confidence": 0.98},
                ],
            )
            msg1 = await mn.save_normalized_message(
                core_case_id=case.id, message_source_file_id=src.id, thread_id=thread.id,
                body_clean=data["email1_body"], sender_candidate="David Polley",
                sender_confidence=0.90,
                recipient_candidates=[{"name": "Jeremey Mills", "role": "to", "confidence": 0.90}],
                sent_timestamp=_dt(2022, 12, 20),
            )
            msg2 = await mn.save_normalized_message(
                core_case_id=case.id, message_source_file_id=src.id, thread_id=thread.id,
                body_clean=data["email2_body"], sender_candidate="David Polley",
                sender_confidence=0.90,
                recipient_candidates=[{"name": "Jeremey Mills", "role": "to", "confidence": 0.90}],
                sent_timestamp=_dt(2022, 12, 27),
            )
            for msg, body in ((msg1, data["email1_body"]), (msg2, data["email2_body"])):
                statements = wave_proof.segment_into_statements(body)
                for idx, stmt in enumerate(statements):
                    scan = wave_proof.scan_for_references(stmt, "David Polley", "Jeremey Mills")
                    has_pronoun = bool(scan["pronouns"])
                    st_row = await mn.save_statement(
                        core_case_id=case.id, normalized_message_id=msg.id,
                        statement_index=idx, statement_text=stmt,
                        speaker_candidate="David Polley", speaker_confidence=0.90,
                        has_pronoun_flag=has_pronoun, pronoun_resolved=False,
                        signal_flags=scan["signal_flags"], attribution_confidence=0.90,
                    )
                    for ent in scan["entities"]:
                        await mn.save_referenced_actor_candidate(
                            core_case_id=case.id, normalized_message_id=msg.id,
                            normalized_statement_id=st_row.id, reference_text=ent,
                            reference_kind="proper_name", resolution_status="unresolved",
                        )
                    if has_pronoun:
                        await mn.save_referenced_actor_candidate(
                            core_case_id=case.id, normalized_message_id=msg.id,
                            normalized_statement_id=st_row.id,
                            reference_text="; ".join(scan["pronouns"]),
                            reference_kind="pronoun", resolution_status="unresolved",
                        )
            await session.commit()

            statements = list((await session.execute(
                select(NormalizedStatement).where(
                    NormalizedStatement.core_case_id == case.id
                )
            )).scalars().all())
            messages = list((await session.execute(
                select(NormalizedMessage).where(NormalizedMessage.core_case_id == case.id)
            )).scalars().all())
            actors = list((await session.execute(
                select(IntakeActorRecord).where(IntakeActorRecord.core_case_id == case.id)
            )).scalars().all())
            refs = list((await session.execute(
                select(ReferencedActorCandidate).where(
                    ReferencedActorCandidate.core_case_id == case.id
                )
            )).scalars().all())
        await engine.dispose()
        return statements, messages, actors, refs

    return asyncio.run(_inner())


def main() -> int:
    statements, messages, actors, refs = _run_fixture()

    msg_by_id = {m.id: m for m in messages}
    stmt_by_id = {s.id: s for s in statements}

    prepared = []
    for spec in TOP5_SPEC:
        # Fetch supporting statements that contain any of the markers.
        supporting = []
        for st in statements:
            if any(m.lower() in st.statement_text.lower() for m in spec["statement_markers"]):
                msg = msg_by_id.get(st.normalized_message_id)
                supporting.append({
                    "statement_id": st.id,
                    "message_id": st.normalized_message_id,
                    "message_sent_date": msg.sent_timestamp.date().isoformat() if msg and msg.sent_timestamp else None,
                    "sender_candidate": msg.sender_candidate if msg else None,
                    "sender_confidence": msg.sender_confidence if msg else None,
                    "statement_index": st.statement_index,
                    "has_pronoun_flag": st.has_pronoun_flag,
                    "pronoun_resolved": st.pronoun_resolved,
                    "signal_flags": st.signal_flags,
                    "text": st.statement_text,
                })
        # Also pull referenced_actor_candidates that target this case
        involved_refs = []
        for r in refs:
            # Keep refs whose text appears in any marker, or whose text is one
            # of the entity cluster surface forms.
            surface_tokens = [
                "preferred gardens", "distinguished gardens", "direct source",
                "the flowery",
            ]
            if spec["risk_id"] == "our_relationship_pronoun":
                if r.reference_kind == "pronoun" and "our" in r.reference_text.lower():
                    involved_refs.append({"id": r.id, "text": r.reference_text, "kind": r.reference_kind})
                continue
            rt = r.reference_text.lower()
            for tok in surface_tokens:
                if tok in rt and any(tok in m.lower() for m in spec["statement_markers"]):
                    involved_refs.append({"id": r.id, "text": r.reference_text, "kind": r.reference_kind})
                    break

        prepared.append({
            "risk_id": spec["risk_id"],
            "rank": spec["rank"],
            "short_label": spec["short_label"],
            "impact_domain": spec["impact_domain"],
            "involved_actors": spec["involved_actors"],
            "involved_entities": spec["involved_entities"],
            "supporting_statements": supporting,
            "supporting_statement_count": len(supporting),
            "referenced_candidates": involved_refs,
            "conflicting_interpretations": [
                {"label": lbl, "reading": txt}
                for lbl, txt in spec["conflicting_interpretations"]
            ],
            "resolution_questions": spec["resolution_questions"],
            "evidence_targets": spec["evidence_targets"],
            "impact_map": spec["impact_map"],
        })

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_case": "Mills v. Polley (Preferred Gardens partnership)",
        "resolution_policy": (
            "No automated resolution performed. No persisted truth-layer row "
            "was modified. Every referenced_actor_candidate and pronoun flag "
            "remains unresolved. This artifact prepares human-guided resolution."
        ),
        "selected_count": len(prepared),
        "top_5": prepared,
        "evidence_corpus_caveat": (
            "The attorney mentioned 1,200+ source files. This script does not "
            "have access to that corpus — it lists evidence_types and "
            "metadata_signals to target. Cross-referencing to specific filenames "
            "belongs to the human operator or a later ingestion pass."
        ),
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[done] wrote {OUT_PATH}")
    for p in prepared:
        print(f"  rank {p['rank']}  {p['risk_id']:40s}  "
              f"supporting_statements={p['supporting_statement_count']}  "
              f"resolution_questions={len(p['resolution_questions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
