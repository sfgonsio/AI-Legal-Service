"""
End-to-end upload + ingest test.

  - uploads 3 files (two loose, one inside a zip)
  - verifies ingest phases advance to ingest_complete
  - verifies Actors were extracted (seed + document-surfaced)
  - verifies no authority resolution occurred (save_state remains pre-analysis)
"""
import io
import sys
import time
import zipfile

import httpx

BASE = "http://127.0.0.1:8765"


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)


def ok(msg):
    print("OK:", msg)


def main():
    client = httpx.Client(base_url=BASE, timeout=15.0, follow_redirects=True)

    # 0. Case 1 is seeded (DRAFT)
    prog = client.get("/cases/1/progress").json()
    ok(f"initial save_state={prog['save_state']} (pre-analysis, ingest path applies)")

    # 1. Upload two loose files with folder structure
    file_a = (
        "Memo from Jeremy Mills to the Board of ACME Corp. dated March 15, 2023.\n"
        "Dr. Alice Chen attended. The Wilson Partnership has an interest in this matter.\n"
        "See also attached spreadsheet from David Polley, LLC."
    ).encode("utf-8")
    file_b = (
        "Subject: Contract acknowledgment\n"
        "From: David Polley <dpolley@example.com>\n"
        "To: Jeremy Mills <jmills@example.com>\n\n"
        "I acknowledge the terms we discussed. Regards, David Polley."
    ).encode("utf-8")

    # One file per POST (matches frontend per-XHR pattern; server accepts N files
    # per request but httpx has trouble composing multi-value form fields with
    # multipart files, so we send sequentially here).
    def upload_one(filename, folder, data_bytes, content_type):
        rel = f"{folder}/{filename}" if folder else filename
        files = {"files": (filename, data_bytes, content_type)}
        form = {
            "case_id": "1",
            "filenames": filename,
            "folders": folder,
            "relative_paths": rel,
        }
        return client.post("/documents/upload", data=form, files=files)

    r = upload_one("memo.txt", "evidence/memos", file_a, "text/plain")
    if r.status_code != 201:
        fail(f"/documents/upload memo {r.status_code}: {r.text[:400]}")
    up1 = r.json()
    r = upload_one("thread.eml", "emails", file_b, "message/rfc822")
    if r.status_code != 201:
        fail(f"/documents/upload thread {r.status_code}: {r.text[:400]}")
    up2 = r.json()
    up = {
        "accepted_count": up1["accepted_count"] + up2["accepted_count"],
        "rejected_count": up1["rejected_count"] + up2["rejected_count"],
        "documents": up1["documents"] + up2["documents"],
    }
    ok(f"uploaded {up['accepted_count']} files (rejected={up['rejected_count']})")
    for d in up["documents"]:
        print(f"  - doc_id={d['document_id']} filename={d['filename']} folder={d['folder']} sha={d['sha256_hash'][:12]}...")

    # 2. Upload a zip archive with one inner file in a nested folder
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "contracts/2022/amendment.txt",
            "Amendment executed by Honorable Judge Roberts. Plaintiff Jeremy Mills acknowledges.\n"
            "Counter-party: Polley Holdings LLC. Co-signed by Ms. Rachel Adams.",
        )
        zf.writestr("__MACOSX/._ignored.txt", "should be skipped")
    buf.seek(0)
    r = client.post(
        "/documents/upload-zip",
        data={"case_id": "1"},
        files={"archive": ("bundle.zip", buf.getvalue(), "application/zip")},
    )
    if r.status_code != 201:
        fail(f"/documents/upload-zip {r.status_code}: {r.text[:400]}")
    uz = r.json()
    ok(f"zip accepted_count={uz['accepted_count']} archive_id={uz['archive_id']}")
    if uz["errors"]:
        print(f"  zip errors: {uz['errors']}")
    print(f"  zip documents: {uz['documents']}")

    # 3. Poll ingest status until the docs WE uploaded are all terminal. Seeded
    # docs from seed_data bypass the upload path and stay in 'uploaded' — not
    # a failure.
    uploaded_ids = set(d["document_id"] for d in up["documents"]) | set(
        d["document_id"] for d in uz["documents"]
    )
    settled = False
    for i in range(30):
        status = client.get("/documents/case/1/ingest-status").json()
        my_docs = [d for d in status["documents"] if d["id"] in uploaded_ids]
        if my_docs and all(
            d["ingest_phase"] in ("ingest_complete", "extract_skipped", "ingest_failed")
            for d in my_docs
        ):
            settled = True
            break
        time.sleep(0.5)
    if not settled:
        fail(f"uploaded docs not settled. my_docs={my_docs}")
    ok(f"ingest settled for {len(uploaded_ids)} uploaded docs; phase_counts (all docs): {status['phase_counts']}")

    # 4. Verify every uploaded doc reached ingest_complete
    bad = [d for d in my_docs if d["ingest_phase"] != "ingest_complete"]
    if bad:
        fail(f"uploaded docs with unexpected phase: {bad}")
    ok(f"all {len(my_docs)} uploaded docs reached ingest_complete")
    for d in my_docs:
        print(f"  - {d['folder']}/{d['filename']} phase={d['ingest_phase']} mentions={d['actor_mention_count']}")

    # 5. Actors
    actors = client.get("/actors/case/1").json()
    c = actors["counts"]
    ok(f"actors: total={c['total']} resolved={c['resolved']} candidate={c['candidate']} ambiguous={c['ambiguous']} orgs={c['organizations']}")
    seeded = [a for a in actors["resolved"] if a["role_hint"] in ("plaintiff", "defendant", "court")]
    if len(seeded) < 2:
        fail(f"expected seeded plaintiff/defendant/court as RESOLVED, got {seeded}")
    ok(f"seeded resolved actors: {[a['display_name']+'('+(a['role_hint'] or '')+')' for a in seeded]}")

    # Candidates should include some extracted names
    cand_names = [a["display_name"] for a in actors["candidate"]]
    orgs = [a["display_name"] for a in actors["organizations"]]
    ok(f"candidate sample: {cand_names[:6]}")
    ok(f"organizations: {orgs[:6]}")
    if not cand_names and not orgs:
        fail("no candidates or organizations extracted; expected at least one")

    # 6. Verify NO authority side-effects: save_state is still DRAFT (ingest doesn't transition state)
    prog2 = client.get("/cases/1/progress").json()
    if prog2["save_state"] != "DRAFT":
        fail(f"ingest should not change save_state; got {prog2['save_state']}")
    ok(f"save_state unchanged: {prog2['save_state']} (analysis NOT triggered by save — correct)")

    # 7. Verify /coas/case/1 still returns 409 (gated by save_state)
    r = client.get("/coas/case/1")
    if r.status_code != 409:
        fail(f"/coas should still 409; got {r.status_code}")
    ok("analytical surfaces remain gated (409) — ingest did not trigger analysis")

    # 8. Upload-config endpoint
    cfg = client.get("/documents/upload-config").json()
    if "max_file_bytes" not in cfg or "supported_extensions" not in cfg:
        fail(f"/documents/upload-config payload missing fields: {cfg}")
    ok(f"upload-config: max_file={cfg['max_file_bytes']} supported={len(cfg['supported_extensions'])} types")

    # 9. check-hashes: sha of memo.txt should be a duplicate; a random sha should not
    import hashlib as _hl
    sha_memo = _hl.sha256(file_a).hexdigest()
    sha_unknown = _hl.sha256(b"nope").hexdigest()
    r = client.post("/documents/case/1/check-hashes", json={"sha256_list": [sha_memo, sha_unknown]})
    if r.status_code != 200:
        fail(f"check-hashes {r.status_code}: {r.text[:200]}")
    dupes = r.json()["duplicates"]
    if not any(d["sha256_hash"] == sha_memo for d in dupes):
        fail(f"expected memo.txt to be flagged as duplicate; dupes={dupes}")
    if any(d["sha256_hash"] == sha_unknown for d in dupes):
        fail("random hash should not be a duplicate")
    ok(f"check-hashes correctly flagged 1 duplicate")

    # 10. DELETE one uploaded document and verify removal
    target_doc_id = my_docs[0]["id"]
    r = client.delete(f"/documents/{target_doc_id}")
    if r.status_code != 204:
        fail(f"DELETE /documents/{target_doc_id} {r.status_code}: {r.text[:200]}")
    r = client.get(f"/documents/{target_doc_id}")
    if r.status_code != 404:
        fail(f"deleted doc still fetchable; status={r.status_code}")
    ok(f"deleted doc {target_doc_id}; subsequent GET returns 404")

    # 11. After delete, check-hashes should no longer flag memo.txt
    r = client.post("/documents/case/1/check-hashes", json={"sha256_list": [sha_memo]})
    dupes2 = r.json()["duplicates"]
    if any(d["sha256_hash"] == sha_memo for d in dupes2):
        fail(f"after delete, memo sha still flagged as dupe: {dupes2}")
    ok("after delete, duplicate no longer flagged")

    print("\n=== UPLOAD + INGEST + UX TEST PASSED ===")


if __name__ == "__main__":
    main()
