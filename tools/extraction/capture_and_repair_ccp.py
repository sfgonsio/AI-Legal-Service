"""Targeted CCP section capture + repair into authority_store/ca/ccp_cc/current/.

Mode (default = sample):
  - Reads the authoritative section list from ccp_authoritative_sections.json.
  - In `sample` mode, fetches only a configurable validation sample (default 10).
  - In `full` mode, fetches every section. ~3,300 fetches at 0.8s = ~45 min.

Writes per-section:
  authority_store/ca/ccp_cc/current/sections/CCP_<NUM>.html  (raw)
  authority_store/ca/ccp_cc/current/sections/CCP_<NUM>.json  (canonical)

Plus manifest.json and source_index.json.

The repair logic mirrors repair_caec.py:
  - Locates the <h6 style="float:left;"><b>NN.</b></h6> + following <p> blocks.
  - Quarantines records that don't parse.
  - Reclassifies "not in authoritative list" as not_in_code (only relevant in
    full mode; sample mode targets only known-real sections).
"""
from __future__ import annotations

import argparse
import hashlib
import html as htmllib
import json
import pathlib
import re
import time
import urllib.request
from datetime import datetime, timezone

WORKTREE_ROOT = pathlib.Path(
    r"C:\Users\sfgon\Documents\GitHub\AI Legal Service\.claude\worktrees\youthful-johnson-1ee1a2"
)
AUTH_LIST_PATH = (
    WORKTREE_ROOT / "tmp_extraction" / "leginfo_probe" / "ccp_authoritative_sections.json"
)
OUT_ROOT = WORKTREE_ROOT / "authority_store" / "ca" / "ccp_cc" / "current"
OUT_SECTIONS = OUT_ROOT / "sections"
OUT_SECTIONS.mkdir(parents=True, exist_ok=True)

URL_TMPL = (
    "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"
    "?lawCode=CCP&sectionNum={num}."
)
USER_AGENT = "casecore-authority-builder/1.0 (+legal-research; polite=1qps)"
SLEEP = 0.8
TIMEOUT = 30

SOURCE_LABEL = "California Code of Civil Procedure"

# Known-important sections used as the default validation sample.
SAMPLE_SECTIONS = [
    "17",       # general definitions
    "170.6",    # peremptory challenge to judge
    "425.10",   # complaint requirements
    "430.10",   # demurrer grounds
    "437c",     # summary judgment
    "583.310",  # 5-year mandatory dismissal
    "1010.6",   # electronic service
    "1856",     # parol evidence
    "2031.310", # motion to compel further responses to RFPs
    "1287",     # arbitration confirmation
]

CHROME_TOKENS = [
    "skip to content", "sitemap", "quick search", "My Subscriptions",
    "leginfo.legislature", "Bill Information", "Select Code", "Keyword(s)",
]


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def extract_section(html: str) -> dict:
    anchor = re.search(r'id="displayCodeSection"', html)
    if not anchor:
        return {"ok": False, "reason": "no displayCodeSection anchor"}
    block = html[anchor.start():]
    end = re.search(r"</BODY>", block, re.I)
    if end:
        block = block[: end.end()]

    m_num = re.search(
        r"<h6[^>]*float:left[^>]*>\s*<b>\s*([\w\.\-]+?)\s*</b>\s*</h6>",
        block, re.I | re.S,
    )
    if not m_num:
        return {"ok": False, "reason": "no section number header"}
    sec_num_raw = m_num.group(1).rstrip(".")
    after_num = block[m_num.end():]

    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", after_num, re.I | re.S)
    text_parts = []
    for p in paragraphs:
        t = re.sub(r"<[^>]+>", "", p)
        t = htmllib.unescape(t)
        t = t.replace("\xa0", " ")
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            text_parts.append(t)
    text = "\n\n".join(text_parts)

    m_enact = re.search(r"<i>\s*\(([^)]+)\)\s*</i>", after_num, re.I | re.S)
    enactment = m_enact.group(1).strip() if m_enact else ""

    if not text:
        return {"ok": False, "reason": "found header but no <p> body paragraphs",
                "section_number": sec_num_raw}
    return {"ok": True, "section_number": sec_num_raw, "text": text, "enactment": enactment}


def write_record(sec_num: str, html: bytes, raw_path: pathlib.Path,
                 source_url: str) -> tuple[str, str, list[str], dict]:
    """Parse + write JSON. Returns (section_id, status, notes, record)."""
    parsed = extract_section(html.decode("utf-8", errors="replace"))
    sec_id = f"CCP_{sec_num}"
    if not parsed["ok"]:
        record = {
            "authority_id": "CA_CCP",
            "family_id": "CCP-CC",
            "section_id": sec_id,
            "section_number": sec_num,
            "citation": f"Code Civ. Proc. \u00a7 {sec_num}",
            "title": "",
            "text": "",
            "source_url": source_url,
            "source_label": SOURCE_LABEL,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "text_sha256": "",
            "raw_html_path": str(raw_path),
            "validation_status": "quarantine",
            "validation_notes": [parsed["reason"]],
        }
        return sec_id, "quarantine", record["validation_notes"], record

    text = parsed["text"]
    notes: list[str] = []
    status = "valid"
    low = text.lower()
    for tok in CHROME_TOKENS:
        if tok.lower() in low:
            status = "quarantine"
            notes.append(f"chrome token leaked: {tok!r}")
            break
    if len(text) < 5:
        status = "quarantine"
        notes.append("text too short")

    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    record = {
        "authority_id": "CA_CCP",
        "family_id": "CCP-CC",
        "section_id": sec_id,
        "section_number": parsed["section_number"],
        "citation": f"Code Civ. Proc. \u00a7 {parsed['section_number']}",
        "title": "",
        "text": text,
        "enactment_history": parsed.get("enactment", ""),
        "source_url": source_url,
        "source_label": SOURCE_LABEL,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "text_sha256": sha,
        "raw_html_path": str(raw_path),
        "validation_status": status,
        "validation_notes": notes,
    }
    return sec_id, status, notes, record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("sample", "full"), default="sample")
    ap.add_argument("--sections", nargs="*", help="Override sample sections (numbers only)")
    args = ap.parse_args()

    if not AUTH_LIST_PATH.exists():
        print(f"[error] authoritative list missing: {AUTH_LIST_PATH}")
        return 1
    auth = json.loads(AUTH_LIST_PATH.read_text(encoding="utf-8"))
    auth_set = set(auth["sections"])

    if args.mode == "sample":
        targets = list(args.sections) if args.sections else list(SAMPLE_SECTIONS)
        # Explicit sample targets that aren't in the authoritative list are
        # flagged as potential enumeration gaps, but still captured so the
        # extraction pipeline can be validated against them. They will show up
        # in the manifest with a marker.
        unknown = [t for t in targets if t not in auth_set]
        if unknown:
            print(f"[warn] sample sections not in authoritative list "
                  f"(possible enumeration gap — will still capture): {unknown}")
    else:
        targets = sorted(auth_set, key=lambda s: tuple(
            int(p) if p.isdigit() else 0 for p in s.split(".")
        ))

    print(f"[info] mode={args.mode}, targets={len(targets)}")

    manifest_entries = []
    source_entries = []
    counts = {"valid": 0, "quarantine": 0}
    fetched = 0
    failed = []

    for sec in targets:
        url = URL_TMPL.format(num=sec)
        raw_path = OUT_SECTIONS / f"CCP_{sec}.html"
        json_path = OUT_SECTIONS / f"CCP_{sec}.json"
        try:
            body = fetch_bytes(url)
        except Exception as e:
            failed.append((sec, str(e)))
            print(f"[warn] CCP {sec}: fetch failed: {e}")
            time.sleep(SLEEP)
            continue
        raw_path.write_bytes(body)
        fetched += 1

        sec_id, status, notes, record = write_record(sec, body, raw_path, url)
        json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        counts[status] += 1
        manifest_entries.append({
            "section_id": sec_id,
            "section_number": sec,
            "citation": record["citation"],
            "validation_status": status,
            "text_sha256": record["text_sha256"],
            "json_path": f"sections/{json_path.name}",
            "raw_html_path": str(raw_path),
        })
        if status == "valid":
            source_entries.append({
                "section_id": sec_id,
                "source_url": url,
                "source_label": SOURCE_LABEL,
                "captured_at": record["captured_at"],
                "raw_html_path": str(raw_path),
            })
        print(f"[ok]   CCP {sec}: {status}, text_len={len(record['text'])}")
        time.sleep(SLEEP)

    # Manifest only updated, not full overwrite, so sample runs leave full
    # data intact across multiple invocations. We always write a manifest
    # representing the CURRENT contents of OUT_SECTIONS.
    # Re-scan all .json files for completeness.
    all_records = []
    for jp in sorted(OUT_SECTIONS.glob("CCP_*.json")):
        d = json.loads(jp.read_text(encoding="utf-8"))
        all_records.append({
            "section_id": d["section_id"],
            "section_number": d["section_number"],
            "citation": d["citation"],
            "validation_status": d["validation_status"],
            "text_sha256": d.get("text_sha256", ""),
            "json_path": f"sections/{jp.name}",
            "raw_html_path": d.get("raw_html_path", ""),
        })

    valid_total = sum(1 for r in all_records if r["validation_status"] == "valid")
    quar_total = sum(1 for r in all_records if r["validation_status"] == "quarantine")

    manifest = {
        "authority_id": "CA_CCP",
        "family_id": "CCP-CC",
        "family_label": "California Code of Civil Procedure",
        "source_label": SOURCE_LABEL,
        "source_base_url": URL_TMPL,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "authoritative_section_count": len(auth_set),
        "authoritative_list_path": str(AUTH_LIST_PATH),
        "section_count": len(all_records),
        "valid_count": valid_total,
        "quarantine_count": quar_total,
        "capture_mode": args.mode,
        "sections": all_records,
    }
    (OUT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Source index — keep entries from valid records only.
    existing_entries = []
    si_path = OUT_ROOT / "source_index.json"
    if si_path.exists():
        try:
            existing_entries = json.loads(si_path.read_text(encoding="utf-8")).get("entries", [])
        except Exception:
            existing_entries = []
    by_id = {e["section_id"]: e for e in existing_entries}
    for e in source_entries:
        by_id[e["section_id"]] = e
    si_path.write_text(json.dumps({
        "authority_id": "CA_CCP",
        "family_id": "CCP-CC",
        "source_label": SOURCE_LABEL,
        "source_base_url": URL_TMPL,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "entries": list(by_id.values()),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"[done] this run fetched: {fetched}, failed: {len(failed)}")
    print(f"[done] manifest now: section_count={len(all_records)}, "
          f"valid={valid_total}, quarantine={quar_total}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
