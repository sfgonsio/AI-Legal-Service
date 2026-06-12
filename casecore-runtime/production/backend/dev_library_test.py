"""
End-to-end test for Legal Library content rendering + OCR reliability API.

Proves that CACI_1900 / CACI_2100 / EVID_1220 render full body text, and
that CCP_3294 returns an explicit NOT_IMPORTED status (never "undefined" or
silent empty).

Also verifies that Document responses include the new extraction_status /
extraction_method / extraction_confidence / is_scanned_pdf fields.
"""
import sys
import httpx

BASE = "http://127.0.0.1:8765"


def fail(msg): print("FAIL:", msg); sys.exit(1)
def ok(msg): print("OK:", msg)


def main():
    c = httpx.Client(base_url=BASE, timeout=20.0, follow_redirects=True)

    # 1. Stats
    s = c.get("/legal-library/stats").json()
    if s["total_records"] < 1000:
        fail(f"stats reports too few records: {s}")
    ok(f"library stats: total={s['total_records']} by_code={s['by_code']} supported={s['supported_codes']}")

    # 2. Proof records
    for rid in ("CACI_1900", "CACI_2100", "EVID_1220"):
        r = c.get(f"/legal-library/records/{rid}").json()
        if r.get("body_status") != "IMPORTED":
            fail(f"{rid} body_status should be IMPORTED; got {r}")
        if not r.get("body_text") or len(r["body_text"]) < 50:
            fail(f"{rid} body_text missing or too short; length={len(r.get('body_text') or '')}")
        first_300 = (r["body_text"] or "")[:300].replace("\n", " ")
        print(f"  === {rid} ===")
        print(f"     code:   {r['code']}")
        print(f"     slug:   {r['record_id']}")
        print(f"     title:  {r['title']}")
        print(f"     length: {r['body_length']}")
        print(f"     cert:   certified={r['certified']} provisional={r['provisional']}")
        print(f"     first:  {first_300}…")
        ok(f"{rid} rendered with IMPORTED body ({r['body_length']} chars)")

    # 3. CCP_3294 — honest NOT_IMPORTED with an explicit message (not undefined).
    r = c.get("/legal-library/records/CCP_3294").json()
    if r.get("body_status") != "NOT_IMPORTED":
        fail(f"CCP_3294 should be NOT_IMPORTED; got {r}")
    if not r.get("status_message"):
        fail("CCP_3294 must carry an explicit status_message")
    if r.get("body_text"):
        fail(f"CCP_3294 body_text should be None, got {r['body_text']!r}")
    ok(f"CCP_3294: body_status={r['body_status']} message={r['status_message']!r}")

    # 4. Invalid id returns an explicit shape, not a 500.
    r = c.get("/legal-library/records/garbage").json()
    if r.get("body_status") != "NOT_IMPORTED":
        fail(f"invalid id should be NOT_IMPORTED; got {r}")
    ok(f"invalid id handled gracefully: {r['status_message']}")

    # 5. List endpoint: CACI filter returns a reasonable number and each row
    # has body_status but no body_text.
    lst = c.get("/legal-library/records?code=CACI&limit=5").json()
    if lst["total"] < 500:
        fail(f"CACI list too small: total={lst['total']}")
    rows = lst["records"]
    if not rows:
        fail("no records in list")
    first = rows[0]
    if "body_status" not in first:
        fail(f"list row missing body_status: {first}")
    if first.get("body_text") not in (None, ""):
        fail(f"list rows must NOT include body_text; got {first.get('body_text')!r}")
    ok(f"list OK: total={lst['total']} first={first['record_id']} status={first['body_status']}")

    # 6. Search filter
    lst2 = c.get("/legal-library/records?code=CACI&q=misrepresentation&limit=5").json()
    ok(f"search found {lst2['total']} CACI with 'misrepresentation' in id/title")

    # 7. Document extraction reliability fields present on existing docs.
    # Mills case (id=1) has seeded docs which bypass the upload pipeline and
    # stay in 'uploaded' / 'NOT_ATTEMPTED'; that's honest.
    docs = c.get("/documents/case/1/ingest-status").json()
    sample = docs["documents"][0]
    for key in ("extraction_status", "extraction_method", "extraction_confidence", "is_scanned_pdf"):
        if key not in sample:
            fail(f"ingest-status doc missing key '{key}': {sample}")
    ok(f"ingest-status carries extraction fields; sample={sample['filename']} status={sample['extraction_status']}")

    print("\n=== LEGAL LIBRARY + OCR FIELDS TEST PASSED ===")


if __name__ == "__main__":
    main()
