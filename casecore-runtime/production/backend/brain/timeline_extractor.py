"""
Timeline event extractor — deterministic, rule-based, stdlib-only.

Does NOT call the authority resolver, COA engine, burden builder, remedy
derivation, or complaint parse. Safe to run during save-path extensions or
on-demand /timeline/{case_id}/build.

Input:  normalized text (any source).
Output: List[ExtractedEvent].
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Tuple


# ---------- date tokens ----------

MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

_MONTH_RE = r"(?:January|Jan|February|Feb|March|Mar|April|Apr|May|June|Jun|July|Jul|August|Aug|September|Sept|Sep|October|Oct|November|Nov|December|Dec)\.?"

# Patterns are matched in order and the first hit wins per span. Each pattern
# captures the full date span in group 0; named groups carry components.
_DATE_PATTERNS = [
    # "January 15, 2023" / "Jan 15 2023"
    re.compile(
        rf"\b(?P<mon>{_MONTH_RE})\s+(?P<day>\d{{1,2}})(?:st|nd|rd|th)?,?\s+(?P<year>\d{{4}})\b",
        re.IGNORECASE,
    ),
    # "15 January 2023"
    re.compile(
        rf"\b(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+(?P<mon>{_MONTH_RE})\s+(?P<year>\d{{4}})\b",
        re.IGNORECASE,
    ),
    # ISO: 2023-01-15
    re.compile(r"\b(?P<year>\d{4})-(?P<mon_n>\d{1,2})-(?P<day>\d{1,2})\b"),
    # US: 01/15/2023 or 1/15/23
    re.compile(r"\b(?P<mon_n>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{2,4})\b"),
    # Month + year only: "January 2023" / "Jan 2023"
    re.compile(
        rf"\b(?P<mon>{_MONTH_RE})\s+(?P<year>\d{{4}})\b",
        re.IGNORECASE,
    ),
    # Year only: "in 2022" — lower priority, requires the "in"/"of" anchor
    re.compile(r"\b(?:in|of|during)\s+(?P<year>\d{4})\b", re.IGNORECASE),
]

# Precision levels (DAY > MONTH > YEAR > UNKNOWN)
PREC_DAY = "DAY"
PREC_MONTH = "MONTH"
PREC_YEAR = "YEAR"
PREC_UNKNOWN = "UNKNOWN"


@dataclass
class ParsedDate:
    timestamp: Optional[datetime]
    raw_text: str
    precision: str
    span: Tuple[int, int]   # offsets in source text


def _parse_match(m: re.Match) -> Optional[ParsedDate]:
    gd = m.groupdict()
    raw = m.group(0)
    span = m.span()

    year = gd.get("year")
    if year is None:
        return None
    try:
        y = int(year)
        if y < 100:
            y += 2000 if y < 50 else 1900  # two-digit years -> 19xx/20xx
    except ValueError:
        return None

    # Month
    m_num = None
    if gd.get("mon_n"):
        try:
            m_num = int(gd["mon_n"])
        except ValueError:
            pass
    elif gd.get("mon"):
        m_num = MONTHS.get(gd["mon"].lower().strip("."))
    day_s = gd.get("day")

    if m_num and day_s:
        try:
            d = int(day_s)
            ts = datetime(y, m_num, d)
            return ParsedDate(ts, raw, PREC_DAY, span)
        except (ValueError, OverflowError):
            return None
    if m_num:
        try:
            ts = datetime(y, m_num, 1)
            return ParsedDate(ts, raw, PREC_MONTH, span)
        except ValueError:
            return None
    # Year only
    try:
        ts = datetime(y, 1, 1)
        return ParsedDate(ts, raw, PREC_YEAR, span)
    except ValueError:
        return None


def find_dates(text: str) -> List[ParsedDate]:
    """Scan text for date mentions. Returns non-overlapping spans, best precision wins."""
    if not text:
        return []
    hits: List[ParsedDate] = []
    taken: List[Tuple[int, int]] = []

    def overlaps(a: Tuple[int, int]) -> bool:
        for s, e in taken:
            if not (a[1] <= s or a[0] >= e):
                return True
        return False

    for pat in _DATE_PATTERNS:
        for m in pat.finditer(text):
            pd = _parse_match(m)
            if pd is None:
                continue
            if overlaps(pd.span):
                continue
            hits.append(pd)
            taken.append(pd.span)
    hits.sort(key=lambda p: p.span[0])
    return hits


# ---------- event classification ----------

_EVENT_KEYWORDS = [
    ("COMMUNICATION", r"\b(email|emailed|wrote|called|phoned|letter|texted|messaged|voicemail|correspondence|notified|notice|spoke|conversation)\b"),
    ("MEETING",        r"\b(met|meeting|attended|conference|deposition|hearing|mediation)\b"),
    ("PAYMENT",        r"\b(paid|payment|wired|transferred|deposit(?:ed)?|received|disbursed|\$[\d,]+)\b"),
    ("FILING",         r"\b(filed|filing|complaint|lawsuit|petition|motion|pleading|served|service of process)\b"),
    ("NOTICE",         r"\b(notice|notified|demand letter|cease and desist|warning)\b"),
    ("AGREEMENT",      r"\b(agreement|contract|signed|executed|amendment|addendum|MOU|term sheet|settled|settlement)\b"),
    ("BREACH",         r"\b(breached|breach|default(?:ed)?|missed|failed to|refused to)\b"),
    ("TRANSACTION",    r"\b(purchase|bought|sold|sale|acquired|lease|loan|invoice)\b"),
]
_EVENT_RES = [(label, re.compile(pat, re.IGNORECASE)) for label, pat in _EVENT_KEYWORDS]


def classify_event(sentence: str) -> str:
    for label, rx in _EVENT_RES:
        if rx.search(sentence):
            return label
    return "OTHER"


# ---------- sentence slicing ----------

_SENT_SPLIT = re.compile(r"(?<=[\.\?\!])\s+(?=[A-Z0-9\[])")


def _sentences_with_offsets(text: str) -> List[Tuple[int, int, str]]:
    """Split text into sentences, preserving (start, end, text) offsets."""
    if not text:
        return []
    out: List[Tuple[int, int, str]] = []
    # simple: find sentence boundaries
    last = 0
    for m in _SENT_SPLIT.finditer(text):
        end = m.start()
        if end > last:
            out.append((last, end, text[last:end]))
        last = m.end()
    if last < len(text):
        out.append((last, len(text), text[last:]))
    return out


# ---------- public: extract events ----------

@dataclass
class ExtractedEvent:
    summary: str
    raw_date_text: Optional[str]
    timestamp: Optional[datetime]
    date_precision: str           # DAY | MONTH | YEAR | UNKNOWN
    event_type: str               # from classifier
    snippet: str
    offset_start: int
    offset_end: int
    # Raw names found in the sentence; caller resolves to actor ids.
    mentioned_names: List[str] = field(default_factory=list)
    confidence: float = 0.0


# Very light name heuristic — mirrors actor_extractor. Kept local to avoid a
# cross-module coupling that would violate SR-12 only in appearance.
_NAME_RE = re.compile(
    r"\b(?:(?:Mr|Mrs|Ms|Dr|Hon|Judge|Attorney|Counsel|Rev|Prof|Sen|Rep|Gov)\.\s+)?"
    r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b"
)
_ORG_RE = re.compile(
    r"\b[A-Z][\w&\-,\.]*(?:\s+[A-Z][\w&\-,\.]*)*\s+"
    r"(Inc\.?|LLC|L\.L\.C\.?|Corp\.?|Corporation|Company|Co\.|Partnership|LP|PLC|GmbH|Ltd\.?)\b"
)


def _names_in(sentence: str) -> List[str]:
    out: List[str] = []
    seen = set()
    for m in _ORG_RE.finditer(sentence):
        s = m.group(0).strip()
        if s.lower() not in seen:
            out.append(s)
            seen.add(s.lower())
    for m in _NAME_RE.finditer(sentence):
        s = m.group(0).strip()
        if s.lower() in seen:
            continue
        out.append(s)
        seen.add(s.lower())
    return out


def _clean_summary(sent: str, max_len: int = 220) -> str:
    s = re.sub(r"\s+", " ", sent).strip()
    if len(s) <= max_len:
        return s
    return s[:max_len - 1].rstrip() + "\u2026"


def _confidence_for(precision: str, has_keyword: bool, has_names: bool) -> float:
    base = {"DAY": 0.85, "MONTH": 0.70, "YEAR": 0.55, "UNKNOWN": 0.35}[precision]
    if has_keyword:
        base = min(0.95, base + 0.05)
    if has_names:
        base = min(0.97, base + 0.05)
    return round(base, 2)


def extract_events(text: str) -> List[ExtractedEvent]:
    """
    Scan text, yield one ExtractedEvent per sentence that either contains a
    parseable date OR matches an event keyword. Sentences without dates still
    produce events with timestamp=None (UNKNOWN bucket) so nothing is silently
    dropped.
    """
    if not text:
        return []
    out: List[ExtractedEvent] = []
    sentences = _sentences_with_offsets(text)
    for start, end, sent in sentences:
        if not sent.strip():
            continue
        dates = find_dates(sent)
        etype = classify_event(sent)
        has_kw = etype != "OTHER"
        # Skip sentences that are neither dated nor event-keyword-bearing —
        # keeps the timeline focused.
        if not dates and not has_kw:
            continue

        names = _names_in(sent)

        if dates:
            # Use the first best-precision hit as the event's date anchor.
            # Higher precision wins.
            best = max(dates, key=lambda p: {"DAY": 3, "MONTH": 2, "YEAR": 1, "UNKNOWN": 0}[p.precision])
            conf = _confidence_for(best.precision, has_kw, bool(names))
            out.append(ExtractedEvent(
                summary=_clean_summary(sent),
                raw_date_text=best.raw_text,
                timestamp=best.timestamp,
                date_precision=best.precision,
                event_type=etype,
                snippet=_clean_summary(sent, max_len=300),
                offset_start=start,
                offset_end=end,
                mentioned_names=names,
                confidence=conf,
            ))
        else:
            conf = _confidence_for("UNKNOWN", has_kw, bool(names))
            out.append(ExtractedEvent(
                summary=_clean_summary(sent),
                raw_date_text=None,
                timestamp=None,
                date_precision=PREC_UNKNOWN,
                event_type=etype,
                snippet=_clean_summary(sent, max_len=300),
                offset_start=start,
                offset_end=end,
                mentioned_names=names,
                confidence=conf,
            ))
    return out
