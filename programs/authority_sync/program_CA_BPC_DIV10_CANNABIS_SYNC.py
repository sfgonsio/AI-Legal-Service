#!/usr/bin/env python3
"""
Authority sync program for California Business and Professions Code
Division 10 (Cannabis), intended for governed legal-authority ingestion.

Primary upstreams:
- LegInfo downloads page for bulk code archives
- Official Division 10 Cannabis TOC page for direct authoritative scope snapshot
"""

import os
import re
import json
import time
import hashlib
import argparse
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DOWNLOADS_PAGE = "https://leginfo.legislature.ca.gov/faces/downloads.xhtml"
DIVISION_TOC_URL = "https://leginfo.legislature.ca.gov/faces/codes_displayexpandedbranch.xhtml?article=&chapter=&division=10.&part=&title=&tocCode=BPC"

BPC_HINTS = [
    r"\bBusiness\s*&\s*Professions\b",
    r"\bBusiness\s+and\s+Professions\b",
    r"\bBPC\b",
    r"bus(?:iness)?prof",
    r"business_professions",
]

ZIP_HINT = r"\.zip(\?|$)"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def sha256_file(path: str, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, value) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def write_text(path: str, text: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def filename_from_url(url: str, fallback: str = "download.zip") -> str:
    path = urlparse(url).path
    name = os.path.basename(path) or fallback
    if "." not in name:
        return fallback
    return name


def fetch_downloads_page(session: requests.Session) -> str:
    r = session.get(DOWNLOADS_PAGE, timeout=60)
    r.raise_for_status()
    return r.text


def fetch_division_toc(session: requests.Session) -> str:
    r = session.get(DIVISION_TOC_URL, timeout=60)
    r.raise_for_status()
    return r.text


def extract_plain_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def find_bpc_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ", strip=True).split())
        href = a["href"].strip()
        abs_url = urljoin(DOWNLOADS_PAGE, href)

        if not abs_url.startswith("http"):
            continue

        score = 0
        hay = f"{text} {href}".lower()

        for pat in BPC_HINTS:
            if re.search(pat, hay, flags=re.IGNORECASE):
                score += 2

        if re.search(ZIP_HINT, abs_url, flags=re.IGNORECASE):
            score += 1

        if score >= 2:
            links.append((score, text, abs_url))

    links.sort(key=lambda x: (-x[0], x[2]))
    return links


def download_with_cache(session: requests.Session, url: str, out_dir: str, state: dict, force: bool = False):
    key = url
    headers = {}
    prior = state.get("remote_objects", {}).get(key, {})

    if not force:
        if "etag" in prior:
            headers["If-None-Match"] = prior["etag"]
        if "last_modified" in prior:
            headers["If-Modified-Since"] = prior["last_modified"]

    r = session.get(url, headers=headers, stream=True, allow_redirects=True, timeout=120)

    if r.status_code == 304:
        return prior.get("path"), "not_modified", prior

    r.raise_for_status()

    fname = filename_from_url(r.url, fallback="bulk_archive.zip")
    local_path = os.path.join(out_dir, fname)
    tmp_path = local_path + ".part"

    with open(tmp_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    os.replace(tmp_path, local_path)

    meta = {
        "url": url,
        "final_url": r.url,
        "downloaded_at": now_iso(),
        "path": local_path,
        "size_bytes": os.path.getsize(local_path),
        "sha256": sha256_file(local_path),
        "content_type": r.headers.get("Content-Type"),
    }

    if "ETag" in r.headers:
        meta["etag"] = r.headers.get("ETag")
    if "Last-Modified" in r.headers:
        meta["last_modified"] = r.headers.get("Last-Modified")

    state.setdefault("remote_objects", {})[key] = meta
    return local_path, "downloaded", meta


def build_manifest(run_id: str, toc_url: str, toc_html_path: str, toc_text_path: str, toc_json_path: str, bulk_meta):
    return {
        "authority_id": "CA_BPC_DIV10_CANNABIS",
        "jurisdiction": "CA",
        "code_family": "BPC",
        "division": "10",
        "title": "Cannabis",
        "scope_note": "Business and Professions Code Division 10 Cannabis; authoritative legal reference for governed reasoning and evidence evaluation.",
        "run_id": run_id,
        "generated_at": now_iso(),
        "upstreams": {
            "toc_url": toc_url,
            "bulk_archive": bulk_meta,
        },
        "current_artifacts": {
            "toc_html": toc_html_path,
            "toc_text": toc_text_path,
            "toc_json": toc_json_path,
        },
        "consumers": {
            "spine": [
                "authority constraints",
                "canonical legal source boundary",
                "validation guardrails"
            ],
            "brain": [
                "legal reasoning inputs",
                "issue framing",
                "authority-aware inference support"
            ],
            "programs": [
                "parse",
                "mapping",
                "coverage",
                "evidence evaluation",
                "case theory support"
            ]
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--force", action="store_true", help="Force redownload")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    authority_root = os.path.join(root, "authority_store", "ca", "bpc", "division_10_cannabis")
    current_dir = os.path.join(authority_root, "current")
    raw_dir = os.path.join(authority_root, "raw")
    runs_dir = os.path.join(authority_root, "runs")
    state_dir = os.path.join(authority_root, "state")
    state_path = os.path.join(state_dir, "sync_state.json")

    for d in [authority_root, current_dir, raw_dir, runs_dir, state_dir]:
        ensure_dir(d)

    state = load_json(state_path, {})
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(runs_dir, run_id)
    ensure_dir(run_dir)

    with requests.Session() as session:
        session.headers.update({
            "User-Agent": "ai-legal-service-authority-sync/1.0"
        })

        downloads_html = fetch_downloads_page(session)
        downloads_html_path = os.path.join(raw_dir, "downloads_page.html")
        write_text(downloads_html_path, downloads_html)

        candidates = find_bpc_links(downloads_html)
        bulk_meta = None

        if candidates:
            best_url = candidates[0][2]
            bulk_path, bulk_status, bulk_meta = download_with_cache(
                session=session,
                url=best_url,
                out_dir=raw_dir,
                state=state,
                force=args.force
            )

            headers_path = os.path.join(raw_dir, "bulk_archive_headers.json")
            save_json(headers_path, bulk_meta)

            if bulk_path and os.path.exists(bulk_path):
                sha_path = os.path.join(raw_dir, "bulk_archive.sha256.txt")
                write_text(sha_path, f"{bulk_meta['sha256']}  {os.path.basename(bulk_path)}\n")

                canonical_bulk = os.path.join(raw_dir, "bulk_archive.zip")
                if os.path.abspath(bulk_path) != os.path.abspath(canonical_bulk):
                    with open(bulk_path, "rb") as src, open(canonical_bulk, "wb") as dst:
                        dst.write(src.read())

        toc_html = fetch_division_toc(session)
        toc_html_path = os.path.join(current_dir, "toc.html")
        toc_text_path = os.path.join(current_dir, "toc.txt")
        toc_json_path = os.path.join(current_dir, "toc.json")

        write_text(toc_html_path, toc_html)
        write_text(toc_text_path, extract_plain_text(toc_html))

        toc_obj = {
            "authority_id": "CA_BPC_DIV10_CANNABIS",
            "url": DIVISION_TOC_URL,
            "captured_at": now_iso(),
            "plain_text_sha256": sha256_file(toc_text_path),
            "html_sha256": sha256_file(toc_html_path),
        }
        save_json(toc_json_path, toc_obj)

    manifest = build_manifest(
        run_id=run_id,
        toc_url=DIVISION_TOC_URL,
        toc_html_path=toc_html_path,
        toc_text_path=toc_text_path,
        toc_json_path=toc_json_path,
        bulk_meta=bulk_meta
    )

    current_manifest_path = os.path.join(current_dir, "division_manifest.json")
    run_manifest_path = os.path.join(run_dir, "run_manifest.json")

    save_json(current_manifest_path, manifest)
    save_json(run_manifest_path, manifest)

    state["last_run_id"] = run_id
    state["last_run_at"] = now_iso()
    state["authority_id"] = "CA_BPC_DIV10_CANNABIS"
    save_json(state_path, state)

    print("Authority sync complete.")
    print(f"Authority root: {authority_root}")
    print(f"Current manifest: {current_manifest_path}")
    print(f"Run manifest: {run_manifest_path}")


if __name__ == "__main__":
    main()
