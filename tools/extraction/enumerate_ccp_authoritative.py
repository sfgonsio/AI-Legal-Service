"""Authoritative enumeration of CA Code of Civil Procedure (CCP) sections.

Strategy:
  1. Fetch the CCP code-tree page (codedisplayexpand.xhtml?tocCode=CCP), which
     embeds ~500 direct part/title/chapter URLs to displayText.xhtml.
  2. For each unique URL in that page, fetch the displayText response and
     extract section markers from the JSF onclick handlers
     (submitCodesValues('NN.', ...)).
  3. Polite: 0.8s sleep between fetches.

Output:
  tmp_extraction/leginfo_probe/ccp_authoritative_sections.json
"""
from __future__ import annotations

import html as htmllib
import json
import pathlib
import re
import time
import urllib.request
from datetime import datetime, timezone

PROBE_DIR = pathlib.Path(
    r"C:\Users\sfgon\Documents\GitHub\AI Legal Service\.claude\worktrees\youthful-johnson-1ee1a2"
    r"\tmp_extraction\leginfo_probe\ccp_probe"
)
PROBE_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = PROBE_DIR.parent / "ccp_authoritative_sections.json"

TOC_URL = "https://leginfo.legislature.ca.gov/faces/codedisplayexpand.xhtml?tocCode=CCP"
BASE = "https://leginfo.legislature.ca.gov/faces/"
USER_AGENT = "casecore-authority-builder/1.0 (+legal-research; polite=1qps)"
SLEEP = 0.8
TIMEOUT = 30

# Extract displayText URLs (with html-encoded ampersands)
URL_RE = re.compile(
    r'codes_displayText\.xhtml\?lawCode=CCP[^"\']+',
    re.I,
)
SECTION_RE = re.compile(r"submitCodesValues\('([\d\.]+)'")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    print(f"[info] fetching CCP code tree: {TOC_URL}")
    toc_html = fetch(TOC_URL)
    print(f"[info] toc size: {len(toc_html)}")

    # Extract URLs, decode html entities
    raw_urls = URL_RE.findall(toc_html)
    decoded = [htmllib.unescape(u) for u in raw_urls]
    # Drop the meaningless "all blank" URL
    unique = sorted({u for u in decoded if any(p in u for p in ("title=", "part=", "chapter="))
                     and not u.endswith("&division=&title=&part=&chapter=&article=")})
    print(f"[info] distinct part/title/chapter URLs: {len(unique)}")

    found_sections: dict[str, dict] = {}
    fetched = 0
    failed = []

    for i, suffix in enumerate(unique, 1):
        url = BASE + suffix
        try:
            html = fetch(url)
        except Exception as e:
            failed.append((suffix, str(e)))
            print(f"[warn] {i}/{len(unique)} fetch failed: {e}")
            time.sleep(SLEEP)
            continue
        fetched += 1
        secs = SECTION_RE.findall(html)
        # Parse params from suffix to record path
        params = {}
        for pair in suffix.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                if v.endswith("."):
                    v = v[:-1]
                if v:
                    params[k] = v
        for s in secs:
            num = s.rstrip(".")
            if num and num not in found_sections:
                found_sections[num] = {
                    "title": params.get("title"),
                    "part": params.get("part"),
                    "chapter": params.get("chapter"),
                    "article": params.get("article"),
                    "division": params.get("division"),
                }
        if i % 25 == 0 or i == len(unique):
            print(f"[info] {i}/{len(unique)} fetched, sections discovered: {len(found_sections)}")
        time.sleep(SLEEP)

    def _natkey(s: str):
        # Multi-dot section numbers (e.g. "874.321.5") need a tuple key.
        parts = s.split(".")
        out = []
        for p in parts:
            try:
                out.append(int(p))
            except ValueError:
                out.append(0)
        return tuple(out)

    sorted_secs = sorted(found_sections.keys(), key=_natkey)
    out = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source_toc_url": TOC_URL,
        "source_section_url_template": BASE + "codes_displayText.xhtml?lawCode=CCP&...",
        "fetched_node_count": fetched,
        "section_count": len(sorted_secs),
        "sections": sorted_secs,
        "section_to_path": {s: found_sections[s] for s in sorted_secs},
        "fetch_failures": failed,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[done] wrote {OUT_PATH}")
    print(f"[done] sections discovered: {len(sorted_secs)}, fetches used: {fetched}, failures: {len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
