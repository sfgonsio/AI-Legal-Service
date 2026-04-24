"""
Legal Library loader.

Single read accessor for the canonical corpus under
`casecore-runtime/legal/canonical/`:
  - caci/           CACI_{id}.json
  - evidence_code/  EVID_{id}.json
  - bpc_cannabis/   BPC_{id}.json

Exposes a uniform LibraryRecord shape with an explicit body_status so the UI
never has to guess whether body text exists. A record_id like "CCP_3294" that
does not exist in the corpus resolves to a NOT_IMPORTED record — never
"undefined" and never a silent empty body.

Enforced by SR-12: this module has no analytical dependencies.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


# -------- body-status vocabulary --------

BODY_IMPORTED = "IMPORTED"           # full text present in canonical corpus
BODY_NOT_IMPORTED = "NOT_IMPORTED"   # record id is not (yet) in this corpus
BODY_REVOKED = "REVOKED"             # explicitly marked revoked in the source
BODY_BLOCKED = "BLOCKED"             # governance-blocked (e.g. confidence gating)


@dataclass
class LibraryRecord:
    record_id: str                  # "CACI_1900"
    code: str                       # "CACI"
    item_id: str                    # "1900"
    title: str                      # human title or "(no title imported)"
    body_text: Optional[str]        # full body text or None
    body_status: str                # IMPORTED | NOT_IMPORTED | REVOKED | BLOCKED
    body_length: int                # len(body_text or "")
    certified: bool                 # true for canonical corpus items
    provisional: bool               # false for canonical corpus
    tags: List[str] = field(default_factory=list)
    # CACI-only extras
    series: Optional[str] = None
    series_title: Optional[str] = None
    directions_for_use: Optional[str] = None
    sources_and_authority: Optional[str] = None
    # EVID-only extras
    structure: Optional[Dict[str, Any]] = None
    # Common provenance
    source: Optional[Dict[str, Any]] = None
    # Explicit reason string when body_status != IMPORTED
    status_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# -------- root resolution --------

def _canonical_root() -> Path:
    override = os.getenv("CASECORE_CANONICAL_PATH")
    if override:
        return Path(override)
    # Walk up from this file looking for casecore-runtime/legal/canonical.
    here = Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        candidate = parent / "casecore-runtime" / "legal" / "canonical"
        if candidate.is_dir():
            return candidate
    # Fallback: 5 levels up (backend/brain/legal_library.py -> production/backend/.. -> runtime root)
    return here.parents[4] / "casecore-runtime" / "legal" / "canonical"


# -------- per-code loader helpers --------

def _parse_caci(path: Path) -> LibraryRecord:
    doc = json.loads(path.read_text(encoding="utf-8"))
    iid = str(doc.get("instruction_id") or path.stem.split("_", 1)[-1])
    text = (doc.get("text") or "").strip()
    body_status = BODY_IMPORTED if text else BODY_NOT_IMPORTED
    return LibraryRecord(
        record_id=f"CACI_{iid}",
        code="CACI",
        item_id=iid,
        title=doc.get("title") or f"CACI {iid}",
        body_text=text or None,
        body_status=body_status,
        body_length=len(text),
        certified=True,
        provisional=False,
        tags=list(doc.get("tags") or []),
        series=doc.get("series"),
        series_title=doc.get("series_title"),
        directions_for_use=doc.get("directions_for_use"),
        sources_and_authority=doc.get("sources_and_authority"),
        source=doc.get("source"),
        status_message=None if text else "Body text not present in canonical record.",
    )


def _parse_evid(path: Path) -> LibraryRecord:
    doc = json.loads(path.read_text(encoding="utf-8"))
    section = str(doc.get("section") or path.stem.split("_", 1)[-1])
    text = (doc.get("text") or "").strip()
    body_status = BODY_IMPORTED if text else BODY_NOT_IMPORTED
    return LibraryRecord(
        record_id=f"EVID_{section}",
        code="EVID",
        item_id=section,
        title=doc.get("title") or f"Evidence Code § {section}",
        body_text=text or None,
        body_status=body_status,
        body_length=len(text),
        certified=True,
        provisional=False,
        tags=list(doc.get("tags") or []),
        structure=doc.get("structure"),
        source=doc.get("source"),
        status_message=None if text else "Body text not present in canonical record.",
    )


def _parse_bpc(path: Path) -> LibraryRecord:
    doc = json.loads(path.read_text(encoding="utf-8"))
    section = str(doc.get("section") or path.stem.split("_", 1)[-1])
    text = (doc.get("text") or "").strip()
    body_status = BODY_IMPORTED if text else BODY_NOT_IMPORTED
    return LibraryRecord(
        record_id=f"BPC_{section}",
        code="BPC",
        item_id=section,
        title=doc.get("title") or f"Bus. & Prof. Code § {section}",
        body_text=text or None,
        body_status=body_status,
        body_length=len(text),
        certified=True,
        provisional=False,
        tags=list(doc.get("tags") or []),
        structure=doc.get("structure"),
        source=doc.get("source"),
        status_message=None if text else "Body text not present in canonical record.",
    )


_PARSERS = {
    "CACI": ("caci", _parse_caci),
    "EVID": ("evidence_code", _parse_evid),
    "BPC": ("bpc_cannabis", _parse_bpc),
}


# -------- index build --------

@lru_cache(maxsize=1)
def build_index() -> Dict[str, Path]:
    """
    Scan the canonical corpus once and build record_id -> file path.
    Cached; call invalidate_cache() after importing new records.
    """
    root = _canonical_root()
    index: Dict[str, Path] = {}
    for code, (subdir, _parser) in _PARSERS.items():
        d = root / subdir
        if not d.is_dir():
            continue
        for f in d.glob("*.json"):
            stem = f.stem  # e.g. CACI_1900
            if "_" not in stem:
                continue
            prefix = stem.split("_", 1)[0].upper()
            if prefix != code:
                continue
            index[stem] = f
    return index


def invalidate_cache() -> None:
    build_index.cache_clear()


# -------- public API --------

SUPPORTED_CODES = ("CACI", "EVID", "BPC")


def list_records(
    code: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    List records, optionally filtered by code or a case-insensitive substring
    match against record_id + title. Body text is NOT included in the list
    response — use fetch_record(record_id) for body.
    """
    idx = build_index()
    items: List[LibraryRecord] = []
    code_u = (code or "").upper() or None
    ql = (q or "").strip().lower() or None

    # Parse lazily; we don't need bodies for list views.
    for record_id, path in idx.items():
        prefix = record_id.split("_", 1)[0].upper()
        if code_u and prefix != code_u:
            continue
        # Cheap: use filename for ID; title is embedded in JSON, we parse a
        # small subset only if filtering by q.
        if ql:
            rec = _parse_by_code(prefix, path)
            hay = f"{rec.record_id} {rec.title}".lower()
            if ql not in hay:
                continue
            # Strip body for list payload
            rec_dict = rec.to_dict()
            rec_dict["body_text"] = None
            items.append(rec_dict)  # type: ignore
        else:
            rec = _parse_by_code(prefix, path)
            rec_dict = rec.to_dict()
            rec_dict["body_text"] = None
            items.append(rec_dict)  # type: ignore

    # sort by record_id for determinism
    items.sort(key=lambda r: r["record_id"] if isinstance(r, dict) else r.record_id)
    total = len(items)
    sliced = items[offset: offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "codes": list(SUPPORTED_CODES),
        "records": sliced,
    }


def _parse_by_code(prefix: str, path: Path) -> LibraryRecord:
    _sub, parser = _PARSERS[prefix]
    return parser(path)


def fetch_record(record_id: str) -> LibraryRecord:
    """
    Return the full LibraryRecord for a given id. If the id is not in the
    canonical corpus, return a NOT_IMPORTED record with an explicit status
    message — never raise "undefined", never return an empty body silently.
    """
    rid = (record_id or "").strip()
    if not rid or "_" not in rid:
        return LibraryRecord(
            record_id=rid or "(empty)",
            code="UNKNOWN",
            item_id="",
            title=rid or "(empty record id)",
            body_text=None,
            body_status=BODY_NOT_IMPORTED,
            body_length=0,
            certified=False,
            provisional=False,
            status_message="Invalid record id. Expected format like 'CACI_1900' or 'EVID_1220'.",
        )

    idx = build_index()
    path = idx.get(rid)
    if path is None:
        prefix = rid.split("_", 1)[0].upper()
        if prefix not in _PARSERS:
            return LibraryRecord(
                record_id=rid,
                code=prefix,
                item_id=rid.split("_", 1)[1],
                title=rid,
                body_text=None,
                body_status=BODY_NOT_IMPORTED,
                body_length=0,
                certified=False,
                provisional=False,
                status_message=(
                    f"Code '{prefix}' is not present in this corpus. "
                    f"Supported codes: {', '.join(SUPPORTED_CODES)}. "
                    f"Other codes (e.g. CCP, CIV) must be imported before they can be displayed."
                ),
            )
        return LibraryRecord(
            record_id=rid,
            code=prefix,
            item_id=rid.split("_", 1)[1],
            title=rid,
            body_text=None,
            body_status=BODY_NOT_IMPORTED,
            body_length=0,
            certified=False,
            provisional=False,
            status_message=(
                f"{rid} is not present in the canonical corpus. The structural "
                f"record may exist elsewhere (e.g. provisional pack) but its "
                f"body text has not been imported into the Legal Library."
            ),
        )

    prefix = rid.split("_", 1)[0].upper()
    return _parse_by_code(prefix, path)


def corpus_stats() -> Dict[str, Any]:
    idx = build_index()
    counts: Dict[str, int] = {c: 0 for c in SUPPORTED_CODES}
    for rid in idx.keys():
        prefix = rid.split("_", 1)[0].upper()
        if prefix in counts:
            counts[prefix] += 1
    return {
        "root": str(_canonical_root()),
        "total_records": sum(counts.values()),
        "by_code": counts,
        "supported_codes": list(SUPPORTED_CODES),
        "missing_codes_hint": "CCP, CIV and other statutes are not present in this corpus.",
    }
