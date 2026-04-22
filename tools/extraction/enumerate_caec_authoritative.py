"""Authoritative enumeration of CA Evidence Code sections.

Walks leginfo's codes_displayText.xhtml tree (division -> chapter -> article).
Drills down only when a parent node returns no section markers, so most fetches
are skipped. Polite: 1.0s sleep between fetches.

Output:
  tmp_extraction/leginfo_probe/caec_authoritative_sections.json
    {
      "captured_at": "...",
      "source_base_url": "...",
      "fetched_node_count": N,
      "section_count": M,
      "sections": ["1","2",...,"1605"],
      "section_to_path": {"100": {"division":"2","chapter":null,"article":null}, ...}
    }

Usage:
  python tools/extraction/enumerate_caec_authoritative.py
"""
from __future__ import annotations

import json
import pathlib
import re
import time
import urllib.request
from datetime import datetime, timezone

PROBE_DIR = pathlib.Path(
    r"C:\Users\sfgon\Documents\GitHub\AI Legal Service\.claude\worktrees\youthful-johnson-1ee1a2\tmp_extraction\leginfo_probe"
)
PROBE_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = PROBE_DIR / "caec_authoritative_sections.json"

BASE = "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml"
LAW = "EVID"
SLEEP = 1.0
TIMEOUT = 30
USER_AGENT = "casecore-authority-builder/1.0 (+legal-research; polite=1qps)"

# Section-link marker in the displayText output:
#   <a href="javascript:submitCodesValues('NN.','...
SECTION_RE = re.compile(r"submitCodesValues\('([\d\.]+)'")

# Probe ranges (intentionally generous; tree-walk skips empty branches fast)
DIV_RANGE = list(range(1, 14))
CHAP_RANGE = list(range(1, 16))
ART_RANGE = list(range(1, 11))


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def url_for(division: str = "", chapter: str = "", article: str = "", part: str = "") -> str:
    return (
        f"{BASE}?lawCode={LAW}"
        f"&division={division}"
        f"&title=&part={part}"
        f"&chapter={chapter}"
        f"&article={article}"
    )


def parse_sections(html: str) -> set[str]:
    return {m.rstrip(".") for m in SECTION_RE.findall(html)}


def main() -> int:
    found_sections: dict[str, dict] = {}  # section_num -> path
    fetched = 0

    print(f"[info] enumerating EVID via {BASE}")
    for d in DIV_RANGE:
        d_str = f"{d}."
        url_d = url_for(division=d_str)
        try:
            status_d, html_d = fetch(url_d)
        except Exception as e:
            print(f"[warn] div {d}: fetch error: {e}")
            time.sleep(SLEEP)
            continue
        fetched += 1
        secs_d = parse_sections(html_d)
        # If the page itself has section markers, record them under the division.
        for s in secs_d:
            if s not in found_sections:
                found_sections[s] = {"division": str(d), "chapter": None, "article": None}
        time.sleep(SLEEP)

        # Heuristic: if division had at least one chapter beneath it (size > some
        # threshold and 0 sections), drill into chapters. If sections > 0 we may
        # still drill (some divisions mix flat sections with sub-chapters).
        # We always probe chapters; the cost is bounded by SLEEP * len(CHAP_RANGE).
        any_chapter_hit = False
        for c in CHAP_RANGE:
            c_str = f"{c}."
            url_c = url_for(division=d_str, chapter=c_str)
            try:
                status_c, html_c = fetch(url_c)
            except Exception as e:
                print(f"[warn] div {d} ch {c}: fetch error: {e}")
                time.sleep(SLEEP)
                continue
            fetched += 1
            secs_c = parse_sections(html_c)
            for s in secs_c:
                if s not in found_sections:
                    found_sections[s] = {
                        "division": str(d),
                        "chapter": str(c),
                        "article": None,
                    }
            time.sleep(SLEEP)
            if secs_c:
                any_chapter_hit = True
                # Drill articles if this chapter looks possibly nested.
                # (Cost: only when chapter exists.)
                for a in ART_RANGE:
                    a_str = f"{a}."
                    url_a = url_for(division=d_str, chapter=c_str, article=a_str)
                    try:
                        status_a, html_a = fetch(url_a)
                    except Exception as e:
                        print(f"[warn] div {d} ch {c} art {a}: fetch error: {e}")
                        time.sleep(SLEEP)
                        continue
                    fetched += 1
                    secs_a = parse_sections(html_a)
                    for s in secs_a:
                        if s not in found_sections:
                            found_sections[s] = {
                                "division": str(d),
                                "chapter": str(c),
                                "article": str(a),
                            }
                    time.sleep(SLEEP)
                    # Stop if article fetches start returning empty (likely past the end).
                    if not secs_a:
                        # Allow one empty (gap) before stopping.
                        try:
                            url_a2 = url_for(division=d_str, chapter=c_str, article=f"{a+1}.")
                            status_a2, html_a2 = fetch(url_a2)
                        except Exception:
                            break
                        fetched += 1
                        time.sleep(SLEEP)
                        if not parse_sections(html_a2):
                            break
            else:
                # Empty chapter — peek one more then stop if both empty (no more chapters).
                if not any_chapter_hit and c >= 3:
                    # First few chapters all empty: division has no chapter-level content.
                    break
                if any_chapter_hit and c >= 5:
                    # We've found content earlier; consecutive empties past 5 chapters
                    # means we've walked off the end of this division.
                    break
        print(
            f"[info] div {d}: fetched so far={fetched}, "
            f"sections discovered total={len(found_sections)}"
        )

    sorted_secs = sorted(
        found_sections.keys(),
        key=lambda s: (float(s) if "." in s else int(s)),
    )
    out = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source_base_url": BASE + f"?lawCode={LAW}&division=N.&chapter=N.&article=N.",
        "fetched_node_count": fetched,
        "section_count": len(sorted_secs),
        "sections": sorted_secs,
        "section_to_path": {s: found_sections[s] for s in sorted_secs},
    }
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[done] wrote {OUT_PATH}")
    print(f"[done] sections discovered: {len(sorted_secs)}, fetches used: {fetched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
