import json
import re
import hashlib
from html import unescape
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

REPO_ROOT = Path(r"C:\Users\sfgon\Documents\GitHub\AI Legal Service")
BASE_URL = "https://leginfo.legislature.ca.gov"
START_URL = BASE_URL + "/faces/codedisplayexpand.xhtml?tocCode=EVID"

OUT_ROOT = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current"
PAGES_DIR = OUT_ROOT / "pages_official_recursive"
SECTIONS_DIR = OUT_ROOT / "sections_official_recursive"
MANIFEST = OUT_ROOT / "section_sync_manifest_official_recursive.json"
GROUP_LINKS_FILE = OUT_ROOT / "official_recursive_group_links.json"

PAGES_DIR.mkdir(parents=True, exist_ok=True)
SECTIONS_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

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

def is_evid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == "leginfo.legislature.ca.gov" and "lawCode=EVID" in url or "tocCode=EVID" in url

def extract_links(html: str, base: str):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base, a["href"])
        if not href.startswith(BASE_URL):
            continue
        if ("codedisplayexpand.xhtml" in href or "codes_displayText.xhtml" in href) and ("EVID" in href):
            out.append((href, norm(a.get_text(" ", strip=True))))
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
        "Next >>",
        "skip to content",
        "accessibility FAQ feedback sitemap login",
    ]
    for b in bad:
        text = text.replace(b, " ")
    return norm(text)

def split_sections(text: str):
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
        front = chunk[:250].lower()
        if any(bad in front for bad in [
            "quick search", "bill information", "my favorites",
            "select code", "skip to content", "keyword(s):"
        ]):
            continue
        if "(Enacted by Stats." in chunk or "(Amended by Stats." in chunk or len(chunk) > 120:
            out.append((sec, chunk))
    return out

def main():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    queue = [START_URL]
    visited = set()
    group_links = []
    group_seen = set()

    while queue:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            html = get(url)
        except Exception as exc:
            print(f"[WARN] failed fetch {url} :: {exc}")
            continue

        for href, label in extract_links(html, url):
            if "codes_displayText.xhtml" in href:
                if href not in group_seen:
                    group_seen.add(href)
                    group_links.append((href, label))
            elif "codedisplayexpand.xhtml" in href:
                if href not in visited and href not in queue:
                    queue.append(href)

    GROUP_LINKS_FILE.write_text(
        json.dumps(
            [{"source_url": u, "source_label": l} for u, l in group_links],
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    section_count = 0
    pages = []

    for idx, (url, label) in enumerate(group_links, start=1):
        try:
            html = get(url)
        except Exception as exc:
            pages.append({
                "source_url": url,
                "source_label": label,
                "error": str(exc),
                "parsed_sections": 0
            })
            print(f"[WARN] group fetch failed :: {label} :: {exc}")
            continue

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
        "start_url": START_URL,
        "visited_expand_pages": len(visited),
        "group_page_count": len(group_links),
        "section_count": section_count,
        "group_links_file": str(GROUP_LINKS_FILE),
        "pages": pages
    }

    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[COMPLETE] group_page_count={len(group_links)} section_count={section_count} manifest={MANIFEST}")

if __name__ == "__main__":
    main()
