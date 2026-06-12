"""
Rule-based actor extractor. Runs during the ingest pipeline (not analysis).

Input:  normalized document text + existing case actors.
Output: list of ExtractedActor records (new or matched existing).

Deterministic. No LLM. No imports from authority-resolution modules.
Enforced by SR-12.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


# ----- deterministic patterns -----

# Proper-noun phrase: 2-4 Title-cased tokens (names) OR single-token "Mr. X" etc.
# We restrict to bigrams+ to reduce noise; single-token names are hard without NER.
_NAME_RE = re.compile(
    r"\b(?:(?:Mr|Mrs|Ms|Dr|Hon|Judge|Attorney|Counsel|Rev|Prof|Sen|Rep|Gov)\.\s+)?"
    r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b"
)

_ORG_SUFFIX_RE = re.compile(
    r"\b[A-Z][\w&\-,\.]*(?:\s+[A-Z][\w&\-,\.]*)*\s+"
    r"(Inc\.?|LLC|L\.L\.C\.?|Corp\.?|Corporation|Company|Co\.|Partnership|LP|PLC|GmbH|Ltd\.?)\b"
)

# Common false-positive starts to reject outright.
_STOP_PHRASES = {
    "best regards", "kind regards", "warm regards", "yours truly", "yours sincerely",
    "sincerely yours", "thank you", "from the", "to the", "in the", "on the",
    "dear sir", "dear madam", "attention please", "this document", "this agreement",
    "exhibit a", "exhibit b", "exhibit c", "schedule a", "schedule b",
}

_STOP_WORDS = {
    "the", "and", "of", "for", "with", "from", "to", "on", "in", "at", "by",
    "is", "are", "was", "were", "be", "been", "being",
    # month names and days (often Title-cased, rarely a person)
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
}


_TITLE_PREFIX_RE = re.compile(r"^(?:Mr|Mrs|Ms|Dr|Hon|Judge|Attorney|Counsel|Rev|Prof|Sen|Rep|Gov)\.\s+")


def canonicalize(name: str) -> str:
    """Lowercase, strip titles + punctuation, collapse whitespace."""
    n = _TITLE_PREFIX_RE.sub("", name.strip())
    n = re.sub(r"[,\.]", "", n)
    n = re.sub(r"\s+", " ", n)
    return n.strip().lower()


def _is_stop(candidate: str) -> bool:
    cl = candidate.strip().lower()
    if cl in _STOP_PHRASES:
        return True
    parts = cl.split()
    if any(p in _STOP_WORDS for p in parts):
        # still keep if more than half tokens are non-stop
        nonstop = sum(1 for p in parts if p not in _STOP_WORDS)
        if nonstop < max(1, len(parts) - 1):
            return True
    return False


@dataclass
class ExtractedActor:
    display_name: str
    canonical: str
    entity_type: str  # PERSON | ORGANIZATION
    snippet: str
    offset_start: int
    offset_end: int
    confidence: float


def _snippet(text: str, start: int, end: int, pad: int = 40) -> str:
    a = max(0, start - pad)
    b = min(len(text), end + pad)
    return text[a:b].replace("\n", " ").strip()


def extract_actors(text: str) -> List[ExtractedActor]:
    """
    Return deduplicated extracted actors for a single document's normalized text.
    Deduplication is within-document; cross-document matching happens at persist
    time in brain.ingest_pipeline.
    """
    if not text:
        return []

    found: dict = {}  # canonical -> ExtractedActor (first hit wins, mention counted later)

    # Organizations first (more specific suffix pattern)
    for m in _ORG_SUFFIX_RE.finditer(text):
        raw = m.group(0)
        canon = canonicalize(raw)
        if not canon or len(canon) < 3 or _is_stop(raw):
            continue
        if canon not in found:
            found[canon] = ExtractedActor(
                display_name=raw,
                canonical=canon,
                entity_type="ORGANIZATION",
                snippet=_snippet(text, m.start(), m.end()),
                offset_start=m.start(),
                offset_end=m.end(),
                confidence=0.75,
            )

    # People
    for m in _NAME_RE.finditer(text):
        raw = m.group(0)
        canon = canonicalize(raw)
        if not canon or len(canon) < 3 or _is_stop(raw):
            continue
        if canon in found:
            continue
        # If this span lies inside an already-matched org, skip.
        if any(o.offset_start <= m.start() < o.offset_end for o in found.values()):
            continue
        found[canon] = ExtractedActor(
            display_name=raw,
            canonical=canon,
            entity_type="PERSON",
            snippet=_snippet(text, m.start(), m.end()),
            offset_start=m.start(),
            offset_end=m.end(),
            confidence=0.65 if _TITLE_PREFIX_RE.match(raw) else 0.55,
        )

    return list(found.values())


def resolve_against_existing(
    extracted: Iterable[ExtractedActor],
    existing_canonicals: dict,
) -> List[Tuple[ExtractedActor, Optional[int], str]]:
    """
    For each extracted actor, decide the resolution state against existing
    actors in the case.

    existing_canonicals: {canonical_name: actor_id}

    Returns list of (extracted, existing_actor_id_or_None, state)
      state in {RESOLVED, CANDIDATE, AMBIGUOUS}
    """
    out = []
    for ex in extracted:
        # Exact match -> RESOLVED against existing row.
        hit = existing_canonicals.get(ex.canonical)
        if hit is not None:
            out.append((ex, hit, "RESOLVED"))
            continue
        # Fuzzy: substring containment (simple, deterministic).
        fuzzy = [aid for c, aid in existing_canonicals.items()
                 if c != ex.canonical and (ex.canonical in c or c in ex.canonical)]
        if len(fuzzy) == 1:
            out.append((ex, fuzzy[0], "RESOLVED"))
        elif len(fuzzy) > 1:
            out.append((ex, None, "AMBIGUOUS"))
        else:
            out.append((ex, None, "CANDIDATE"))
    return out
