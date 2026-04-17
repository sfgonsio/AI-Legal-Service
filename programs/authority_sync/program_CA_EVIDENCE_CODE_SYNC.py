import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]

BASE_URL = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"
LAW_CODE = "EVID"

AUTHORITY_ID = "CA_EVIDENCE_CODE"
AUTHORITY_ROOT = REPO_ROOT / "authority_store" / "ca" / "evidence_code"
CURRENT_DIR = AUTHORITY_ROOT / "current"
SECTIONS_DIR = CURRENT_DIR / "sections"
RUNS_DIR = AUTHORITY_ROOT / "runs"
MANIFEST_PATH = CURRENT_DIR / "section_sync_manifest.json"

USER_AGENT = "Mozilla/5.0"

SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch_url(url: str) -> str | None:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                return None
            raw = resp.read()
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return None


def is_valid_section_page(html_text: str) -> bool:
    if not html_text:
        return False

    lowered = html_text.lower()
    reject_markers = [
        "no section found",
        "page not found",
        "internal server error",
    ]
    if any(marker in lowered for marker in reject_markers):
        return False

    return ("lawCode=EVID" in html_text) or ("Evidence Code" in html_text) or ("EVID" in html_text)


def build_url(section_num: int) -> str:
    return f"{BASE_URL}?sectionNum={section_num}.&lawCode={LAW_CODE}"


def write_section_json(section_num: int, source_url: str, html_text: str, run_id: str) -> Path:
    section_id = f"EVID_{section_num}"
    citation = f"Evid. Code § {section_num}"

    payload = {
        "authority_id": AUTHORITY_ID,
        "section_id": section_id,
        "section_number": str(section_num),
        "citation": citation,
        "title": "",
        "text": "",
        "source_url": source_url,
        "source_label": "California Evidence Code",
        "captured_at": utc_now_iso(),
        "html_sha256": sha256_text(html_text),
        "text_sha256": "",
        "run_id": run_id,
        "raw_html_path": str(SECTIONS_DIR / f"{section_id}.html"),
    }

    html_path = SECTIONS_DIR / f"{section_id}.html"
    json_path = SECTIONS_DIR / f"{section_id}.json"

    html_path.write_text(html_text, encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return json_path


def run_probe(start: int = 100, end: int = 1700) -> dict:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    found_sections: list[int] = []
    section_files: list[str] = []
    failures: list[dict] = []

    for i in range(start, end + 1):
        print(f"Checking §{i}...")
        url = build_url(i)
        html_text = fetch_url(url)

        if html_text and is_valid_section_page(html_text):
            json_path = write_section_json(i, url, html_text, run_id)
            found_sections.append(i)
            section_files.append(str(json_path))
            print(f"  FOUND §{i}")
        else:
            failures.append({"section_number": i, "source_url": url, "reason": "missing_or_invalid"})
            print(f"  MISSING §{i}")

    manifest = {
        "authority_id": AUTHORITY_ID,
        "run_id": run_id,
        "captured_at": utc_now_iso(),
        "source_pattern": f"{BASE_URL}?sectionNum=<N>.&lawCode={LAW_CODE}",
        "section_count": len(found_sections),
        "sections": found_sections,
        "section_files": section_files,
        "failures_sample": failures[:50],
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    return manifest


if __name__ == "__main__":
    result = run_probe(100, 1700)
    print(f"[CA_EVIDENCE_CODE_SYNC] sections={result['section_count']} manifest={MANIFEST_PATH}")