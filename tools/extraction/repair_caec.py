"""Repair California Evidence Code (CAEC) extractions.

The existing authority_store/ca/evidence_code/current/sections/EVID_*.json files
contain site chrome (navigation menus, "skip to content", etc.) instead of the
actual statute text. The paired EVID_*.html files, however, DO contain the real
content inside a <div id="displayCodeSection"> block.

This script:
1. Walks every EVID_*.html file.
2. Extracts the section number, statute body, and enactment/history note.
3. Rewrites EVID_*.json with a canonical schema aligned to the user's spec.
4. Emits authority_store/ca/evidence_code/current/manifest.json and source_index.json.

Any HTML that cannot be parsed cleanly is routed to a quarantine marker
(validation_status != "valid") and flagged in the manifest rather than silently
replacing good existing content.
"""

from __future__ import annotations

import hashlib
import html as htmllib
import json
import pathlib
import re
import sys
from datetime import datetime, timezone
from typing import Optional

REPO_ROOT = pathlib.Path(
    r"C:\Users\sfgon\Documents\GitHub\AI Legal Service"
)
WORKTREE_ROOT = pathlib.Path(
    r"C:\Users\sfgon\Documents\GitHub\AI Legal Service\.claude\worktrees\youthful-johnson-1ee1a2"
)
SRC_SECTIONS = (
    REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current" / "sections"
)
OUT_ROOT = (
    WORKTREE_ROOT / "authority_store" / "ca" / "evidence_code" / "current"
)
OUT_SECTIONS = OUT_ROOT / "sections"
OUT_SECTIONS.mkdir(parents=True, exist_ok=True)

SOURCE_LABEL = "California Evidence Code"
SOURCE_BASE_URL = (
    "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"
    "?lawCode=EVID&sectionNum={num}."
)

CHROME_TOKENS = [
    "skip to content",
    "sitemap",
    "quick search",
    "My Subscriptions",
    "leginfo.legislature",
    "Bill Information",
    "Select Code",
    "Keyword(s)",
]


def extract_section(html: str) -> dict:
    """Return dict with 'section_number', 'text', 'enactment', 'ok', 'reason'."""
    # Locate the displayCodeSection div. Use a loose regex that tolerates
    # attribute order.
    anchor = re.search(r'id="displayCodeSection"', html)
    if not anchor:
        return {"ok": False, "reason": "no displayCodeSection anchor"}
    block = html[anchor.start():]
    # End at </BODY> or end of html
    end = re.search(r"</BODY>", block, re.I)
    if end:
        block = block[: end.end()]

    # Section number from <h6 ...><b>123.</b></h6>
    m_num = re.search(
        r"<h6[^>]*float:left[^>]*>\s*<b>\s*([\w\.\-]+?)\s*</b>\s*</h6>",
        block,
        re.I | re.S,
    )
    if not m_num:
        return {"ok": False, "reason": "no section number header"}
    sec_num_raw = m_num.group(1).rstrip(".")
    after_num = block[m_num.end():]

    # Collect the <p> paragraph bodies (actual statute text) that follow.
    paragraphs = re.findall(
        r"<p[^>]*>(.*?)</p>", after_num, re.I | re.S
    )
    text_parts = []
    for p in paragraphs:
        # Strip inline tags, decode entities, normalize whitespace
        t = re.sub(r"<[^>]+>", "", p)
        t = htmllib.unescape(t)
        t = t.replace("\xa0", " ")  # non-breaking space → regular space
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            text_parts.append(t)
    text = "\n\n".join(text_parts)

    # Enactment / legislative history: the first <i>...</i> after the section body
    m_enact = re.search(r"<i>\s*\(([^)]+)\)\s*</i>", after_num, re.I | re.S)
    enactment = m_enact.group(1).strip() if m_enact else ""

    if not text:
        return {
            "ok": False,
            "reason": "found header but no <p> body paragraphs",
            "section_number": sec_num_raw,
        }

    return {
        "ok": True,
        "section_number": sec_num_raw,
        "text": text,
        "enactment": enactment,
    }


def main() -> int:
    if not SRC_SECTIONS.exists():
        print(f"[error] source sections dir missing: {SRC_SECTIONS}")
        return 1

    manifest_entries = []
    source_entries = []
    counts = {"valid": 0, "quarantine": 0}
    skipped_chrome = []

    html_files = sorted(SRC_SECTIONS.glob("EVID_*.html"))
    print(f"[info] {len(html_files)} html files in source")

    for i, h in enumerate(html_files):
        html = h.read_text(encoding="utf-8", errors="replace")
        parsed = extract_section(html)
        out_name = h.name.replace(".html", ".json")
        out_path = OUT_SECTIONS / out_name

        if not parsed["ok"]:
            # Quarantine marker: write minimal JSON noting the failure.
            sec_num = parsed.get("section_number") or h.stem.replace("EVID_", "")
            record = {
                "authority_id": "CA_EVIDENCE_CODE",
                "family_id": "CAEC",
                "section_id": f"EVID_{sec_num}",
                "section_number": sec_num,
                "citation": f"Evid. Code \u00a7 {sec_num}",
                "title": "",
                "text": "",
                "source_url": SOURCE_BASE_URL.format(num=sec_num),
                "source_label": SOURCE_LABEL,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "text_sha256": "",
                "raw_html_path": str(h),
                "validation_status": "quarantine",
                "validation_notes": [parsed["reason"]],
            }
            counts["quarantine"] += 1
            out_path.write_text(
                json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            manifest_entries.append({
                "section_id": record["section_id"],
                "section_number": record["section_number"],
                "citation": record["citation"],
                "validation_status": "quarantine",
                "json_path": f"sections/{out_name}",
                "raw_html_path": str(h),
            })
            continue

        sec_num = parsed["section_number"]
        text = parsed["text"]

        # Sanity: reject chrome tokens if they somehow leaked into text
        low = text.lower()
        notes: list[str] = []
        status = "valid"
        for tok in CHROME_TOKENS:
            if tok.lower() in low:
                status = "quarantine"
                notes.append(f"chrome token leaked: {tok!r}")
                skipped_chrome.append(h.name)
                break
        if len(text) < 5:
            status = "quarantine"
            notes.append("text too short")

        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        citation = f"Evid. Code \u00a7 {sec_num}"
        record = {
            "authority_id": "CA_EVIDENCE_CODE",
            "family_id": "CAEC",
            "section_id": f"EVID_{sec_num}",
            "section_number": sec_num,
            "citation": citation,
            "title": "",
            "text": text,
            "enactment_history": parsed.get("enactment", ""),
            "source_url": SOURCE_BASE_URL.format(num=sec_num),
            "source_label": SOURCE_LABEL,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "text_sha256": sha,
            "raw_html_path": str(h),
            "validation_status": status,
            "validation_notes": notes,
        }
        counts[status] += 1
        out_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        manifest_entries.append({
            "section_id": record["section_id"],
            "section_number": record["section_number"],
            "citation": record["citation"],
            "validation_status": status,
            "text_sha256": sha,
            "json_path": f"sections/{out_name}",
            "raw_html_path": str(h),
        })
        source_entries.append({
            "section_id": record["section_id"],
            "source_url": record["source_url"],
            "source_label": SOURCE_LABEL,
            "captured_at": record["captured_at"],
            "raw_html_path": str(h),
        })

    # Sort manifest entries by section number (natural)
    def sortkey(e):
        s = e["section_number"]
        m = re.match(r"^(\d+)(.*)$", s)
        if m:
            return (int(m.group(1)), m.group(2))
        return (0, s)

    manifest_entries.sort(key=sortkey)

    manifest = {
        "authority_id": "CA_EVIDENCE_CODE",
        "family_id": "CAEC",
        "family_label": "California Evidence Code",
        "source_label": SOURCE_LABEL,
        "source_base_url": SOURCE_BASE_URL,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "section_count": len(manifest_entries),
        "valid_count": counts["valid"],
        "quarantine_count": counts["quarantine"],
        "sections": manifest_entries,
    }
    (OUT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    source_index = {
        "authority_id": "CA_EVIDENCE_CODE",
        "family_id": "CAEC",
        "source_label": SOURCE_LABEL,
        "source_base_url": SOURCE_BASE_URL,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "entries": source_entries,
    }
    (OUT_ROOT / "source_index.json").write_text(
        json.dumps(source_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"[done] sections processed: {len(manifest_entries)} "
        f"(valid={counts['valid']}, quarantine={counts['quarantine']})"
    )
    if skipped_chrome:
        print(f"[warn] {len(skipped_chrome)} chrome-leak samples: {skipped_chrome[:5]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
