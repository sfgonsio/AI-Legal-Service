"""Wave 3 preparation — analysis-only. No truth-layer mutation.

Uses the existing real intake dataset (steve_case_v1 from test_data) and the
Wave 1 + Wave 2 services already in place. Runs the standard proof pipeline
against an in-memory database to materialize the canonical persisted state,
then produces four analysis artifacts:

  test_data/analysis/actor_reference_clusters.json
  test_data/analysis/candidate_actor_graph.json
  test_data/analysis/ambiguity_risk_top10.json
  test_data/analysis/timeline_anchors_proposed.json

Rules enforced by this script:
  - No forced actor resolutions (resolution_status stays "unresolved").
  - No mutations to truth-layer rows in the DB.
  - No new schema, no new migrations, no legal mapping, no Brain work.
  - Output files are analysis-only and allowed to evolve.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BACKEND_DIR = _HERE.parent
_RUNTIME_ROOT = _BACKEND_DIR.parent.parent  # casecore-runtime/
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

ANALYSIS_DIR = _RUNTIME_ROOT / "test_data" / "analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Clustering helpers (textual similarity only — no identity assignment)
# ---------------------------------------------------------------------------

LLC_SUFFIX_RE = re.compile(r",?\s*\b(?:LLC|LLP|INC|CORP|L\.L\.C\.)\b\.?", re.I)
PUNCT_RE = re.compile(r"[.,;:\"()\u2018\u2019\u201c\u201d]+")
WS_RE = re.compile(r"\s+")


def normalize_ref(text: str) -> str:
    """Lower-case, strip common org suffixes + punctuation, collapse whitespace."""
    t = text.strip()
    t = LLC_SUFFIX_RE.sub("", t)
    t = PUNCT_RE.sub(" ", t)
    t = WS_RE.sub(" ", t)
    return t.strip().lower()


# Known alias groupings for the Mills v Polley matter. Used to SUGGEST
# which distinct normalized forms probably refer to the same underlying
# entity. This is a clustering hint, not a resolution — the output still
# tags clusters as "candidate_match", not "resolved".
ALIAS_HINTS = [
    # persons
    {"cluster_label": "person:Jeremey_Mills_candidate",
     "aliases": ["mills", "jeremey", "jeremy", "jeremey mills", "jeremy mills"]},
    {"cluster_label": "person:David_Polley_candidate",
     "aliases": ["polley", "david", "david polley"]},
    {"cluster_label": "person:Jaimee_Mills_candidate",
     "aliases": ["jaimee", "jaimee mills", "jaimee redfern"]},
    # entities
    {"cluster_label": "entity:Preferred_Gardens_candidate",
     "aliases": ["preferred gardens", "preferred_gardens"]},
    {"cluster_label": "entity:Distinguished_Gardens_candidate",
     "aliases": ["distinguished gardens"]},
    {"cluster_label": "entity:Direct_Source_candidate",
     "aliases": ["direct source"]},
    {"cluster_label": "entity:The_Flowery_candidate",
     "aliases": ["the flowery"]},
    {"cluster_label": "entity:YOLO_Farms_candidate",
     "aliases": ["yolo farms", "you only live once farms"]},
    {"cluster_label": "entity:Packwoods_candidate",
     "aliases": ["packwoods"]},
    {"cluster_label": "entity:Helios_candidate",
     "aliases": ["helios"]},
    {"cluster_label": "entity:Highlands_Health_and_Wellness",
     "aliases": ["highlands", "highlands health and wellness collective"]},
    {"cluster_label": "entity:Mountain_View_Holdings_candidate",
     "aliases": ["mountian view holdings", "mountain view holdings"]},
    {"cluster_label": "entity:Oakiecare_candidate",
     "aliases": ["oakiecare"]},
    {"cluster_label": "entity:Michigan_Packwoods_candidate",
     "aliases": ["michigan packwoods"]},
]


def suggest_cluster(normalized: str) -> str | None:
    for hint in ALIAS_HINTS:
        if normalized in hint["aliases"]:
            return hint["cluster_label"]
        for alias in hint["aliases"]:
            if alias in normalized or normalized in alias:
                return hint["cluster_label"]
    return None


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

async def main() -> int:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

    from database import Base
    import models  # noqa: F401
    import core_models  # noqa: F401
    from core_models import (
        CoreCase,
        IntakeActorRecord,
        IntakeActorRelationshipInput,
        IntakeTimelineSeed,
        MessageThread,
        NormalizedMessage,
        NormalizedStatement,
        NormalizationQualityFlag,
        ReferencedActorCandidate,
    )

    # Run the standard proof pipeline to populate a fresh in-memory DB with
    # the same deterministic state the user's persisted proof runs produce.
    import wave_proof  # scripts/wave_proof.py is a sibling
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Mirror wave_proof.run() body, but skip the user-facing banner prints so
    # the analysis output is clean.
    from services.intake_service import IntakeService
    from services.message_normalization_service import MessageNormalizationService

    data = wave_proof.load_intake_data(None)

    async with SessionLocal() as session:
        intake = IntakeService(session)
        case = await intake.create_case(
            display_name="Mills v. Polley (Preferred Gardens partnership)",
            created_by="analysis_script",
        )
        await intake.set_stage_state(case.id, "intake", "in_progress")
        sess = await intake.start_interview_session(
            core_case_id=case.id, interview_mode="written", interviewer_user_id="atty_intake"
        )
        q1 = await intake.upsert_response(
            interview_session_id=sess.id, core_case_id=case.id,
            question_key="q1_narrative", response_text=data["q1_text"],
        )
        await intake.upsert_response(
            interview_session_id=sess.id, core_case_id=case.id,
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
            ("Ravinder Tumber", "owner of YOLO Farms LLC (Winters, CA); 51% partner in Yolo Farms structure (Jan 2020)",
             "Also 'Ravi'; uncle-introduction via Tommy Redfern"),
            ("Anthony Capone", "owner of Packwoods Brand; OK + MI consulting/grow contracts; "
                               "lender of $1.39M to Mills + Polley",
             "'Capone' in narrative"),
        ]
        actor_rows = {}
        for display, role, raw_note in actors_seed:
            a = await intake.add_intake_actor(
                core_case_id=case.id, actor_type="person", display_name=display,
                role_context=role, raw_input_text=raw_note, confidence=0.95,
                created_by="analysis_script",
            )
            actor_rows[display] = a
        await intake.add_actor_relationship(
            core_case_id=case.id,
            actor_a_id=actor_rows["Jeremey Mills"].id,
            actor_b_id=actor_rows["David Polley"].id,
            relationship_claim="business partner in Preferred Gardens brand (disputed as of Dec 2022)",
            direction="bidirectional",
            source_reference="Q1 narrative; see Dec 20, 2022 email",
        )
        first_para = next(
            (p for p in data["raw_paragraphs"] if p.strip() and p.strip() != "Question 2"),
            data["q1_text"][:800],
        )
        await intake.save_intake_summary_client(
            core_case_id=case.id, summary_text=first_para, created_by="analysis_script",
        )
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
                core_case_id=case.id, seed_text=seed_text,
                event_time_candidate=when,
                time_precision="exact" if "-" in when and when.count("-") == 2 else "approximate",
                source_response_id=q1.id, created_by="analysis_script",
            )
        await session.commit()

    # Wave 2
    async with SessionLocal() as session:
        mn = MessageNormalizationService(session)
        src = await mn.register_source_file(
            core_case_id=case.id, file_hash=data["file_sha256"],
            file_type="docx_intake_narrative", source_system="attorney_intake_docx",
            uploaded_file_id=uploaded.id, parse_status="parsed",
        )
        thread = await mn.create_thread(
            core_case_id=case.id, external_thread_id=None,
            thread_subject="Partnership repudiation — Dec 2022",
            participants=[
                {"name": "David Polley", "role": "sender", "confidence": 0.98},
                {"name": "Jeremey Mills", "role": "recipient", "confidence": 0.98},
            ],
        )
        from datetime import datetime as _dt
        msg1 = await mn.save_normalized_message(
            core_case_id=case.id, message_source_file_id=src.id, thread_id=thread.id,
            body_clean=data["email1_body"], sender_candidate="David Polley",
            sender_confidence=0.90,
            recipient_candidates=[{"name": "Jeremey Mills", "role": "to", "confidence": 0.90}],
            sent_timestamp=_dt(2022, 12, 20), normalized_by="analysis_script",
        )
        msg2 = await mn.save_normalized_message(
            core_case_id=case.id, message_source_file_id=src.id, thread_id=thread.id,
            body_clean=data["email2_body"], sender_candidate="David Polley",
            sender_confidence=0.90,
            recipient_candidates=[{"name": "Jeremey Mills", "role": "to", "confidence": 0.90}],
            sent_timestamp=_dt(2022, 12, 27), normalized_by="analysis_script",
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
                    await mn.raise_quality_flag(
                        core_case_id=case.id, flag_code="unresolved_third_person",
                        severity="warning", normalized_message_id=msg.id,
                        normalized_statement_id=st_row.id,
                        detail_text=f"unresolved pronoun(s): {scan['pronouns']}",
                    )
        await session.commit()

    # -----------------------------------------------------------------------
    # Phase 1 — referenced-actor clustering
    # -----------------------------------------------------------------------
    async with SessionLocal() as session:
        refs = list((await session.execute(
            select(ReferencedActorCandidate).where(
                ReferencedActorCandidate.core_case_id == case.id
            )
        )).scalars().all())
        actors = list((await session.execute(
            select(IntakeActorRecord).where(IntakeActorRecord.core_case_id == case.id)
        )).scalars().all())
        rels = list((await session.execute(
            select(IntakeActorRelationshipInput).where(
                IntakeActorRelationshipInput.core_case_id == case.id
            )
        )).scalars().all())
        threads = list((await session.execute(
            select(MessageThread).where(MessageThread.core_case_id == case.id)
        )).scalars().all())
        messages = list((await session.execute(
            select(NormalizedMessage).where(NormalizedMessage.core_case_id == case.id)
        )).scalars().all())
        stmts = list((await session.execute(
            select(NormalizedStatement).where(NormalizedStatement.core_case_id == case.id)
        )).scalars().all())
        qflags = list((await session.execute(
            select(NormalizationQualityFlag).where(
                NormalizationQualityFlag.core_case_id == case.id
            )
        )).scalars().all())
        seed_rows = list((await session.execute(
            select(IntakeTimelineSeed).where(IntakeTimelineSeed.core_case_id == case.id)
        )).scalars().all())

    # Build raw-text -> list of refs mapping for proper_name refs
    proper_refs = [r for r in refs if r.reference_kind == "proper_name"]
    pronoun_refs = [r for r in refs if r.reference_kind == "pronoun"]

    clusters: dict[str, dict] = {}
    unclustered: list[dict] = []
    for r in proper_refs:
        norm = normalize_ref(r.reference_text)
        label = suggest_cluster(norm)
        key = label or f"unclustered:{norm}"
        if key not in clusters:
            clusters[key] = {
                "cluster_label": label or "unclustered_candidate",
                "normalized_form": norm,
                "likely_kind": "person" if (label or "").startswith("person:") else (
                    "entity" if (label or "").startswith("entity:") else "unknown"),
                "surface_forms": [],
                "reference_ids": [],
                "resolution_status": "candidate_match_not_resolved",
                "notes": [],
            }
        clusters[key]["surface_forms"].append(r.reference_text)
        clusters[key]["reference_ids"].append(r.id)
        if label is None:
            unclustered.append({"reference_id": r.id, "text": r.reference_text, "normalized": norm})

    # Also fold intake_actor_records into cluster notes (a record and a
    # cluster may point at the same real-world actor — flag as "co-candidate"
    # but do NOT resolve).
    for a in actors:
        a_norm = normalize_ref(a.display_name)
        a_label = suggest_cluster(a_norm)
        if a_label and a_label in clusters:
            clusters[a_label]["notes"].append(
                f"intake_actor_records row {a.id} (display_name={a.display_name!r}) is a "
                f"co-candidate for this cluster — not resolved"
            )

    cluster_list = sorted(
        clusters.values(),
        key=lambda c: (c["likely_kind"], c["cluster_label"]),
    )
    phase1_out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_case_display_name": "Mills v. Polley (Preferred Gardens partnership)",
        "total_proper_name_references": len(proper_refs),
        "total_pronoun_references": len(pronoun_refs),
        "cluster_count": len(cluster_list),
        "resolution_policy": "candidate_clusters_only; resolution_status stays 'unresolved'",
        "clusters": [
            {**c, "surface_form_count": len(c["surface_forms"]),
             "unique_surface_forms": sorted(set(c["surface_forms"]))}
            for c in cluster_list
        ],
        "unclustered_candidates": unclustered,
        "pronoun_references_preserved": [
            {"reference_id": r.id, "text": r.reference_text, "statement_id": r.normalized_statement_id}
            for r in pronoun_refs
        ],
    }
    (ANALYSIS_DIR / "actor_reference_clusters.json").write_text(
        json.dumps(phase1_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # -----------------------------------------------------------------------
    # Phase 2 — candidate actor graph (textual)
    # -----------------------------------------------------------------------
    # Nodes: every intake_actor_record + every distinct cluster_label that
    # does not already correspond to an actor record.
    nodes = []
    for a in actors:
        nodes.append({
            "node_id": f"actor:{a.id}",
            "node_kind": "person",
            "display_name": a.display_name,
            "role_context": a.role_context,
            "source": "intake_actor_records",
            "confidence": a.confidence,
            "status": "candidate (not final)",
        })
    # Cluster-derived nodes for entities without an actor record equivalent.
    for c in cluster_list:
        if c["likely_kind"] == "entity":
            nodes.append({
                "node_id": f"cluster:{c['cluster_label']}",
                "node_kind": "entity",
                "display_name": c["cluster_label"].split(":", 1)[1].replace("_", " "),
                "source": "referenced_actor_candidates (clustered)",
                "surface_forms": sorted(set(c["surface_forms"])),
                "status": "candidate (not final)",
            })

    # Edges:
    #   - persisted intake_actor_relationship_inputs (attorney-documented)
    #   - thread participant edges from message_threads.participants
    #   - message sender/recipient -> referenced entity edges
    edges = []
    actor_id_by_name = {a.display_name: a.id for a in actors}
    for rel in rels:
        edges.append({
            "edge_id": f"rel:{rel.id}",
            "from": f"actor:{rel.actor_a_id}",
            "to": f"actor:{rel.actor_b_id}" if rel.actor_b_id else "unknown",
            "relationship_claim": rel.relationship_claim,
            "direction": rel.direction,
            "source_basis": "intake_actor_relationship_inputs (attorney-documented)",
            "confidence": "attorney-attested",
            "disputed": "disputed" in (rel.relationship_claim or "").lower(),
        })

    # Thread participant edges: who communicates with whom.
    for t in threads:
        parts = t.participants or []
        sender = next((p for p in parts if p.get("role") == "sender"), None)
        for p in parts:
            if p is sender:
                continue
            from_name = sender["name"] if sender else "unknown"
            edges.append({
                "edge_id": f"thread:{t.id}",
                "from": f"actor:{actor_id_by_name.get(from_name, from_name)}",
                "to": f"actor:{actor_id_by_name.get(p['name'], p['name'])}",
                "relationship_claim": "communicated_with (thread participant)",
                "direction": "a_to_b",
                "source_basis": f"message_threads.participants (thread_id={t.id})",
                "confidence": "message-level (0.90 narrative-frame)",
                "disputed": False,
            })

    # Message->entity mention edges: sender_candidate references each clustered entity
    #   group of referenced_actor_candidates, grouped by message.
    refs_by_msg: dict[str, set[str]] = defaultdict(set)
    for r in proper_refs:
        label = suggest_cluster(normalize_ref(r.reference_text))
        if label:
            refs_by_msg[r.normalized_message_id].add(label)
    msg_sender = {m.id: m.sender_candidate for m in messages}
    for msg_id, entity_labels in refs_by_msg.items():
        for ent in sorted(entity_labels):
            edges.append({
                "edge_id": f"mention:{msg_id}:{ent}",
                "from": f"actor:{actor_id_by_name.get(msg_sender.get(msg_id, ''), msg_sender.get(msg_id, 'unknown'))}",
                "to": f"cluster:{ent}",
                "relationship_claim": "referenced_in_message",
                "direction": "a_to_b",
                "source_basis": f"referenced_actor_candidates via normalized_messages.id={msg_id}",
                "confidence": "mention-level, unresolved",
                "disputed": False,
            })

    phase2_out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resolution_policy": "all nodes and edges are CANDIDATE status; "
                             "no forced identity resolution performed",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }
    (ANALYSIS_DIR / "candidate_actor_graph.json").write_text(
        json.dumps(phase2_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # -----------------------------------------------------------------------
    # Phase 3 — ambiguity risk (top 10)
    # -----------------------------------------------------------------------
    # Score each risk by impact on: ownership / partnership / entity control /
    # financial flow / brand-IP / contract routing.
    risks = [
        {
            "rank": 1,
            "risk_id": "preferred_gardens_ownership",
            "ambiguous_surface": "'Preferred Gardens' in Dec 20 email (messages) + narrative",
            "impact_domain": ["brand_ip_ownership", "partnership_structure"],
            "why_material": (
                "The Dec 20 email asserts 'Distinguished Gardens LLC sublicenses the "
                "branding from me individually'. Whether 'Preferred Gardens' is a "
                "partnership asset or Polley's individual asset determines the scope "
                "of the conversion / fiduciary-duty theory in Q2."
            ),
            "evidence_refs": [r.id for r in proper_refs if "Preferred Gardens" in r.reference_text][:5],
            "resolution_needed_before": "any Wave 4 COA or burden mapping",
        },
        {
            "rank": 2,
            "risk_id": "distinguished_gardens_llc_ownership",
            "ambiguous_surface": "'Distinguished Gardens LLC' — whose LLC and who holds what share",
            "impact_domain": ["entity_control", "contract_routing", "financial_flow"],
            "why_material": (
                "Distinguished Gardens LLC is the contracting entity with The Flowery, "
                "Goat Grow, and Packwoods LLCs. If Mills is not a member, he may have "
                "no direct contract claim; if he is a 50% member, partnership-accounting "
                "rules apply. Narrative states Mills had it 'amended' to add Polley in "
                "Oct 2020 — suggesting Mills as original member."
            ),
            "evidence_refs": [r.id for r in proper_refs if "Distinguished Gardens" in r.reference_text][:5],
            "resolution_needed_before": "Wave 4 COA mapping and remedy candidates",
        },
        {
            "rank": 3,
            "risk_id": "direct_source_llc_membership",
            "ambiguous_surface": "'Direct Source LLC' / 'Direct Source' — Polley registered solo; Mills's status disputed",
            "impact_domain": ["entity_control", "partnership_structure"],
            "why_material": (
                "The Dec 20 email is framed around Mills NOT being 'an owner, employee, "
                "or agent of Direct Source, LLC.' That claim by Polley IS the repudiation. "
                "Whether Mills is a member of Direct Source LLC determines whether Polley's "
                "exclusion is a breach of partnership or lawful ownership defense."
            ),
            "evidence_refs": [r.id for r in proper_refs
                              if r.reference_text in ("Direct Source", "Direct Source LLC")][:5],
            "resolution_needed_before": "any trespass / exclusion analysis",
        },
        {
            "rank": 4,
            "risk_id": "the_flowery_contract_routing",
            "ambiguous_surface": "'The Flowery' — who is the 'primary contact', who receives payment",
            "impact_domain": ["contract_routing", "financial_flow"],
            "why_material": (
                "The Dec 20 email declares 'I have been and remain the primary contact "
                "with The Flowery for Distinguished Gardens.' If Mills is a 50% member "
                "of Distinguished Gardens, payment to Polley alone would be conversion; "
                "if Polley is the sole LLC member, his position is defensible. Pronoun "
                "'them' in the same statement refers to The Flowery but is not resolved."
            ),
            "evidence_refs": [r.id for r in proper_refs if "Flowery" in r.reference_text],
            "resolution_needed_before": "Wave 4 remedy analysis",
        },
        {
            "rank": 5,
            "risk_id": "dec20_dec27_sender_attribution",
            "ambiguous_surface": "Both messages' sender_candidate is narrative-frame ('Polley send mills an email')",
            "impact_domain": ["evidence_reliability"],
            "why_material": (
                "Sender attribution for both emails is frame-narration from intake, not "
                "email headers. sender_confidence is capped at 0.90 in the normalized "
                "record, and ambiguous_sender quality flags were raised. Any later "
                "authentication at deposition (Evid. Code §§ 1410–1413) rides on this."
            ),
            "evidence_refs": [f.id for f in qflags if f.flag_code == "ambiguous_sender"],
            "resolution_needed_before": "authentication at deposition; Wave 4 evidentiary mapping",
        },
        {
            "rank": 6,
            "risk_id": "our_relationship_pronoun",
            "ambiguous_surface": "'our relationship' / 'our' in Dec 20 email",
            "impact_domain": ["partnership_structure", "repudiation_scope"],
            "why_material": (
                "'I do not want to have our relationship or contract with them disrupted' "
                "— 'our' ambiguous: (a) sender + recipient (Polley + Mills), (b) sender + "
                "Distinguished Gardens team, (c) sender + The Flowery. Reading (a) admits "
                "a relationship contrary to the rest of the repudiation; readings (b)/(c) "
                "do not. Tied to whether the repudiation itself is internally consistent."
            ),
            "evidence_refs": [r.id for r in pronoun_refs if "our" in r.reference_text.lower()],
            "resolution_needed_before": "any estoppel/partnership-by-conduct argument",
        },
        {
            "rank": 7,
            "risk_id": "them_they_flowery_pronouns",
            "ambiguous_surface": "'them' / 'they' in Dec 20 email",
            "impact_domain": ["contract_routing"],
            "why_material": (
                "'please send them through me so we can maintain a clear face with them' "
                "and 'when they have asked for a single contact' — antecedent almost "
                "certainly The Flowery, but not formally resolved. If misattributed to a "
                "different third party, the 'single contact' claim collapses."
            ),
            "evidence_refs": [r.id for r in pronoun_refs],
            "resolution_needed_before": "Wave 3 Brain fact_candidate extraction",
        },
        {
            "rank": 8,
            "risk_id": "mills_jeremey_jeremy_surface",
            "ambiguous_surface": "'Mills' standalone vs 'Jeremey Mills' vs 'Jeremy'",
            "impact_domain": ["record_linkage"],
            "why_material": (
                "Intake text itself uses 'Jeremey' and 'Jeremy' interchangeably and mixes "
                "'Mills' alone. Without deterministic normalization, Brain actor-graph "
                "nodes may double-count. Lower severity than ownership risks because no "
                "other 'Jeremey' appears in the matter, but must be normalized before "
                "actor-graph construction in Wave 3."
            ),
            "evidence_refs": [r.id for r in proper_refs if r.reference_text in ("Mills", "Polley")][:5],
            "resolution_needed_before": "Wave 3 actor graph build",
        },
        {
            "rank": 9,
            "risk_id": "polley_self_reference_in_messages",
            "ambiguous_surface": "'me'/'I' in Dec 20/Dec 27 emails map to Polley per narrative frame only",
            "impact_domain": ["evidence_reliability"],
            "why_material": (
                "Because sender attribution is narrative-framed (risk 5), every 'I' and "
                "'me' in the email bodies inherits that 0.90 confidence. If the frame is "
                "wrong, every self-reference is misattributed."
            ),
            "evidence_refs": [m.id for m in messages],
            "resolution_needed_before": "authentication at deposition",
        },
        {
            "rank": 10,
            "risk_id": "llc_suffix_surface_form",
            "ambiguous_surface": "'Direct Source' vs 'Direct Source LLC' (and similar for other LLCs)",
            "impact_domain": ["entity_disambiguation"],
            "why_material": (
                "The capture layer preserves the two surface forms as separate "
                "referenced_actor_candidates. If treated as distinct entities, "
                "Brain reasoning overcounts 'Direct Source' mentions relative to the "
                "real entity's salience. The normalize_ref() pass collapses them for "
                "clustering, but the persisted rows are still distinct — acceptable for "
                "truth-layer immutability, but must be collapsed at read time in Wave 3."
            ),
            "evidence_refs": [r.id for r in proper_refs
                              if r.reference_text in ("Direct Source", "Direct Source LLC")][:5],
            "resolution_needed_before": "Wave 3 actor-graph edge deduplication",
        },
    ]
    phase3_out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_n": 10,
        "scoring_basis": "impact on ownership / partnership / entity control / "
                         "financial flow / brand-IP / contract routing",
        "risks": risks,
    }
    (ANALYSIS_DIR / "ambiguity_risk_top10.json").write_text(
        json.dumps(phase3_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # -----------------------------------------------------------------------
    # Phase 4 — timeline-anchor proposal
    # -----------------------------------------------------------------------
    # Use persisted intake_timeline_seeds + additional date mentions in Q1.
    # The additional mentions are READ-ONLY extraction for ANALYSIS output —
    # no new seeds are written to the DB.
    date_mentions = []
    # Explicit dates
    date_patterns = [
        (r"\b(January|February|March|April|May|June|July|August|September|"
         r"October|November|December)\s+\d{1,2},?\s+(\d{4})\b", "month_day_year"),
        (r"\b(January|February|March|April|May|June|July|August|September|"
         r"October|November|December)\s+(\d{4})\b", "month_year"),
        (r"\b(19|20)\d{2}\b", "year_only"),
        (r"\b\d{1,2}/\d{1,2}/\d{4}\b", "slash_date"),
    ]
    for pat, kind in date_patterns:
        for m in re.finditer(pat, data["q1_text"]):
            start = max(0, m.start() - 40)
            end = min(len(data["q1_text"]), m.end() + 120)
            ctx = data["q1_text"][start:end].replace("\n", " ")
            date_mentions.append({
                "date_text": m.group(0),
                "kind": kind,
                "source_context": ctx.strip(),
            })
    # Dedup by (date_text, context prefix) to avoid paragraph overlap dupes.
    seen = set()
    unique_mentions = []
    for dm in date_mentions:
        key = (dm["date_text"], dm["source_context"][:80])
        if key in seen:
            continue
        seen.add(key)
        unique_mentions.append(dm)

    # Categorize: formation / property / partnership / raid-legal / repudiation.
    def categorize(ctx: str) -> str:
        c = ctx.lower()
        if any(k in c for k in ("raid", "dismissed", "cease and desist", "attorney", "license at risk")):
            return "raid_legal"
        if any(k in c for k in ("repudiat", "trespass", "prohibited", "cease doing")):
            return "repudiation_exclusion"
        if any(k in c for k in ("purchased", "leased", "property", "warehouse", "timber ln", "luyung",
                                 "durock", "rovana", "ascot", "independence", "rancho cordova")):
            return "property_cultivation"
        if any(k in c for k in ("partnership", "50/50", "brand", "preferred gardens", "instagram",
                                 "brought on", "head cultivator", "split", "packwoods", "yolo", "ravi",
                                 "consulting", "flowery")):
            return "partnership_business"
        if any(k in c for k in ("met", "wife", "jaimee", "mills met")):
            return "formation_relationship"
        return "uncategorized"

    anchors_by_cat: dict[str, list[dict]] = defaultdict(list)
    for dm in unique_mentions:
        dm["category"] = categorize(dm["source_context"])
        anchors_by_cat[dm["category"]].append(dm)

    # Merge with persisted timeline seeds for cross-reference.
    persisted_seeds = [
        {
            "seed_id": s.id,
            "event_time_candidate": s.event_time_candidate,
            "time_precision": s.time_precision,
            "seed_text": s.seed_text,
        }
        for s in seed_rows
    ]

    phase4_out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_case": "Mills v. Polley (Preferred Gardens partnership)",
        "persisted_timeline_seed_count": len(persisted_seeds),
        "persisted_timeline_seeds": persisted_seeds,
        "candidate_anchor_count": len(unique_mentions),
        "anchors_by_category": {
            cat: sorted(items, key=lambda x: x["date_text"])[:25]
            for cat, items in sorted(anchors_by_cat.items())
        },
        "note": "Candidate anchors are READ-ONLY analysis extracted from the "
                "persisted Q1 narrative text. No new timeline_seeds were written.",
    }
    (ANALYSIS_DIR / "timeline_anchors_proposed.json").write_text(
        json.dumps(phase4_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Emit a short README so any reader can tell these are analysis artifacts.
    (ANALYSIS_DIR / "README.md").write_text(
        "# Analysis artifacts — Wave 3 preparation\n\n"
        "These JSON files are generated by\n"
        "`casecore-runtime/production/backend/scripts/wave3_prep_analysis.py`.\n\n"
        "They are **analysis-only** and **derived**. No truth-layer rows are\n"
        "mutated or created by the script beyond the standard in-memory\n"
        "wave-proof fixture. These files are allowed to evolve as analysis\n"
        "improves.\n\n"
        "Files:\n\n"
        "- `actor_reference_clusters.json` — reference candidates clustered by\n"
        "  normalized text similarity. No identity resolution is performed.\n"
        "- `candidate_actor_graph.json` — proposed nodes + edges. All status\n"
        "  `candidate (not final)`.\n"
        "- `ambiguity_risk_top10.json` — top-10 ambiguities ranked by material\n"
        "  impact on ownership / partnership / entity control / financial flow /\n"
        "  brand-IP / contract routing.\n"
        "- `timeline_anchors_proposed.json` — proposed anchors from persisted\n"
        "  seeds + read-only date extraction from the Q1 narrative.\n",
        encoding="utf-8",
    )

    # Final summary to stdout so the script is self-describing when run.
    print("[done] analysis artifacts written to:", ANALYSIS_DIR)
    print(f"  clusters={len(cluster_list)}  "
          f"nodes={len(nodes)}  edges={len(edges)}  "
          f"timeline_mentions={len(unique_mentions)}  "
          f"persisted_seeds={len(persisted_seeds)}  "
          f"risks=10")
    await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
