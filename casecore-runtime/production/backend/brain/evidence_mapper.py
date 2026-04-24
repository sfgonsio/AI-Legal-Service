"""
Evidence mapping — builds the graph

    Evidence (Document | Interview)
        -> Event (TimelineEvent)
            -> Actor
                -> Element (COA element)
                    -> COA

so an attorney can trace every element back to a source document or
interview passage.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class EvidenceNode:
    source_kind: str                # DOCUMENT | INTERVIEW
    source_id: int                  # Document.id or Interview.id
    label: str                      # filename or "Interview #N"
    sha256_hash: Optional[str] = None
    file_type: Optional[str] = None


@dataclass
class EvidenceEdge:
    evidence: EvidenceNode
    event_id: str
    event_summary: str
    event_timestamp: Optional[str]
    actor_ids: List[int]
    coa_links: List[Dict[str, str]] = field(default_factory=list)   # [{caci_id, element_id}]


@dataclass
class EvidenceMap:
    total_events: int
    total_edges: int
    edges: List[EvidenceEdge]
    actors_referenced: List[int]
    coverage_per_coa: List[Dict[str, Any]]


def build_evidence_map(timeline_events, coa_candidates, documents, interviews) -> EvidenceMap:
    doc_by_id = {d.id: d for d in documents}
    iv_by_id = {i.id: i for i in interviews}

    # Index per-event which COA/elements it supports
    coa_links_by_event: Dict[str, List[Dict[str, str]]] = {}
    for c in coa_candidates:
        for s in c.elements:
            for eid in s.supporting_event_ids:
                coa_links_by_event.setdefault(eid, []).append({
                    "caci_id": c.caci_id,
                    "coa_name": c.name,
                    "element_id": s.element_id,
                    "element_label": s.label,
                    "element_status": s.status,
                })

    edges: List[EvidenceEdge] = []
    actors_referenced: set = set()
    for ev in timeline_events:
        if ev.source_document_id:
            d = doc_by_id.get(ev.source_document_id)
            if d:
                edges.append(EvidenceEdge(
                    evidence=EvidenceNode(
                        source_kind="DOCUMENT",
                        source_id=d.id,
                        label=(d.folder + "/" + d.filename) if d.folder else d.filename,
                        sha256_hash=d.sha256_hash,
                        file_type=d.file_type,
                    ),
                    event_id=ev.event_id,
                    event_summary=ev.summary,
                    event_timestamp=ev.timestamp.isoformat() if ev.timestamp else None,
                    actor_ids=list(ev.actor_ids or []),
                    coa_links=coa_links_by_event.get(ev.event_id, []),
                ))
        if ev.source_interview_id:
            iv = iv_by_id.get(ev.source_interview_id)
            if iv:
                edges.append(EvidenceEdge(
                    evidence=EvidenceNode(
                        source_kind="INTERVIEW",
                        source_id=iv.id,
                        label=f"Interview #{iv.id} ({iv.mode})",
                    ),
                    event_id=ev.event_id,
                    event_summary=ev.summary,
                    event_timestamp=ev.timestamp.isoformat() if ev.timestamp else None,
                    actor_ids=list(ev.actor_ids or []),
                    coa_links=coa_links_by_event.get(ev.event_id, []),
                ))
        for aid in (ev.actor_ids or []):
            actors_referenced.add(aid)

    # Coverage per COA: how many elements have ≥1 evidence edge
    coverage_per_coa: List[Dict[str, Any]] = []
    for c in coa_candidates:
        supported = sum(1 for s in c.elements if s.status in ("SUPPORTED", "PARTIAL"))
        coverage_per_coa.append({
            "caci_id": c.caci_id,
            "name": c.name,
            "elements_total": len(c.elements),
            "elements_with_evidence": supported,
            "coverage_pct": c.coverage_pct,
            "confidence": c.confidence,
        })

    return EvidenceMap(
        total_events=len(timeline_events),
        total_edges=len(edges),
        edges=edges,
        actors_referenced=sorted(actors_referenced),
        coverage_per_coa=coverage_per_coa,
    )


def serialize(em: EvidenceMap) -> Dict[str, Any]:
    return asdict(em)
