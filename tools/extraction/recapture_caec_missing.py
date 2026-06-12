"""Targeted recapture for CA Evidence Code sections missed by the prior crawl.

Reads the authoritative section list (built by enumerate_caec_authoritative.py),
diffs against the on-disk record set, and fetches HTML only for sections that
appear in the authoritative list but have no record on disk. Polite: 1.0s sleep
between fetches.

Output:
  authority_store/ca/evidence_code/current/sections/EVID_<NUM>.html  (new files)

It does NOT write JSON or update the manifest — repair_caec.py is the
canonical normalizer. Run that next.
"""
from __future__ import annotations

import json
import pathlib
import time
import urllib.request
from datetime import datetime, timezone

WORKTREE_ROOT = pathlib.Path(
    r"C:\Users\sfgon\Documents\GitHub\AI Legal Service\.claude\worktrees\youthful-johnson-1ee1a2"
)
AUTH_LIST_PATH = (
    WORKTREE_ROOT / "tmp_extraction" / "leginfo_probe" / "caec_authoritative_sections.json"
)
# Section HTML lives in the REAL repo authority_store (where the prior crawl wrote them).
SECTIONS_DIR = pathlib.Path(
    r"C:\Users\sfgon\Documents\GitHub\AI Legal Service"
    r"\authority_store\ca\evidence_code\current\sections"
)

URL_TMPL = (
    "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"
    "?lawCode=EVID&sectionNum={num}."
)
USER_AGENT = "casecore-authority-builder/1.0 (+legal-research; polite=1qps)"
SLEEP = 1.0
TIMEOUT = 30


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.status, resp.read()


def main() -> int:
    if not AUTH_LIST_PATH.exists():
        print(f"[error] authoritative list missing: {AUTH_LIST_PATH}")
        print("[hint] run enumerate_caec_authoritative.py first")
        return 1

    auth = json.loads(AUTH_LIST_PATH.read_text(encoding="utf-8"))
    auth_sections = set(auth["sections"])

    # Existing on-disk records (any HTML present, regardless of validity).
    on_disk = set()
    for p in SECTIONS_DIR.glob("EVID_*.html"):
        # Strip "EVID_" prefix and ".html" suffix.
        on_disk.add(p.stem.removeprefix("EVID_"))

    targets = sorted(
        auth_sections - on_disk,
        key=lambda s: (float(s) if "." in s else int(s)),
    )
    print(f"[info] authoritative sections: {len(auth_sections)}")
    print(f"[info] on-disk html files: {len(on_disk)}")
    print(f"[info] targets to fetch: {len(targets)}")

    if not targets:
        print("[done] nothing to fetch")
        return 0

    fetched = 0
    failed: list[tuple[str, str]] = []
    for sec in targets:
        url = URL_TMPL.format(num=sec)
        out_path = SECTIONS_DIR / f"EVID_{sec}.html"
        try:
            status, body = fetch(url)
        except Exception as e:
            failed.append((sec, str(e)))
            print(f"[warn] EVID {sec}: fetch failed: {e}")
            time.sleep(SLEEP)
            continue
        out_path.write_bytes(body)
        fetched += 1
        print(f"[ok]   EVID {sec} -> {len(body)} bytes")
        time.sleep(SLEEP)

    print()
    print(f"[done] fetched: {fetched}, failed: {len(failed)}")
    if failed:
        for sec, err in failed:
            print(f"  failed: EVID {sec}: {err}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
