import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORITY_ID = "CA_BPC_DIV10_CANNABIS"
AUTHORITY_ROOT = REPO_ROOT / "authority_store" / "ca" / "bpc" / "division_10_cannabis"
CURRENT_DIR = AUTHORITY_ROOT / "current"
TOC_JSON = CURRENT_DIR / "toc.json"
DIVISION_MANIFEST = CURRENT_DIR / "division_manifest.json"

SECTIONS_DIR = CURRENT_DIR / "sections"
PAGES_DIR = CURRENT_DIR / "pages"
RUNS_DIR = AUTHORITY_ROOT / "runs"

BASE_URL = "https://leginfo.legislature.ca.gov"

SECTION_MIN = 26000.0
SECTION_MAX = 26325.0

SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
PAGES_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

def sanitize_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "page"

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

    # Convert common block tags to line breaks
    text = re.sub(r"(?i)</?(div|p|br|li|tr|td|table|h1|h2|h3|h4|h5|h6)[^>]*>", "\n", text)

    # Strip all remaining tags
    text = re.sub(r"(?is)<[^>]+>", " ", text)

    text = html.unescape(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def looks_like_statute_line(line: str) -> bool:
    m = re.match(r"^(26\d{3}(?:\.\d+)?)(?:\.)?\s+", line)
    if not m:
        return False
    try:
        value = float(m.group(1))
        return SECTION_MIN <= value <= SECTION_MAX
    except ValueError:
        return False

def extract_section_starts(lines: List[str]) -> List[Tuple[int, str]]:
    starts: List[Tuple[int, str]] = []
    for idx, line in enumerate(lines):
        if looks_like_statute_line(line):
            sec = re.match(r"^(26\d{3}(?:\.\d+)?)", line).group(1)
            starts.append((idx, sec))
    return starts

def parse_sections_from_text(page_text: str, source_label: str, source_url: str, run_id: str, html_sha: str):
    # Find all section numbers like 26000, 26001, 26039.6 etc
    pattern = re.compile(r'(26\d{3}(?:\.\d+)?)\.\s+')

    matches = list(pattern.finditer(page_text))
    if not matches:
        return []

    sections = []

    for i, match in enumerate(matches):
        section_number = match.group(1)

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(page_text)

        text_block = page_text[start:end].strip()

        # Clean text
        text_block = re.sub(r'\s+', ' ', text_block).strip()

        if not text_block:
            continue

        section_id = f"BPC_{section_number}"
        citation = f"BPC § {section_number}"

        sections.append({
            "authority_id": AUTHORITY_ID,
            "section_id": section_id,
            "section_number": section_number,
            "citation": citation,
            "title": "",
            "text": text_block,
            "source_url": source_url,
            "source_label": source_label,
            "captured_at": utc_now_iso(),
            "html_sha256": html_sha,
            "text_sha256": sha256_text(text_block),
            "run_id": run_id
        })

    return sections

def choose_fetch_links(toc_payload: Dict[str, Any]) -> List[Dict[str, str]]:
    links = toc_payload.get("links", [])
    selected: List[Dict[str, str]] = []

    for item in links:
        href = (item.get("href") or "").strip()
        label = (item.get("label") or "").strip()

        if "codes_displayText.xhtml" not in href:
            continue

        if not label:
            continue

        if "DIVISION 10" in label.upper():
            continue

        if "Cannabis" in label or "CHAPTER" in label.upper() or "ARTICLE" in label.upper():
            selected.append({
                "href": href,
                "label": label
            })

    deduped: List[Dict[str, str]] = []
    seen = set()
    for item in selected:
        key = (item["href"], item["label"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped

def main() -> None:
    if not TOC_JSON.exists():
        raise FileNotFoundError(f"Missing toc.json: {TOC_JSON}")
    if not DIVISION_MANIFEST.exists():
        raise FileNotFoundError(f"Missing division_manifest.json: {DIVISION_MANIFEST}")

    toc_payload = load_json(TOC_JSON)
    division_manifest = load_json(DIVISION_MANIFEST)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    link_records = choose_fetch_links(toc_payload)
    if not link_records:
        raise RuntimeError("No fetchable Division 10 chapter/article links found in toc.json")

    print(f"[SECTION_SYNC] authority: {AUTHORITY_ID}")
    print(f"[SECTION_SYNC] fetch links discovered: {len(link_records)}")

    fetched_pages: List[Dict[str, Any]] = []
    unparsed_pages: List[Dict[str, Any]] = []
    sections_by_number: Dict[str, Dict[str, Any]] = {}

    for idx, link in enumerate(link_records, start=1):
        href = link["href"]
        label = link["label"]
        full_url = urljoin(BASE_URL, href)

        print(f"[SECTION_SYNC] fetching {idx}/{len(link_records)} :: {label}")

        try:
            page_html = fetch_url(full_url)
        except Exception as exc:
            unparsed_pages.append({
                "source_url": full_url,
                "source_label": label,
                "error": f"fetch failed: {exc}"
            })
            continue

        html_sha = sha256_text(page_html)
        page_slug = sanitize_filename(label)
        page_path = PAGES_DIR / f"{page_slug}.html"
        with open(page_path, "w", encoding="utf-8") as f:
            f.write(page_html)

        page_text = html_to_text(page_html)
        parsed_sections = parse_sections_from_text(
            page_text=page_text,
            source_label=label,
            source_url=full_url,
            run_id=run_id,
            html_sha=html_sha
        )

        fetched_pages.append({
            "source_url": full_url,
            "source_label": label,
            "page_file": str(page_path),
            "html_sha256": html_sha,
            "parsed_sections": len(parsed_sections)
        })

        if not parsed_sections:
            unparsed_pages.append({
                "source_url": full_url,
                "source_label": label,
                "error": "no sections parsed"
            })
            continue

        for section in parsed_sections:
            sec_no = section["section_number"]
            if sec_no not in sections_by_number:
                sections_by_number[sec_no] = section

    ordered_sections = sorted(
        sections_by_number.values(),
        key=lambda s: float(s["section_number"])
    )

    for section in ordered_sections:
        out_path = SECTIONS_DIR / f"{section['section_id']}.json"
        save_json(out_path, section)

    section_sync_manifest = {
        "authority_id": AUTHORITY_ID,
        "division_title": division_manifest.get("title", ""),
        "run_id": run_id,
        "generated_at": utc_now_iso(),
        "authority_current_dir": str(CURRENT_DIR),
        "sections_dir": str(SECTIONS_DIR),
        "pages_dir": str(PAGES_DIR),
        "source_toc_json": str(TOC_JSON),
        "source_division_manifest": str(DIVISION_MANIFEST),
        "fetch_link_count": len(link_records),
        "page_count": len(fetched_pages),
        "section_count": len(ordered_sections),
        "unparsed_pages": unparsed_pages,
        "pages": fetched_pages,
        "section_files": [str(SECTIONS_DIR / f"{s['section_id']}.json") for s in ordered_sections]
    }

    save_json(CURRENT_DIR / "section_sync_manifest.json", section_sync_manifest)
    save_json(run_dir / "run_manifest.json", section_sync_manifest)

    print(
        f"[SECTION_SYNC] complete :: pages={len(fetched_pages)} "
        f"sections={len(ordered_sections)} unparsed={len(unparsed_pages)}"
    )

if __name__ == "__main__":
    main()

