"""
Remedy derivation — per COA, derive typical remedies.

Remedy categories (UI vocabulary):
  - compensatory            (expectation / out-of-pocket / reliance damages)
  - punitive                (Civ. Code §3294 — intentional torts; clear and convincing)
  - injunctive              (prohibitory or mandatory)
  - declaratory             (CCP §1060)
  - restitution             (unjust enrichment, disgorgement)
  - costs_fees_interest     (CCP §1021 / §1032 / §3287)

Each remedy is labeled with a grounding note so the attorney knows *why*
this COA supports it. No hallucinated citations: every named statute cited
in the notes is an actual California statute — these are general references,
not pinpoint authority. Pinpoint citations remain an attorney decision.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Set


@dataclass
class RemedyItem:
    category: str
    label: str
    grounding: str
    confidence: float
    supporting_event_ids: List[str] = field(default_factory=list)


@dataclass
class CoaRemedyBundle:
    caci_id: str
    name: str
    authority_reference: str
    remedies: List[RemedyItem]


# Default remedy templates per CACI id.
_REMEDY_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "CACI_303": [
        {"category": "compensatory", "label": "Expectation damages (benefit of the bargain)",
         "grounding": "Civ. Code §3300 — general measure for contract breach.", "base_conf": 0.90},
        {"category": "restitution", "label": "Restitution where contract was rescinded or unenforceable",
         "grounding": "Civ. Code §§1688–1693 (rescission); general unjust-enrichment.", "base_conf": 0.55},
        {"category": "costs_fees_interest", "label": "Prejudgment interest on liquidated sum",
         "grounding": "Civ. Code §3287.", "base_conf": 0.70},
        {"category": "costs_fees_interest", "label": "Attorney's fees if contract so provides",
         "grounding": "Civ. Code §1717 when contract contains a fees clause.", "base_conf": 0.50},
    ],
    "CACI_1900": [
        {"category": "compensatory", "label": "Out-of-pocket damages caused by reliance",
         "grounding": "Civ. Code §§1709, 3333; out-of-pocket measure for fraud.", "base_conf": 0.85},
        {"category": "compensatory", "label": "Consequential damages reasonably caused by fraud",
         "grounding": "Civ. Code §3333.", "base_conf": 0.70},
        {"category": "punitive", "label": "Punitive damages (intentional tort)",
         "grounding": "Civ. Code §3294 — requires clear and convincing evidence of malice, oppression, or fraud.",
         "base_conf": 0.60},
        {"category": "restitution", "label": "Rescission and restitution",
         "grounding": "Civ. Code §§1689, 1691; fraud in the inducement.", "base_conf": 0.55},
    ],
    "CACI_1906": [
        {"category": "compensatory", "label": "Out-of-pocket damages (negligent misrep measure)",
         "grounding": "Civ. Code §§1709, 3333; Alliance Mortgage v. Rothwell (1995) 10 Cal.4th 1226.",
         "base_conf": 0.75},
        {"category": "restitution", "label": "Restitution where representation induced transaction",
         "grounding": "Civ. Code §§1688–1693.", "base_conf": 0.50},
    ],
    "CACI_2100": [
        {"category": "compensatory", "label": "Value of the property at the time of conversion",
         "grounding": "Civ. Code §3336 — value of the property plus fair compensation for loss of use.",
         "base_conf": 0.90},
        {"category": "punitive", "label": "Punitive damages for malicious conversion",
         "grounding": "Civ. Code §3294.", "base_conf": 0.55},
        {"category": "costs_fees_interest", "label": "Prejudgment interest",
         "grounding": "Civ. Code §3287.", "base_conf": 0.65},
    ],
    "CACI_4100": [
        {"category": "compensatory", "label": "Compensatory damages for loss caused by breach of duty",
         "grounding": "General tort measure; Civ. Code §3333.", "base_conf": 0.80},
        {"category": "restitution", "label": "Disgorgement / constructive trust on benefits retained",
         "grounding": "Civ. Code §§2223–2224; fiduciary-duty restitution.", "base_conf": 0.70},
        {"category": "punitive", "label": "Punitive damages where breach involved malice, oppression, or fraud",
         "grounding": "Civ. Code §3294.", "base_conf": 0.55},
        {"category": "injunctive", "label": "Injunctive relief to prevent continuing breach",
         "grounding": "Civ. Code §3422; CCP §526.", "base_conf": 0.45},
    ],
}


def _has_money_event(coa_events: Set[str], event_by_id) -> bool:
    for eid in coa_events:
        ev = event_by_id.get(eid)
        if ev is None:
            continue
        if "$" in (ev.summary or "") or any(
            m.legal_element_type == "REMEDY" for m in (ev.legal_mappings or [])
        ):
            return True
    return False


def derive_remedies(coa_candidates, timeline_events) -> List[CoaRemedyBundle]:
    """
    Build a remedy bundle per COA, grounded in that COA's template.

    Confidence is the template's base, boosted when the timeline actually
    carries evidence in that remedy's direction (e.g. dollar amounts,
    REMEDY-type legal mappings).
    """
    event_by_id = {ev.event_id: ev for ev in timeline_events}
    out: List[CoaRemedyBundle] = []

    for c in coa_candidates:
        tmpl = _REMEDY_TEMPLATES.get(c.caci_id)
        if not tmpl:
            continue
        remedies: List[RemedyItem] = []
        coa_event_set = set(c.supporting_event_ids)
        has_money = _has_money_event(coa_event_set, event_by_id)

        for r in tmpl:
            supporting: List[str] = []
            conf = float(r["base_conf"])
            # Modest confidence bump for compensatory/restitution when the
            # timeline shows monetary evidence.
            if has_money and r["category"] in ("compensatory", "restitution"):
                conf = min(0.95, conf + 0.05)
                # Attach the monetary-bearing events as supports
                for eid in coa_event_set:
                    ev = event_by_id.get(eid)
                    if ev is None:
                        continue
                    if "$" in (ev.summary or ""):
                        supporting.append(eid)

            # Slight bump for punitive when intentional-tort signals exist
            if r["category"] == "punitive" and c.caci_id in ("CACI_1900", "CACI_4100", "CACI_2100"):
                # Only bump if coverage_pct suggests the liability picture is solid
                if c.coverage_pct >= 0.5:
                    conf = min(0.70, conf + 0.05)

            remedies.append(RemedyItem(
                category=r["category"],
                label=r["label"],
                grounding=r["grounding"],
                confidence=round(conf, 2),
                supporting_event_ids=supporting,
            ))

        out.append(CoaRemedyBundle(
            caci_id=c.caci_id,
            name=c.name,
            authority_reference=c.authority["reference"],
            remedies=remedies,
        ))
    return out


def serialize(bundles: List[CoaRemedyBundle]) -> List[Dict[str, Any]]:
    return [asdict(b) for b in bundles]
