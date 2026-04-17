import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set
from urllib.parse import urljoin
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORITY_ID = "CA_EVIDENCE_CODE"
AUTHORITY_ROOT = REPO_ROOT / "authority_store" / "ca" / "evidence_code"
CURRENT_DIR = AUTHORITY_ROOT / "current"
SECTIONS_DIR = CURRENT_DIR / "sections"
PAGES_DIR = CURRENT_DIR / "pages"
RUNS_DIR = AUTHORITY_ROOT / "runs"

CODE_MANIFEST = CURRENT_DIR / "code_manifest.json"
SECTION_SYNC_MANIFEST = CURRENT_DIR / "section_sync_manifest.json"
TOC_JSON = CURRENT_DIR / "toc.json"

BASE_URL = "https://leginfo.legislature.ca.gov"
TOC_URL = "https://leginfo.legislature.ca.gov/faces/codesTOCSelected.xhtml?tocCode=EVID"
USER_AGENT = "Mozilla/5.0"

SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
PAGES_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

def fetch_url(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urlopen(req, timeout=60) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")

def html_to_text(html_text: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html_text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<noscript.*?>.*?</noscript>", " ", text)
    text = re.sub(r"(?i)</?(div|p|br|li|tr|td|table|h1|h2|h3|h4|h5|h6|span)[^>]*>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def sanitize_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value.strip("_") or "page"

def extract_toc_links(toc_html: str) -> List[Dict[str, str]]:
    links: List[Dict[str, str]] = []
    seen: Set[str] = set()

    pattern = re.compile(
        r'<a[^>]+href="([^"]*codes_displayText\.xhtml\?[^"]*lawCode=EVID[^"]*)"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL
    )

    for match in pattern.finditer(toc_html):
        href = html.unescape(match.group(1))
        label_html = match.group(2)
        label = re.sub(r"(?is)<[^>]+>", " ", label_html)
        label = html.unescape(label)
        label = re.sub(r"\s+", " ", label).strip()

        full_url = urljoin(BASE_URL, href)

        if full_url in seen:
            continue
        seen.add(full_url)

        links.append({
            "href": full_url,
            "label": label
        })

    return links

def extract_section_number_from_text(page_text: str) -> str:
    patterns = [
        r"######\s*(\d{1,5}(?:\.\d+)?)",
        r"(?m)^\s*(\d{1,5}(?:\.\d+)?)\.\s+",
    ]
    for pattern in patterns:
        m = re.search(pattern, page_text)
        if m:
            return m.group(1)
    return ""

def parse_sections_from_text(page_text: str, source_url: str, run_id: str, html_sha: str) -> List[Dict[str, Any]]:
    section_pattern = re.compile(
        r'(?s)(?:######\s*(\d{1,5}(?:\.\d+)?)\s*\n+|\n\s*(\d{1,5}(?:\.\d+)?)\.\s+)(.*?)(?=(?:\n######\s*\d{1,5}(?:\.\d+)?\s*\n)|(?:\n\s*\d{1,5}(?:\.\d+)?\.\s+)|\Z)'
    )

    sections: List[Dict[str, Any]] = []

    for match in section_pattern.finditer(page_text):
        section_number = match.group(1) or match.group(2)
        body = match.group(3).strip()
        body = re.sub(r"\s+", " ", body).strip()

        if not section_number or not body:
            continue

        section_id = f"EVID_{section_number}"
        citation = f"Evid. Code § {section_number}"

        sections.append({
            "authority_id": AUTHORITY_ID,
            "section_id": section_id,
            "section_number": section_number,
            "citation": citation,
            "title": "",
            "text": body,
            "source_url": source_url,
            "source_label": "California Evidence Code",
            "captured_at": utc_now_iso(),
            "html_sha256": html_sha,
            "text_sha256": sha256_text(body),
            "run_id": run_id
        })

    return sections

def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    toc_html = fetch_url(TOC_URL)
    toc_sha = sha256_text(toc_html)

    toc_file = PAGES_DIR / "evidence_code_toc.html"
    toc_file.write_text(toc_html, encoding="utf-8")

    toc_links = extract_toc_links(toc_html)
    save_json(TOC_JSON, {
        "authority_id": AUTHORITY_ID,
        "captured_at": utc_now_iso(),
        "html_sha256": toc_sha,
        "url": TOC_URL,
        "links": toc_links
    })

    print(f"[CA_EVIDENCE_CODE_SECTION_SYNC] toc links discovered={len(toc_links)}")

    sections_written: List[str] = []
    pages_logged: List[Dict[str, Any]] = []
    failures: List[Dict[str, str]] = []
    seen_sections: Set[str] = set()

    for link in toc_links:
        source_url = link["href"]
        source_label = link["label"] or "EVID page"

        try:
            page_html = fetch_url(source_url)
            html_sha = sha256_text(page_html)

            page_slug = sanitize_filename(source_label)
            page_file = PAGES_DIR / f"{page_slug}.html"
            page_file.write_text(page_html, encoding="utf-8")

            page_text = html_to_text(page_html)
            parsed_sections = parse_sections_from_text(page_text, source_url, run_id, html_sha)

            pages_logged.append({
                "source_url": source_url,
                "source_label": source_label,
                "page_file": str(page_file),
                "html_sha256": html_sha,
                "parsed_sections": len(parsed_sections),
            })

            if not parsed_sections:
                failures.append({
                    "source_url": source_url,
                    "reason": "no_sections_parsed"
                })
                continue

            for section in parsed_sections:
                section_number = section["section_number"]
                if section_number in seen_sections:
                    continue
                seen_sections.add(section_number)

                out_file = SECTIONS_DIR / f"{section['section_id']}.json"
                save_json(out_file, section)
                sections_written.append(str(out_file))

            print(f"[PAGE] {source_label} parsed_sections={len(parsed_sections)}")

        except Exception as exc:
            failures.append({
                "source_url": source_url,
                "reason": f"fetch_or_parse_error: {exc}"
            })

    code_manifest = {
        "authority_id": AUTHORITY_ID,
        "title": "California Evidence Code",
        "source_url": TOC_URL,
        "captured_at": utc_now_iso(),
        "run_id": run_id,
        "html_sha256": toc_sha,
        "page_file": str(toc_file),
        "toc_link_count": len(toc_links),
    }

    sync_manifest = {
        "authority_id": AUTHORITY_ID,
        "run_id": run_id,
        "source_url": TOC_URL,
        "page_file": str(toc_file),
        "toc_link_count": len(toc_links),
        "section_count": len(sections_written),
        "section_files": sections_written,
        "failures": failures,
        "pages": pages_logged[:100]
    }

    save_json(CODE_MANIFEST, code_manifest)
    save_json(SECTION_SYNC_MANIFEST, sync_manifest)
    save_json(run_dir / "run_manifest.json", sync_manifest)

    print(f"[CA_EVIDENCE_CODE_SECTION_SYNC] sections={len(sections_written)} output={SECTION_SYNC_MANIFEST}")

if __name__ == "__main__":
    main()
