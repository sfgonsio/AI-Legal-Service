"""
COA engine — grounded Cause-of-Action candidate generation.

Input: TimelineEvent rows + TimelineEventLegalMapping rows (built by the
timeline layer) + Actor rows + Case row.

Output: per-case list of CANDIDATE COAs, each:
  - grounded in a Legal Library record (body_status=IMPORTED confirmed)
  - carrying a structured element list
  - per-element supporting events + actors
  - confidence derived from mapping coverage + signal strength

No hallucinated authority. Every CACI reference is verified present in the
canonical corpus before inclusion; if a record is NOT_IMPORTED, the COA is
dropped rather than emitted with a broken citation.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from . import legal_library


# ---- Authoritative element breakdowns for the v1 supported COAs ----
# These are structured restatements of the CACI instructions that already
# exist (IMPORTED) in the Legal Library corpus. The engine verifies each
# CACI body is present before using these definitions.

_COA_DEFS: Dict[str, Dict[str, Any]] = {
    "CACI_303": {
        "name": "Breach of Contract",
        "elements": [
            {"id": "contract_existence",
             "label": "A contract existed between the parties",
             "proof_types": ["written_contract", "oral_agreement", "conduct"]},
            {"id": "plaintiff_performance",
             "label": "Plaintiff performed (or performance was excused)",
             "proof_types": ["performance_records", "testimony"]},
            {"id": "defendant_breach",
             "label": "Defendant breached the contract",
             "proof_types": ["breach_event", "failure_to_perform"]},
            {"id": "damages",
             "label": "Plaintiff was harmed by the breach",
             "proof_types": ["financial_records", "expert_testimony"]},
        ],
    },
    "CACI_1900": {
        "name": "Intentional Misrepresentation",
        "elements": [
            {"id": "misrepresentation",
             "label": "Defendant represented a material fact that was false",
             "proof_types": ["communications", "documents"]},
            {"id": "knowledge_of_falsity",
             "label": "Defendant knew the representation was false (or made it recklessly)",
             "proof_types": ["internal_records", "testimony"]},
            {"id": "intent_to_induce_reliance",
             "label": "Defendant intended plaintiff to rely on the representation",
             "proof_types": ["context_evidence"]},
            {"id": "justifiable_reliance",
             "label": "Plaintiff reasonably relied on the representation",
             "proof_types": ["reliance_actions"]},
            {"id": "damages",
             "label": "Plaintiff was harmed by the reliance",
             "proof_types": ["financial_records"]},
        ],
    },
    "CACI_1906": {
        "name": "Negligent Misrepresentation",
        "elements": [
            {"id": "misrepresentation",
             "label": "Defendant represented a material fact that was false",
             "proof_types": ["communications", "documents"]},
            {"id": "no_reasonable_ground",
             "label": "Defendant had no reasonable ground to believe the representation was true",
             "proof_types": ["internal_records", "context_evidence"]},
            {"id": "intent_to_induce_reliance",
             "label": "Defendant intended plaintiff to rely on the representation",
             "proof_types": ["context_evidence"]},
            {"id": "justifiable_reliance",
             "label": "Plaintiff reasonably relied on the representation",
             "proof_types": ["reliance_actions"]},
            {"id": "damages",
             "label": "Plaintiff suffered out-of-pocket damages",
             "proof_types": ["financial_records"]},
        ],
    },
    "CACI_2100": {
        "name": "Conversion",
        "elements": [
            {"id": "ownership_or_right_to_possession",
             "label": "Plaintiff owned or had a right to possess the property",
             "proof_types": ["ownership_docs", "testimony"]},
            {"id": "wrongful_control",
             "label": "Defendant substantially interfered with plaintiff's property",
             "proof_types": ["control_evidence", "demand_refusal"]},
            {"id": "harm",
             "label": "Plaintiff was harmed by the interference",
             "proof_types": ["valuation_docs"]},
        ],
    },
    "CACI_4100": {
        "name": "Breach of Fiduciary Duty",
        "elements": [
            {"id": "fiduciary_relationship",
             "label": "A fiduciary relationship existed between the parties",
             "proof_types": ["partnership_agreement", "conduct"]},
            {"id": "breach_of_duty",
             "label": "Defendant breached the fiduciary duty",
             "proof_types": ["accounting_records", "testimony"]},
            {"id": "damages",
             "label": "Plaintiff was harmed as a result of the breach",
             "proof_types": ["financial_records"]},
        ],
    },
}


# Keyword heuristics for associating event evidence with specific COA elements
# when the timeline legal mapper's label alone is not granular enough.
_ELEMENT_KEYWORDS: Dict[str, List[str]] = {
    "contract_existence":          ["contract", "agreement", "signed", "executed", "amendment", "addendum", "MOU", "term sheet"],
    "plaintiff_performance":       ["performed", "delivered", "paid", "completed"],
    "defendant_breach":            ["breach", "default", "failed to", "refused to", "did not perform", "violated"],
    "damages":                     ["damages", "harm", "loss", "injur", "suffered", "$"],

    "misrepresentation":           ["misrepresent", "false", "lied", "deceived", "concealed", "hid"],
    "knowledge_of_falsity":        ["knew", "knowing", "recklessly", "internal records"],
    "intent_to_induce_reliance":   ["intended", "induce", "represented"],
    "justifiable_reliance":        ["relied", "reliance", "believed", "told me"],
    "no_reasonable_ground":        ["should have known", "careless", "negligen"],

    "ownership_or_right_to_possession": ["owned", "possess", "title", "rights"],
    "wrongful_control":                 ["wrongful", "took possession", "refused to return", "withheld", "converted"],

    "fiduciary_relationship":      ["partner", "fiduciary", "trustee", "officer", "director", "executor"],
    "breach_of_duty":              ["self-dealing", "conflict of interest", "breach", "concealed", "diverted"],
    "harm":                        ["harm", "damage", "loss", "injur"],
}


@dataclass
class CoaElementSupport:
    element_id: str
    label: str
    proof_types: List[str]
    supporting_event_ids: List[str] = field(default_factory=list)
    supporting_document_ids: List[int] = field(default_factory=list)
    supporting_interview_ids: List[int] = field(default_factory=list)
    actor_ids: List[int] = field(default_factory=list)
    confidence: float = 0.0                # per-element
    status: str = "UNSUPPORTED"            # SUPPORTED | PARTIAL | UNSUPPORTED


@dataclass
class CoaCandidate:
    caci_id: str
    name: str
    authority: Dict[str, Any]              # library-grounded citation
    elements: List[CoaElementSupport]
    supporting_event_ids: List[str]
    actor_ids: List[int]
    coverage_pct: float                    # supported_or_partial / total
    confidence: float
    rationale: str


def _element_label_matches(element_id: str, mapping_label: str) -> bool:
    return element_id.lower() in (mapping_label or "").lower()


def _text_supports_element(element_id: str, text: str) -> bool:
    if not text:
        return False
    tl = text.lower()
    for kw in _ELEMENT_KEYWORDS.get(element_id, []):
        if kw in tl:
            return True
    return False


def generate_coa_candidates(
    timeline_events: List[Any],
) -> List[CoaCandidate]:
    """
    Walk timeline legal_mappings, bucket by CACI reference, for each bucket
    verify the canonical record IMPORTED, then emit a grounded COA.

    timeline_events must be ORM-loaded with `legal_mappings` selectinloaded.
    """
    # Bucket mappings by caci_id
    by_caci: Dict[str, List[Tuple[Any, Any]]] = defaultdict(list)
    for ev in timeline_events:
        for m in (ev.legal_mappings or []):
            if m.legal_element_type != "COA_ELEMENT":
                continue
            ref = (m.element_reference or "").strip()
            if not ref:
                continue
            by_caci[ref].append((ev, m))

    out: List[CoaCandidate] = []
    for caci_id, hits in by_caci.items():
        defn = _COA_DEFS.get(caci_id)
        if not defn:
            # COA not in v1 supported list; skip rather than emit a partial structure.
            continue

        # Authority grounding: Legal Library must have the IMPORTED body.
        lib = legal_library.fetch_record(caci_id)
        if lib.body_status != legal_library.BODY_IMPORTED:
            # Skip rather than emit a COA with a broken citation.
            continue

        # Per-element support: start from mapping hits, then augment with
        # keyword matches against event summaries.
        elem_supports: List[CoaElementSupport] = []
        overall_actor_ids: set = set()
        overall_event_ids: set = set()
        for e in defn["elements"]:
            eid = e["id"]
            support = CoaElementSupport(
                element_id=eid, label=e["label"], proof_types=e["proof_types"],
            )
            # Pass 1: explicit label match
            for ev, m in hits:
                if _element_label_matches(eid, m.element_label):
                    if ev.event_id not in support.supporting_event_ids:
                        support.supporting_event_ids.append(ev.event_id)
                    if ev.source_document_id and ev.source_document_id not in support.supporting_document_ids:
                        support.supporting_document_ids.append(ev.source_document_id)
                    if ev.source_interview_id and ev.source_interview_id not in support.supporting_interview_ids:
                        support.supporting_interview_ids.append(ev.source_interview_id)
                    for aid in (ev.actor_ids or []):
                        if aid not in support.actor_ids:
                            support.actor_ids.append(aid)
                    support.confidence = max(support.confidence, float(m.confidence))
            # Pass 2: keyword inference against timeline events whose
            # mappings pointed to this COA but not this specific element
            for ev, _m in hits:
                if ev.event_id in support.supporting_event_ids:
                    continue
                if _text_supports_element(eid, ev.summary):
                    support.supporting_event_ids.append(ev.event_id)
                    if ev.source_document_id and ev.source_document_id not in support.supporting_document_ids:
                        support.supporting_document_ids.append(ev.source_document_id)
                    if ev.source_interview_id and ev.source_interview_id not in support.supporting_interview_ids:
                        support.supporting_interview_ids.append(ev.source_interview_id)
                    for aid in (ev.actor_ids or []):
                        if aid not in support.actor_ids:
                            support.actor_ids.append(aid)
                    # Inferred hits keep modest confidence
                    support.confidence = max(support.confidence, 0.50)

            if not support.supporting_event_ids:
                support.status = "UNSUPPORTED"
                support.confidence = max(support.confidence, 0.0)
            else:
                # PARTIAL if only one event or low confidence; SUPPORTED if 2+ events or high confidence.
                if len(support.supporting_event_ids) >= 2 or support.confidence >= 0.70:
                    support.status = "SUPPORTED"
                else:
                    support.status = "PARTIAL"
                overall_event_ids.update(support.supporting_event_ids)
                for aid in support.actor_ids:
                    overall_actor_ids.add(aid)
            elem_supports.append(support)

        # COA-level metrics
        total = len(elem_supports)
        supported = sum(1 for s in elem_supports if s.status == "SUPPORTED")
        partial = sum(1 for s in elem_supports if s.status == "PARTIAL")
        coverage_pct = ((supported + partial) / total) if total else 0.0
        # COA confidence = weighted mean of element confidences + coverage factor
        if total:
            mean_elem_conf = sum(s.confidence for s in elem_supports) / total
        else:
            mean_elem_conf = 0.0
        coa_conf = round(min(0.95, 0.5 * mean_elem_conf + 0.5 * coverage_pct), 2)

        out.append(CoaCandidate(
            caci_id=caci_id,
            name=defn["name"],
            authority={
                "reference": lib.record_id,
                "title": lib.title,
                "body_status": lib.body_status,           # IMPORTED
                "body_length": lib.body_length,
                "certified": lib.certified,
                "source_url": (lib.source or {}).get("url") if lib.source else None,
            },
            elements=elem_supports,
            supporting_event_ids=sorted(overall_event_ids),
            actor_ids=sorted(overall_actor_ids),
            coverage_pct=round(coverage_pct, 2),
            confidence=coa_conf,
            rationale=(
                f"{len(hits)} timeline mappings cite {caci_id}; "
                f"{supported} of {total} elements SUPPORTED, {partial} PARTIAL."
            ),
        ))

    # Sort COAs by confidence, then by name
    out.sort(key=lambda c: (-c.confidence, c.name))
    return out


def serialize(coas: List[CoaCandidate]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for c in coas:
        d = asdict(c)
        out.append(d)
    return out
