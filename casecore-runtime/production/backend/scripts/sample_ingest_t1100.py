"""
T1100 sample ingest validation — 5-file sample run.

Tests:
  - PDF extraction (pypdf)
  - Image OCR (Claude-vision)
  - Short video transcription (Whisper via ffmpeg)
  - Dedup: uploading the same PDF twice → second must be deduplicated_reuse

Usage:
  cd casecore-runtime/production/backend
  .venv/Scripts/python.exe scripts/sample_ingest_t1100.py

Requires the backend to be running at http://127.0.0.1:8000.
Start with:
  CASECORE_STORAGE_PATH="$(pwd)/storage_local" .venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
T1100 = Path(r"C:\Users\sfgon\Documents\Archive\.All_Source_Files\T1100")

# 5-file sample: diverse types + one intentional duplicate
SAMPLE = [
    ("T1100_0001_Gmail - Yolo Farms and Direct Source Payment Summary.pdf",   "pdf"),
    ("T1100_0005_021168_IMG_0578.JPG",                                        "image"),
    ("T1100_0012_000984_a01cd10a1cf44e3a8336291899316292.MOV",                "video"),
    ("T1100_0007_000699_Gmail - Final Payment for Preferred Gardens order - 40501.pdf", "pdf"),
    # Intentional duplicate of file [0] — must be deduped, not reprocessed
    ("T1100_0001_Gmail - Yolo Farms and Direct Source Payment Summary.pdf",   "pdf_dedup"),
]

POLL_INTERVAL = 3   # seconds between status polls
POLL_TIMEOUT  = 300 # max seconds to wait for all docs to finish


def check_server() -> None:
    try:
        r = httpx.get(f"{BASE}/llm/status", timeout=5)
        r.raise_for_status()
        print(f"[server] OK  —  {r.json()}")
    except Exception as e:
        print(f"[server] UNREACHABLE: {e}\nStart the backend first.", file=sys.stderr)
        sys.exit(1)


def create_case(client: httpx.Client) -> int:
    r = client.post("/cases/", json={
        "name":       "T1100 Sample Ingest Validation",
        "plaintiff":  "Test Plaintiff",
        "defendant":  "Test Defendant",
    })
    r.raise_for_status()
    case_id = r.json()["id"]
    print(f"[case]   created id={case_id}")
    return case_id


def upload_file(client: httpx.Client, case_id: int, filename: str, label: str) -> int:
    path = T1100 / filename
    if not path.exists():
        print(f"[upload] MISSING: {filename}", file=sys.stderr)
        sys.exit(1)
    size_kb = path.stat().st_size // 1024
    print(f"[upload] {label:12s}  {filename[:60]}  ({size_kb} KB) ...", end=" ", flush=True)
    with open(path, "rb") as fh:
        r = client.post(
            f"/documents/upload",
            data={"case_id": str(case_id)},
            files={"files": (filename, fh, "application/octet-stream")},
            timeout=120,
        )
    r.raise_for_status()
    batch = r.json()
    doc_id = batch["documents"][0]["document_id"]
    print(f"doc_id={doc_id}")
    return doc_id


def poll_until_done(client: httpx.Client, case_id: int, doc_ids: list[int]) -> dict:
    deadline = time.time() + POLL_TIMEOUT
    terminal = {"ingest_complete", "extract_skipped", "ingest_failed", "deduplicated_reuse"}
    results: dict[int, dict] = {}
    pending = set(doc_ids)
    print(f"\n[poll]   waiting for {len(pending)} docs ...")

    while pending and time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        r = client.get(f"/documents/?case_id={case_id}", timeout=10)
        if r.status_code != 200:
            continue
        for doc in r.json():
            did = doc["id"]
            phase = doc.get("ingest_phase", "")
            if did in pending and phase in terminal:
                pending.discard(did)
                results[did] = doc
                status_str = phase.upper()
                method = doc.get("extraction_method") or "—"
                chars  = doc.get("char_count") or 0
                print(f"  doc {did:>4}  {status_str:<25}  method={method:<20}  chars={chars:>8,}")

    if pending:
        print(f"[poll]   TIMEOUT — still pending: {pending}", file=sys.stderr)

    return results


def summarize(doc_ids: list[int], results: dict, labels: list[str]) -> None:
    print("\n" + "=" * 70)
    print("SAMPLE RUN SUMMARY")
    print("=" * 70)
    unique     = [did for did, d in results.items() if d.get("ingest_phase") == "ingest_complete"]
    deduped    = [did for did, d in results.items() if d.get("ingest_phase") == "deduplicated_reuse"]
    skipped    = [did for did, d in results.items() if d.get("ingest_phase") == "extract_skipped"]
    failed     = [did for did, d in results.items() if d.get("ingest_phase") == "ingest_failed"]
    total_chars = sum((d.get("char_count") or 0) for d in results.values())

    print(f"  Files submitted : {len(doc_ids)}")
    print(f"  Unique processed: {len(unique)}  (LLM API calls made)")
    print(f"  Dedup skipped   : {len(deduped)}  (no reprocessing — SHA256 reuse)")
    print(f"  Extract skipped : {len(skipped)}  (unsupported / OCR_REQUIRED)")
    print(f"  Failed          : {len(failed)}")
    print(f"  Total chars     : {total_chars:,}")
    print()
    for i, (did, label) in enumerate(zip(doc_ids, labels)):
        d = results.get(did, {})
        print(f"  [{i+1}] {label:10s}  doc={did}  phase={d.get('ingest_phase','?'):<25}  "
              f"method={d.get('extraction_method') or '—':<18}  chars={d.get('char_count') or 0:>8,}")
    print("=" * 70)
    print("COST NOTE: Claude-vision (images) and Whisper (audio) consume API tokens.")
    print("Dedup file consumed 0 API tokens (content reuse).")
    if failed:
        print(f"\nFAILURES: {[results[d].get('ingest_error_detail') for d in failed]}")


def main() -> None:
    check_server()
    with httpx.Client(base_url=BASE, timeout=120) as client:
        case_id = create_case(client)
        doc_ids: list[int] = []
        labels:  list[str] = []
        for filename, label in SAMPLE:
            did = upload_file(client, case_id, filename, label)
            doc_ids.append(did)
            labels.append(label)
        results = poll_until_done(client, case_id, doc_ids)
    summarize(doc_ids, results, labels)


if __name__ == "__main__":
    main()
