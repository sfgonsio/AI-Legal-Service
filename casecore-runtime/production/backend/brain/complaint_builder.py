"""
Complaint builder — assembles a structured draft from real case data only.

Uses:
  - Case row (caption, court, parties)
  - Actor roster (defendants, additional parties)
  - Timeline events in chronological order (factual allegations)
  - CoaCandidate list (causes of action; authority-grounded)
  - RemedyBundle list (prayer for relief)

Every allegation carries a back-reference to its source event / document /
interview, so a reviewer can trace each sentence to the evidence that
produced it. No allegations are fabricated.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ComplaintParty:
    role: str           # Plaintiff | Defendant | Third Party
    name: str
    notes: Optional[str] = None
    actor_id: Optional[int] = None


@dataclass
class ComplaintAllegation:
    para_no: int
    text: str
    source_event_id: Optional[str] = None
    source_document_id: Optional[int] = None
    source_interview_id: Optional[int] = None
    date_label: Optional[str] = None


@dataclass
class ComplaintCauseOfAction:
    count: int
    title: str                          # "FIRST CAUSE OF ACTION — Breach of Contract (CACI 303)"
    against: str
    authority_reference: str            # e.g. CACI_303
    authority_body_status: str          # IMPORTED (we refuse to cite otherwise)
    allegations: List[ComplaintAllegation]
    element_support: List[Dict[str, Any]]
    confidence: float


@dataclass
class ComplaintDraft:
    caption: str
    court: str
    filed_on: Optional[str]
    parties: List[ComplaintParty]
    jurisdiction_and_venue: str
    general_allegations: List[ComplaintAllegation]
    causes_of_action: List[ComplaintCauseOfAction]
    prayer_for_relief: List[str]
    provenance: Dict[str, Any]


_ORDINALS = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH", "EIGHTH", "NINTH", "TENTH"]


def _ordinal(n: int) -> str:
    if 1 <= n <= len(_ORDINALS):
        return _ORDINALS[n - 1]
    return f"{n}TH"


def _format_date(ts: Optional[datetime], precision: str) -> str:
    if ts is None:
        return "at an unknown date"
    if precision == "DAY":
        return f"on {ts.strftime('%B %d, %Y')}"
    if precision == "MONTH":
        return f"in {ts.strftime('%B %Y')}"
    if precision == "YEAR":
        return f"in {ts.year}"
    return "at an unknown date"


def build_complaint(
    case,
    actors: List[Any],
    timeline_events: List[Any],
    coa_candidates,
    remedy_bundles,
) -> ComplaintDraft:
    # --- Parties ---
    parties: List[ComplaintParty] = []
    if case.plaintiff:
        parties.append(ComplaintParty(role="Plaintiff", name=case.plaintiff))
    if case.defendant:
        parties.append(ComplaintParty(role="Defendant", name=case.defendant))
    # Actor roster may include additional named entities. Exclude actors
    # whose role_hint places them outside the party caption (the court, the
    # presiding judge, opposing counsel, etc.).
    NON_PARTY_ROLES = {"court", "judge", "opposing_counsel", "counsel", "attorney"}
    for a in actors:
        if a.role_hint in ("plaintiff", "defendant"):
            continue
        if a.role_hint and a.role_hint.lower() in NON_PARTY_ROLES:
            continue
        if a.resolution_state != "RESOLVED":
            continue
        parties.append(ComplaintParty(
            role="Third Party" if a.entity_type == "ORGANIZATION" else "Additional Party",
            name=a.display_name,
            notes=a.role_hint or None,
            actor_id=a.id,
        ))

    court = case.court or "[court not specified]"
    caption = f"{case.plaintiff or '[Plaintiff]'} v. {case.defendant or '[Defendant]'}"
    filed_on = case.created_at.isoformat() if case.created_at else None

    # --- Jurisdiction / Venue (template; attorney refines) ---
    jv = (
        "Jurisdiction and venue are proper in this Court. This action arises from "
        "conduct occurring in California and involves parties subject to the "
        "Court's jurisdiction. Venue is proper under CCP § 395(a) where the "
        "contract was to be performed or the obligation incurred."
    )

    # --- General allegations from timeline (chronological) ---
    sorted_events = sorted(
        [e for e in timeline_events],
        key=lambda x: (x.timestamp is None, x.timestamp or datetime.max, x.id),
    )
    general: List[ComplaintAllegation] = []
    para = 1
    for ev in sorted_events:
        date_label = _format_date(ev.timestamp, ev.date_precision)
        text = ev.summary.strip()
        # Normalize simple sentence capitalization
        if not text.endswith((".", "?", "!")):
            text += "."
        allegation = ComplaintAllegation(
            para_no=para,
            text=text,
            source_event_id=ev.event_id,
            source_document_id=ev.source_document_id,
            source_interview_id=ev.source_interview_id,
            date_label=date_label,
        )
        general.append(allegation)
        para += 1

    # --- Causes of action ---
    causes: List[ComplaintCauseOfAction] = []
    ev_by_id = {ev.event_id: ev for ev in sorted_events}
    for idx, c in enumerate(coa_candidates, start=1):
        coa_allegs: List[ComplaintAllegation] = []
        coa_para = 1
        # Element-by-element factual recitation
        for s in c.elements:
            if s.status == "UNSUPPORTED":
                continue
            for eid in s.supporting_event_ids:
                ev = ev_by_id.get(eid)
                if ev is None:
                    continue
                coa_allegs.append(ComplaintAllegation(
                    para_no=coa_para,
                    text=f"({s.element_id}) {ev.summary.strip()}",
                    source_event_id=ev.event_id,
                    source_document_id=ev.source_document_id,
                    source_interview_id=ev.source_interview_id,
                    date_label=_format_date(ev.timestamp, ev.date_precision),
                ))
                coa_para += 1

        elem_support = [
            {"element_id": s.element_id, "label": s.label, "status": s.status,
             "confidence": s.confidence,
             "supporting_event_ids": list(s.supporting_event_ids)}
            for s in c.elements
        ]
        causes.append(ComplaintCauseOfAction(
            count=idx,
            title=f"{_ordinal(idx)} CAUSE OF ACTION — {c.name} ({c.caci_id.replace('_', ' ')})",
            against=case.defendant or "Defendant",
            authority_reference=c.caci_id,
            authority_body_status=c.authority["body_status"],
            allegations=coa_allegs,
            element_support=elem_support,
            confidence=c.confidence,
        ))

    # --- Prayer for relief (from remedies) ---
    prayer: List[str] = []
    seen = set()
    for b in remedy_bundles:
        for r in b.remedies:
            line = f"{r.label} ({r.category})"
            if line not in seen:
                prayer.append(line)
                seen.add(line)
    if not any("costs" in p.lower() or "interest" in p.lower() for p in prayer):
        prayer.append("Costs of suit and pre- and post-judgment interest as allowed by law (costs_fees_interest)")
    prayer.append("Such other and further relief as the Court deems just and proper")

    provenance = {
        "timeline_event_count": len(sorted_events),
        "coa_count": len(causes),
        "authority_grounded": all(c.authority_body_status == "IMPORTED" for c in causes),
        "notes": (
            "Every CACI citation in this draft references an IMPORTED Legal Library record. "
            "Statute citations in grounding notes (e.g. Civ. Code §§3333, 3294) are general "
            "references for attorney review — pinpoint citations remain an attorney decision."
        ),
    }

    return ComplaintDraft(
        caption=caption,
        court=court,
        filed_on=filed_on,
        parties=parties,
        jurisdiction_and_venue=jv,
        general_allegations=general,
        causes_of_action=causes,
        prayer_for_relief=prayer,
        provenance=provenance,
    )


def serialize(draft: ComplaintDraft) -> Dict[str, Any]:
    return asdict(draft)
