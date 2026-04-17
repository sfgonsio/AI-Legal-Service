#!/usr/bin/env python3
"""
Authority sync program for California Business and Professions Code
Division 10 (Cannabis), using the official Division 10 page as the
authoritative source snapshot.

Outputs:
- authority_store/ca/bpc/division_10_cannabis/current/toc.html
- authority_store/ca/bpc/division_10_cannabis/current/toc.txt
- authority_store/ca/bpc/division_10_cannabis/current/toc.json
- authority_store/ca/bpc/division_10_cannabis/current/division_manifest.json
- authority_store/ca/bpc/division_10_cannabis/runs/<run_id>/run_manifest.json
- authority_store/ca/bpc/division_10_cannabis/state/sync_state.json
"""

import os
import re
import json
import hashlib
import argparse
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

DIVISION_TOC_URL = "https://leginfo.legislature.ca.gov/faces/codes_displayexpandedbranch.xhtml?article=&chapter=&division=10.&part=&title=&tocCode=BPC"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: str, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


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


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_plain_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def extract_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        label = " ".join(a.get_text(" ", strip=True).split())
        href = a["href"].strip()
        if label or href:
            links.append({
                "label": label,
                "href": href,
            })
    return links


def fetch_division_toc(session: requests.Session) -> str:
    r = session.get(DIVISION_TOC_URL, timeout=60)
    r.raise_for_status()
    return r.text


def build_manifest(run_id: str, toc_html_path: str, toc_text_path: str, toc_json_path: str):
    return {
        "authority_id": "CA_BPC_DIV10_CANNABIS",
        "jurisdiction": "CA",
        "code_family": "BPC",
        "division": "10",
        "title": "Cannabis",
        "scope_note": "Business and Professions Code Division 10 Cannabis; authoritative source snapshot for Spine, Brain, and Program use.",
        "run_id": run_id,
        "generated_at": now_iso(),
        "upstreams": {
            "toc_url": DIVISION_TOC_URL
        },
        "current_artifacts": {
            "toc_html": toc_html_path,
            "toc_text": toc_text_path,
            "toc_json": toc_json_path
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
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    authority_root = os.path.join(root, "authority_store", "ca", "bpc", "division_10_cannabis")
    current_dir = os.path.join(authority_root, "current")
    runs_dir = os.path.join(authority_root, "runs")
    state_dir = os.path.join(authority_root, "state")
    state_path = os.path.join(state_dir, "sync_state.json")

    for d in [authority_root, current_dir, runs_dir, state_dir]:
        ensure_dir(d)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(runs_dir, run_id)
    ensure_dir(run_dir)

    with requests.Session() as session:
        session.headers.update({
            "User-Agent": "ai-legal-service-authority-sync/1.0"
        })

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
        "html_sha256": sha256_file(toc_html_path),
        "plain_text_sha256": sha256_file(toc_text_path),
        "links": extract_links(toc_html)
    }
    save_json(toc_json_path, toc_obj)

    manifest = build_manifest(
        run_id=run_id,
        toc_html_path=toc_html_path,
        toc_text_path=toc_text_path,
        toc_json_path=toc_json_path
    )

    current_manifest_path = os.path.join(current_dir, "division_manifest.json")
    run_manifest_path = os.path.join(run_dir, "run_manifest.json")

    save_json(current_manifest_path, manifest)
    save_json(run_manifest_path, manifest)

    state = load_json(state_path, {})
    state["authority_id"] = "CA_BPC_DIV10_CANNABIS"
    state["last_run_id"] = run_id
    state["last_run_at"] = now_iso()
    state["last_success"] = {
        "toc_html": toc_html_path,
        "toc_text": toc_text_path,
        "toc_json": toc_json_path,
        "division_manifest": current_manifest_path
    }
    save_json(state_path, state)

    print("Authority sync complete.")
    print(f"Authority root: {authority_root}")
    print(f"Current manifest: {current_manifest_path}")
    print(f"Run manifest: {run_manifest_path}")


if __name__ == "__main__":
    main()
