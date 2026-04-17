import json
import re
import hashlib
from html import unescape
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

REPO_ROOT = Path(r"C:\Users\sfgon\Documents\GitHub\AI Legal Service")
BASE_URL = "https://leginfo.legislature.ca.gov"
TOC_URL = BASE_URL + "/faces/codedisplayexpand.xhtml?tocCode=EVID"

OUT_ROOT = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current"
PAGES_DIR = OUT_ROOT / "pages_official_group"
SECTIONS_DIR = OUT_ROOT / "sections_official_group"
MANIFEST = OUT_ROOT / "section_sync_manifest_official_group.json"

PAGES_DIR.mkdir(parents=True, exist_ok=True)
SECTIONS_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0"
})

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def sha256_text(v: str) -> str:
    return hashlib.sha256(v.encode("utf-8")).hexdigest()

def norm(v: str) -> str:
    v = unescape(v)
    v = v.replace("Â§", "§").replace("Â", "")
    v = re.sub(r"\s+", " ", v).strip()
    return v

def get(url: str) -> str:
    r = SESSION.get(url, timeout=30)
    r.raise_for_status()
    return r.text

def extract_group_links(toc_html: str):
    soup = BeautifulSoup(toc_html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "codes_displayText.xhtml" in href:
            full = urljoin(BASE_URL, href)
            label = norm(a.get_text(" ", strip=True))
            links.append((full, label))
    seen = set()
    out = []
    for full, label in links:
        if full not in seen:
            seen.add(full)
            out.append((full, label))
    return out

def trim_to_code_text(text: str) -> str:
    marker = "Code Text"
    idx = text.find(marker)
    if idx >= 0:
        text = text[idx:]
    return text

def strip_ui(text: str) -> str:
    bad = [
        "Code: Select Code",
        "Quick Search",
        "Bill Number",
        "Bill Keyword",
        "Home Bill Information California Law Publications Other Resources My Subscriptions My Favorites",
        "Code Search",
        "Text Search",
        "Up^",
        "Add To My Favorites",
        "Search Phrase:",
        "cross-reference chaptered bills PDF",
        "<< Previous",
        "Next >>"
    ]
    for b in bad:
        text = text.replace(b, " ")
    return norm(text)

def split_sections(text: str):
    # matches 720. or 1037.8.
    pat = re.compile(r'(?<!\w)(\d+(?:\.\d+)?)\.\s')
    matches = list(pat.finditer(text))
    out = []
    for i, m in enumerate(matches):
        sec = m.group(1)
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if len(chunk) < 40:
            continue
        # keep only chunks that look like statutes
        if "(Enacted by Stats." in chunk or "(Amended by Stats." in chunk or len(chunk) > 120:
            out.append((sec, chunk))
    return out

def main():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    toc_html = get(TOC_URL)
    group_links = extract_group_links(toc_html)

    section_count = 0
    pages = []

    for idx, (url, label) in enumerate(group_links, start=1):
        html = get(url)
        page_file = PAGES_DIR / f"group_{idx:03d}.html"
        page_file.write_text(html, encoding="utf-8")

        soup = BeautifulSoup(html, "html.parser")
        text = norm(soup.get_text("\n", strip=True))
        text = trim_to_code_text(text)
        text = strip_ui(text)

        parsed = 0
        for sec, chunk in split_sections(text):
            record = {
                "authority_id": "CA_EVIDENCE_CODE",
                "section_id": f"EVID_{sec}",
                "section_number": sec,
                "citation": f"Evid. Code § {sec}",
                "title": "",
                "text": chunk,
                "source_url": url,
                "source_label": label,
                "captured_at": now_iso(),
                "html_sha256": sha256_text(html),
                "text_sha256": sha256_text(chunk),
                "run_id": run_id,
                "raw_html_path": str(page_file)
            }
            out_file = SECTIONS_DIR / f"EVID_{sec}.json"
            out_file.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
            parsed += 1
            section_count += 1

        pages.append({
            "source_url": url,
            "source_label": label,
            "page_file": str(page_file),
            "html_sha256": sha256_text(html),
            "parsed_sections": parsed
        })
        print(f"[OK] parsed_sections={parsed} :: {label}")

    manifest = {
        "authority_id": "CA_EVIDENCE_CODE",
        "run_id": run_id,
        "generated_at": now_iso(),
        "source_toc_url": TOC_URL,
        "page_count": len(group_links),
        "section_count": section_count,
        "pages": pages
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[COMPLETE] section_count={section_count} manifest={MANIFEST}")

if __name__ == "__main__":
    main()
