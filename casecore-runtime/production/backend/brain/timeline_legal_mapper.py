"""
Timeline legal mapper — heuristic, rule-based, deterministic.

Maps a TimelineEvent to CANDIDATE legal elements and strategy flags.

NOT an analysis step. This layer is the pre-analysis counterpart of actor
extraction: it surfaces hints for attorneys. Grounded legal authority comes
from the Brain resolver only, and only during Submit for Legal Analysis.
Enforced by the SR audit — this module must not import anything from the
analysis surface.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .timeline_extractor import ExtractedEvent


# ----- vocabulary -----

# Element type vocabulary (also enforced in the schema).
ELEM_COA = "COA_ELEMENT"
ELEM_BOP = "BURDEN_OF_PRODUCTION"
ELEM_BOPP = "BURDEN_OF_PERSUASION"
ELEM_REMEDY = "REMEDY"
ELEM_EVID = "EVIDENCE_ADMISSIBILITY"
ELEM_PROC = "PROCEDURAL"

REL_SUPPORTS = "SUPPORTS"
REL_WEAKENS = "WEAKENS"
REL_CONTRADICTS = "CONTRADICTS"
REL_NEUTRAL = "NEUTRAL"


# ----- rules -----

@dataclass
class LegalMapping:
    legal_element_type: str
    element_reference: Optional[str]   # e.g. "CACI_303" or "EVID_1220"
    element_label: str
    confidence: float
    rationale: str
    supporting_evidence_refs: List[dict] = field(default_factory=list)


@dataclass
class StrategyFlags:
    deposition_target: bool = False
    interrogatory_target: bool = False
    document_request_target: bool = False
    rationale: str = ""


@dataclass
class LegalAnalysisHints:
    claim_relation: str
    strategy: StrategyFlags
    mappings: List[LegalMapping]


# Regexes used for nuanced detection beyond event_type.
_RE = {
    "contract_word":     re.compile(r"\b(contract|agreement|MOU|addendum|amendment|term sheet)\b", re.I),
    "signed":            re.compile(r"\b(signed|executed|countersigned|entered into)\b", re.I),
    "breach_word":       re.compile(r"\b(breach(?:ed|es)?|default(?:ed)?|failed to|did not perform|refused to|violated)\b", re.I),
    "misrep":            re.compile(r"\b(misrepresent(?:ed|ation)?|false(?:ly)?|lied|deceiv(?:ed|e)|concealed|hid|omitted)\b", re.I),
    "fiduciary":         re.compile(r"\b(fiduciary|partner(?:ship)?|trustee|executor|officer|director|self.?dealing|conflict of interest)\b", re.I),
    "conversion":        re.compile(r"\b(converted|wrongfully (?:took|controll|retain)|refused to return|misappropriat(?:ed|ion))\b", re.I),
    "negligent":         re.compile(r"\b(negligen(?:t|ce|tly)|reckless(?:ly)?|should have known|careless(?:ly)?)\b", re.I),
    "damages_money":     re.compile(r"\$[\d,]+(?:\.\d+)?|\b(\d+[\d,]*)\s*(dollars|USD)\b", re.I),
    "harm":              re.compile(r"\b(harm(?:ed)?|damag(?:ed|es)|los[st](?:es)?|injur(?:y|ed)|suffered)\b", re.I),
    "notice_word":       re.compile(r"\b(notice|demand letter|cease and desist|served|service of process)\b", re.I),
    "denial":            re.compile(r"\b(denied|disputes?|disputed|never|did not (?:receive|know|authoriz[e]?)|refuses?|refused|contest(?:s|ed)?)\b", re.I),
    "documentary":       re.compile(r"\b(email|letter|invoice|contract|receipt|records?|statement|transcript|agreement|report|memo)\b", re.I),
    "unknown_detail":    re.compile(r"\b(approximately|around|about|sometime|later|subsequently|eventually)\b", re.I),
    "fifth_amendment":   re.compile(r"\b(fifth amendment|plead the fifth|invoke[sd]?)\b", re.I),
    "statement_reliance":re.compile(r"\b(reli(?:ed|ance)|believed|told me|represented)\b", re.I),
}


# ----- helpers -----

def _has(sent: str, key: str) -> bool:
    return bool(_RE[key].search(sent))


def _coa_suggestions(ex: ExtractedEvent) -> List[LegalMapping]:
    """
    Return CANDIDATE COA mappings. References use canonical Legal Library
    ids so the UI can deep-link; labels are human-readable.
    """
    s = ex.summary
    out: List[LegalMapping] = []

    # Breach of contract — agreement + breach OR event_type markers
    if _has(s, "contract_word") and (_has(s, "signed") or ex.event_type == "AGREEMENT"):
        out.append(LegalMapping(
            ELEM_COA, "CACI_303",
            "Breach of Contract — contract_existence",
            confidence=0.75,
            rationale="mentions contract/agreement + signed/executed",
        ))
    if ex.event_type == "BREACH" or _has(s, "breach_word"):
        out.append(LegalMapping(
            ELEM_COA, "CACI_303",
            "Breach of Contract — defendant_breach",
            confidence=0.70,
            rationale="explicit breach / refusal-to-perform language",
        ))

    # Intentional misrepresentation
    if _has(s, "misrep"):
        out.append(LegalMapping(
            ELEM_COA, "CACI_1900",
            "Intentional Misrepresentation — misrepresentation / knowledge of falsity",
            confidence=0.65,
            rationale="false/misrepresented/concealed language",
        ))
        if _has(s, "statement_reliance"):
            out.append(LegalMapping(
                ELEM_COA, "CACI_1900",
                "Intentional Misrepresentation — justifiable reliance",
                confidence=0.60,
                rationale="mentions reliance / 'told me' / 'represented'",
            ))

    # Breach of fiduciary duty
    if _has(s, "fiduciary"):
        out.append(LegalMapping(
            ELEM_COA, "CACI_4100",
            "Breach of Fiduciary Duty — fiduciary relationship / breach",
            confidence=0.65,
            rationale="fiduciary/partner/trustee language",
        ))

    # Conversion
    if _has(s, "conversion"):
        out.append(LegalMapping(
            ELEM_COA, "CACI_2100",
            "Conversion — wrongful control",
            confidence=0.65,
            rationale="wrongful control / refused to return language",
        ))

    # Negligent misrepresentation (softer signal than intentional)
    if _has(s, "negligent") and _has(s, "misrep"):
        out.append(LegalMapping(
            ELEM_COA, "CACI_1906",
            "Negligent Misrepresentation",
            confidence=0.55,
            rationale="'should have known' / 'careless' combined with representation language",
        ))

    return out


def _burden_suggestions(ex: ExtractedEvent) -> List[LegalMapping]:
    """Burden-of-production / burden-of-persuasion hints."""
    s = ex.summary
    out: List[LegalMapping] = []

    # Plaintiff typically carries the BoPP on element facts. Events that
    # provide specific factual details for contested elements sit on BoP.
    if ex.event_type in ("AGREEMENT", "PAYMENT", "BREACH", "COMMUNICATION", "TRANSACTION"):
        out.append(LegalMapping(
            ELEM_BOP, None,
            "Carries plaintiff's burden of production on a factual element",
            confidence=0.55,
            rationale=f"event_type={ex.event_type} produces documentary/testimonial evidence",
        ))

    if ex.event_type in ("BREACH", "AGREEMENT") and _has(s, "contract_word"):
        out.append(LegalMapping(
            ELEM_BOPP, "CACI_303",
            "Relevant to plaintiff's preponderance burden on breach-of-contract elements",
            confidence=0.55,
            rationale="breach + contract language relevant to persuasion burden",
        ))

    if _has(s, "fifth_amendment"):
        out.append(LegalMapping(
            ELEM_EVID, None,
            "Potential adverse inference (Fifth Amendment in civil)",
            confidence=0.50,
            rationale="Fifth Amendment / invoke language",
        ))
    return out


def _remedy_suggestions(ex: ExtractedEvent) -> List[LegalMapping]:
    s = ex.summary
    out: List[LegalMapping] = []
    if ex.event_type == "PAYMENT" or _RE["damages_money"].search(s):
        out.append(LegalMapping(
            ELEM_REMEDY, None,
            "Compensatory damages (monetary)",
            confidence=0.60,
            rationale="dollar figure or payment event",
        ))
    if _has(s, "harm"):
        out.append(LegalMapping(
            ELEM_REMEDY, None,
            "General damages (harm / injury / loss)",
            confidence=0.50,
            rationale="harm / damaged / suffered language",
        ))
    if _has(s, "misrep") or _has(s, "conversion"):
        out.append(LegalMapping(
            ELEM_REMEDY, None,
            "Possible punitive damages (intentional tort signal)",
            confidence=0.45,
            rationale="intentional misconduct signal (Civ. Code §3294 requires clear and convincing evidence)",
        ))
    return out


def _procedural_suggestions(ex: ExtractedEvent) -> List[LegalMapping]:
    out: List[LegalMapping] = []
    if ex.event_type == "FILING":
        out.append(LegalMapping(
            ELEM_PROC, None,
            "Procedural event (filing) — check statute of limitations anchors",
            confidence=0.60,
            rationale="filing keyword",
        ))
    if ex.event_type == "NOTICE":
        out.append(LegalMapping(
            ELEM_PROC, None,
            "Notice/demand event — may toll or trigger conditions precedent",
            confidence=0.55,
            rationale="notice/demand letter keyword",
        ))
    return out


# ----- strategy flags -----

def _strategy_flags(ex: ExtractedEvent, mappings: List[LegalMapping]) -> StrategyFlags:
    s = ex.summary
    reasons: List[str] = []

    deposition = False
    interrogatory = False
    doc_req = False

    # Deposition target: event has actors AND the event carries claim-relevant action
    if ex.mentioned_names and ex.event_type in ("BREACH", "COMMUNICATION", "MEETING", "AGREEMENT", "PAYMENT"):
        deposition = True
        reasons.append(f"deposition: {ex.event_type} with named actors")

    # Interrogatory target: claims are present but facts are vague
    if ex.date_precision in ("UNKNOWN", "YEAR") or _has(s, "unknown_detail"):
        if ex.event_type != "OTHER":
            interrogatory = True
            reasons.append("interrogatory: imprecise date or vague timing on a substantive event")
    if any(m.legal_element_type == ELEM_COA for m in mappings) and not _RE["damages_money"].search(s):
        # COA-signal present but no dollar figure yet
        interrogatory = True
        reasons.append("interrogatory: COA signal without damages quantified")

    # Document request target: event references documents or agreement/transaction
    if _has(s, "documentary") or ex.event_type in ("AGREEMENT", "TRANSACTION", "FILING"):
        doc_req = True
        reasons.append("document request: references document or transactional event")

    return StrategyFlags(
        deposition_target=deposition,
        interrogatory_target=interrogatory,
        document_request_target=doc_req,
        rationale="; ".join(reasons),
    )


def _claim_relation(ex: ExtractedEvent, mappings: List[LegalMapping]) -> str:
    s = ex.summary
    # CONTRADICTS dominates: denial/dispute language is strongest.
    if _has(s, "denial"):
        return REL_CONTRADICTS
    # SUPPORTS: a COA element hit + specific factual anchors (date DAY or MONTH).
    if mappings and any(m.legal_element_type == ELEM_COA for m in mappings):
        if ex.date_precision in ("DAY", "MONTH"):
            return REL_SUPPORTS
        return REL_SUPPORTS  # COA signal alone still leans supports
    if ex.event_type in ("BREACH", "PAYMENT", "AGREEMENT"):
        return REL_SUPPORTS
    return REL_NEUTRAL


# ----- public entry -----

def analyze_event(ex: ExtractedEvent) -> LegalAnalysisHints:
    """
    Produce legal-layer hints for a single timeline event.

    Never calls the authority resolver. Output is candidate-only, labeled as
    hints for attorneys — the authoritative mapping still requires Submit for
    Legal Analysis.
    """
    mappings: List[LegalMapping] = []
    mappings.extend(_coa_suggestions(ex))
    mappings.extend(_burden_suggestions(ex))
    mappings.extend(_remedy_suggestions(ex))
    mappings.extend(_procedural_suggestions(ex))

    # Dedupe by (type, reference, label). Keep highest confidence.
    dedup: dict = {}
    for m in mappings:
        key = (m.legal_element_type, m.element_reference or "", m.element_label)
        prev = dedup.get(key)
        if prev is None or m.confidence > prev.confidence:
            dedup[key] = m
    mappings = sorted(
        dedup.values(),
        key=lambda x: (-x.confidence, x.legal_element_type, x.element_reference or ""),
    )

    flags = _strategy_flags(ex, mappings)
    relation = _claim_relation(ex, mappings)

    return LegalAnalysisHints(
        claim_relation=relation,
        strategy=flags,
        mappings=mappings,
    )
