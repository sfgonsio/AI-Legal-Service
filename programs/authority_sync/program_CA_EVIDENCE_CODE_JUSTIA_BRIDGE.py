import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[2]

INDEX_URL = "https://law.justia.com/codes/california/code-evid/"
BASE_DOMAIN = "https://law.justia.com"

CURRENT_DIR = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current"
SECTIONS_DIR = CURRENT_DIR / "sections_justia_bridge"
FAILURES_DIR = CURRENT_DIR / "failures_justia_bridge"
MANIFEST_PATH = CURRENT_DIR / "section_sync_manifest_justia_bridge.json"

SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
FAILURES_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.google.com/",
    "DNT": "1"
})

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def normalize_text(text: str) -> str:
    fixes = {
        "Â§": "§",
        "Â": "",
        "\u00a0": " ",
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_html(url: str) -> str:
    r = SESSION.get(url, timeout=30, allow_redirects=True)
    if r.status_code == 403:
        time.sleep(1.5)
        r = SESSION.get(url, timeout=30, allow_redirects=True)
    r.raise_for_status()
    return r.text

def is_code_path(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc.endswith("justia.com") and "/codes/california/code-evid/" in parsed.path

def collect_candidate_links(index_html: str) -> list[str]:
    soup = BeautifulSoup(index_html, "html.parser")
    links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = urljoin(INDEX_URL, a["href"])
        if not is_code_path(href):
            continue
        if href == INDEX_URL:
            continue
        if href in seen:
            continue
        seen.add(href)
        links.append(href)

    return links

def looks_like_section_url(url: str) -> bool:
    path = urlparse(url).path.rstrip("/")
    return bool(re.search(r"/section-\d+/?$", path))

def extract_section_number_from_url(url: str) -> str:
    m = re.search(r"/section-(\d+)/?$", urlparse(url).path.rstrip("/") + "/")
    return m.group(1) if m else ""

def extract_section_text(html: str, section_number: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    # Remove obvious junk
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    full_text = normalize_text(soup.get_text("\n", strip=True))

    start_match = re.search(rf"\b{re.escape(section_number)}\.\s", full_text)
    if not start_match:
        return "", ""

    body = full_text[start_match.start():]

    stop_markers = [
        "Disclaimer:",
        "Justia Legal Resources",
        "Free Daily Summaries",
        "Ask a Lawyer",
        "Find a Lawyer",
        "Previous",
        "Next",
    ]
    for marker in stop_markers:
        idx = body.find(marker)
        if idx > 0:
            body = body[:idx]

    body = normalize_text(body)

    title = ""
    h1 = soup.find(["h1", "h2"])
    if h1:
        title = normalize_text(h1.get_text(" ", strip=True))

    return title, body

def accept_section_text(section_number: str, text: str) -> tuple[bool, str]:
    starts_ok = text.startswith(f"{section_number}.")
    len_ok = len(text) >= 80
    reject_front = any(
        bad.lower() in text[:250].lower()
        for bad in [
            "quick search",
            "bill information",
            "my favorites",
            "skip to content",
            "select code",
        ]
    )
    accepted = starts_ok and len_ok and (not reject_front)
    return accepted, f"starts_ok={starts_ok}; len_ok={len_ok}; reject_front={reject_front}; len={len(text)}"

def build_record(section_number: str, title: str, text: str, html: str, url: str, run_id: str) -> dict:
    return {
        "authority_id": "CA_EVIDENCE_CODE",
        "section_id": f"EVID_{section_number}",
        "section_number": section_number,
        "citation": f"Evid. Code § {section_number}",
        "title": title,
        "text": text,
        "source_url": url,
        "source_label": "California Evidence Code (Justia bridge)",
        "captured_at": now_iso(),
        "html_sha256": sha256_text(html),
        "text_sha256": sha256_text(text) if text else "",
        "run_id": run_id,
        "raw_html_path": str((SECTIONS_DIR / f"EVID_{section_number}.html").resolve())
    }

def write_failure(section_number: str, url: str, html: str, reason: str, run_id: str) -> None:
    payload = {
        "authority_id": "CA_EVIDENCE_CODE",
        "section_id": f"EVID_{section_number}" if section_number else "",
        "section_number": section_number,
        "run_id": run_id,
        "reason": reason,
        "captured_at": now_iso(),
        "source_url": url,
        "html_sha256": sha256_text(html),
    }
    name = f"EVID_{section_number}_failure.json" if section_number else f"unknown_{sha256_text(url)[:12]}_failure.json"
    (FAILURES_DIR / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    index_html = get_html(INDEX_URL)
    candidate_links = collect_candidate_links(index_html)

    section_links = [u for u in candidate_links if looks_like_section_url(u)]
    if not section_links:
        # crawl one level deeper
        second_level = []
        seen = set(candidate_links)
        for url in candidate_links:
            try:
                html = get_html(url)
                for sub in collect_candidate_links(html):
                    if sub not in seen:
                        seen.add(sub)
                        second_level.append(sub)
                time.sleep(0.1)
            except Exception:
                pass
        section_links = [u for u in second_level if looks_like_section_url(u)]

    section_links = sorted(set(section_links), key=lambda u: int(extract_section_number_from_url(u) or "999999"))

    section_files = []
    failures = []

    for url in section_links:
        section_number = extract_section_number_from_url(url)
        try:
            html = get_html(url)
            title, text = extract_section_text(html, section_number)
            accepted, diagnostic = accept_section_text(section_number, text)

            if accepted:
                html_path = SECTIONS_DIR / f"EVID_{section_number}.html"
                json_path = SECTIONS_DIR / f"EVID_{section_number}.json"

                html_path.write_text(html, encoding="utf-8")
                record = build_record(section_number, title, text, html, url, run_id)
                json_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

                section_files.append(str(json_path.relative_to(REPO_ROOT)))
                print(f"[OK] EVID_{section_number} :: {diagnostic}")
            else:
                write_failure(section_number, url, html, diagnostic, run_id)
                failures.append({"section_number": section_number, "reason": diagnostic})
                print(f"[FAIL] EVID_{section_number} :: {diagnostic}")

            time.sleep(0.1)

        except Exception as exc:
            failures.append({"section_number": section_number, "reason": f"exception: {exc}"})
            print(f"[EXCEPTION] EVID_{section_number} :: {exc}")

    manifest = {
        "authority_id": "CA_EVIDENCE_CODE",
        "run_id": run_id,
        "captured_at": now_iso(),
        "source_label": "Justia bridge",
        "source_scope": "bridge",
        "index_url": INDEX_URL,
        "section_link_count": len(section_links),
        "section_count": len(section_files),
        "failure_count": len(failures),
        "section_files": section_files[:2000],
        "failures_sample": failures[:100]
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[CA_EVIDENCE_CODE_JUSTIA_BRIDGE] sections={len(section_files)} failures={len(failures)} manifest={MANIFEST_PATH}")

if __name__ == "__main__":
    main()

