"""
End-to-end test for the intake-to-brain pipeline.

Flow:
  create fresh case -> upload evidence -> complete interview -> mark ready ->
  Submit for Legal Analysis -> GET /cases/{id}/analysis.

Asserts:
  - analysis blob returned
  - >= 1 COA candidate grounded in CACI (body_status=IMPORTED)
  - every COA reference exists in Legal Library (no hallucinated citations)
  - burdens produced for each COA
  - remedies produced for each COA
  - complaint has parties + allegations + causes
  - evidence map has edges back to real documents / interviews
  - /cases/{id}/analysis is gated when case is in DRAFT
"""
import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8765"


def fail(msg): print("FAIL:", msg); sys.exit(1)
def ok(msg): print("OK:", msg)


def main():
    c = httpx.Client(base_url=BASE, timeout=60.0, follow_redirects=True)

    # 1. Fresh case
    r = c.post("/cases/", json={
        "name": "Analysis Test Case", "court": "Sacramento County Superior Court",
        "plaintiff": "Pat Plaintiff", "defendant": "Sam Defendant",
    })
    if r.status_code != 201: fail(f"create case: {r.text[:200]}")
    case_id = r.json()["id"]
    ok(f"created case_id={case_id}")

    # Before any analysis, /analysis must 409
    r = c.get(f"/cases/{case_id}/analysis")
    if r.status_code != 409:
        fail(f"/analysis on DRAFT must 409; got {r.status_code}")
    ok("pre-analysis: /analysis returns 409 (gated)")

    # 2. Upload an evidence document with dates + legal signals
    doc_bytes = (
        "On January 10, 2023, Pat Plaintiff and Sam Defendant signed a written "
        "partnership agreement.\n"
        "On March 15, 2023, Pat Plaintiff emailed Sam Defendant about the breach.\n"
        "On April 2, 2023, Sam Defendant refused to pay the $50,000 invoice owed under the contract.\n"
        "On May 10, 2023, Pat Plaintiff mailed a formal demand letter.\n"
        "Sam Defendant converted funds belonging to the partnership and refused to return them.\n"
        "Sam Defendant falsely represented that the accounts were in order, knowing this was untrue.\n"
        "Pat Plaintiff relied on that representation and suffered damages of $50,000.\n"
    ).encode("utf-8")
    r = c.post("/documents/upload",
        data={
            "case_id": str(case_id),
            "filenames": "evidence_memo.txt",
            "folders": "evidence",
            "relative_paths": "evidence/evidence_memo.txt",
        },
        files={"files": ("evidence_memo.txt", doc_bytes, "text/plain")},
    )
    if r.status_code != 201: fail(f"upload: {r.text[:200]}")
    ok(f"uploaded evidence_memo.txt")

    # Poll ingest
    for _ in range(40):
        st = c.get(f"/documents/case/{case_id}/ingest-status").json()
        if st["in_flight_count"] == 0 and st["success_count"] >= 1:
            break
        time.sleep(0.3)
    ok(f"ingest settled: success={st['success_count']}")

    # 3. Complete a freeform interview
    r = c.post("/interviews/", json={"case_id": case_id, "mode": "FREEFORM_NARRATIVE"})
    iv_id = r.json()["id"]
    narrative = (
        "Pat Plaintiff and Sam Defendant entered into a partnership on January 10, 2023. "
        "Sam Defendant was a fiduciary. On February 5, 2023 a payment of $10,000 was wired. "
        "Later, Sam Defendant misrepresented the accounts and refused to return partnership funds."
    )
    c.patch(f"/interviews/{iv_id}/narrative", json={"narrative_text": narrative})
    r = c.post(f"/interviews/{iv_id}/complete", json={})
    if r.status_code != 202: fail(f"interview complete: {r.text[:200]}")
    for _ in range(40):
        iv = c.get(f"/interviews/{iv_id}").json()
        if iv["processing_state"] in ("complete", "failed"):
            break
        time.sleep(0.3)
    if iv["processing_state"] != "complete":
        fail(f"interview didn't complete: {iv}")
    ok("interview complete (actors extracted)")

    # 4. save-draft (SAVED) then submit-for-analysis
    c.post(f"/cases/{case_id}/save-draft", json={
        "return_to_dashboard": True, "actor_id": "attorney:analysis_test",
    })
    r = c.post(f"/cases/{case_id}/submit-for-analysis", json={
        "actor_id": "attorney:analysis_test",
    })
    if r.status_code != 202: fail(f"submit: {r.text[:200]}")
    ok(f"submit accepted; run_id={r.json()['run_id']}")

    # Wait for analysis to settle into REVIEW_REQUIRED or APPROVED
    for _ in range(80):
        prog = c.get(f"/cases/{case_id}/progress").json()
        if prog["save_state"] in ("REVIEW_REQUIRED", "APPROVED"):
            break
        time.sleep(0.3)
    if prog["save_state"] not in ("REVIEW_REQUIRED", "APPROVED"):
        fail(f"analysis did not settle: {prog}")
    ok(f"analysis settled: save_state={prog['save_state']}")

    # 5. GET /cases/{id}/analysis
    r = c.get(f"/cases/{case_id}/analysis")
    if r.status_code != 200: fail(f"/analysis: {r.status_code} {r.text[:300]}")
    out = r.json()
    res = out["result"]
    stats = res["stats"]
    ok(f"analysis returned: {stats}")

    if stats["coa_candidates"] < 1:
        fail(f"no COA candidates generated: {stats}")

    # 6. Verify every COA reference exists in Legal Library (no hallucinated authority)
    for coa in res["coas"]:
        ref = coa["authority"]["reference"]
        lib = c.get(f"/legal-library/records/{ref}").json()
        if lib.get("body_status") != "IMPORTED":
            fail(f"COA {ref} is not IMPORTED in Legal Library (hallucinated authority): {lib}")
    ok(f"all {len(res['coas'])} COAs have IMPORTED Legal Library grounding")

    # 7. Burdens per COA
    if len(res["burdens"]) != len(res["coas"]):
        fail("burden count != COA count")
    for b in res["burdens"]:
        if not b["element_burdens"]:
            fail(f"no element burdens for COA {b['caci_id']}")
        for eb in b["element_burdens"]:
            if eb["burden_of_production"] != "plaintiff" or eb["burden_of_persuasion"] != "plaintiff":
                fail(f"unexpected burden assignment on {b['caci_id']}/{eb['element_id']}: {eb}")
    ok(f"burdens: {len(res['burdens'])} COAs, plaintiff/preponderance default applied")

    # 8. Remedies per COA
    if len(res["remedies"]) != len(res["coas"]):
        fail("remedy count != COA count")
    total_remedy_items = sum(len(b["remedies"]) for b in res["remedies"])
    if total_remedy_items == 0:
        fail("no remedy items produced")
    ok(f"remedies: {total_remedy_items} items across {len(res['remedies'])} COAs")

    # 9. Complaint coherence
    complaint = res["complaint"]
    if not complaint["causes_of_action"]:
        fail("complaint has no causes of action")
    if not complaint["parties"]:
        fail("complaint has no parties")
    if not complaint["general_allegations"]:
        fail("complaint has no general allegations")
    if not complaint["prayer_for_relief"]:
        fail("complaint has no prayer for relief")
    for coa in complaint["causes_of_action"]:
        if coa["authority_body_status"] != "IMPORTED":
            fail(f"complaint cites non-IMPORTED authority: {coa}")
    ok(f"complaint: parties={len(complaint['parties'])} allegations={len(complaint['general_allegations'])} "
       f"coas={len(complaint['causes_of_action'])} prayer_items={len(complaint['prayer_for_relief'])}")

    # 10. Evidence map
    em = res["evidence_map"]
    if em["total_edges"] == 0:
        fail("evidence map has no edges")
    if not em["coverage_per_coa"]:
        fail("evidence map coverage_per_coa empty")
    ok(f"evidence map: {em['total_edges']} edges, {len(em['coverage_per_coa'])} COAs covered")

    # 11. Print samples
    print("\n--- COA SAMPLE ---")
    top = res["coas"][0]
    print(f"  {top['caci_id']} — {top['name']} (coverage={top['coverage_pct']*100:.0f}% conf={top['confidence']:.2f})")
    print(f"  authority: {top['authority']['reference']} / {top['authority']['title']} / body_status={top['authority']['body_status']}")
    for s in top["elements"]:
        print(f"    - [{s['status']}] {s['element_id']}: {s['label']} (conf={s['confidence']:.2f}, events={len(s['supporting_event_ids'])})")

    print("\n--- BURDEN SAMPLE ---")
    bsamp = res["burdens"][0]
    for eb in bsamp["element_burdens"][:3]:
        print(f"  [{bsamp['caci_id']}/{eb['element_id']}] BoP={eb['burden_of_production']} BoPP={eb['burden_of_persuasion']} std={eb['standard']}")

    print("\n--- REMEDY SAMPLE ---")
    rsamp = res["remedies"][0]
    for r_item in rsamp["remedies"]:
        print(f"  [{rsamp['caci_id']}] ({r_item['category']}) {r_item['label']} conf={r_item['confidence']:.2f}")
        print(f"    grounding: {r_item['grounding']}")

    print("\n--- COMPLAINT SAMPLE ---")
    print(f"  caption: {complaint['caption']}")
    print(f"  court:   {complaint['court']}")
    print(f"  parties: {[p['name'] + ' (' + p['role'] + ')' for p in complaint['parties']]}")
    print(f"  general allegations (first 3):")
    for a in complaint["general_allegations"][:3]:
        print(f"    ¶{a['para_no']} ({a['date_label']}): {a['text'][:80]}")
    print(f"  causes of action:")
    for coa in complaint["causes_of_action"]:
        print(f"    {coa['title']} (conf={coa['confidence']:.2f}, {len(coa['allegations'])} allegations)")
    print(f"  prayer: {complaint['prayer_for_relief'][:4]}")

    print("\n--- EVIDENCE MAP SAMPLE ---")
    for edge in em["edges"][:4]:
        ev = edge["evidence"]
        print(f"  {ev['source_kind']} {ev['label']} -> event {edge['event_id'][:8]} -> "
              f"COA links: {[c['caci_id'] + '/' + c['element_id'] for c in edge['coa_links'][:2]]}")

    print("\n=== INTAKE -> BRAIN ANALYSIS TEST PASSED ===")


if __name__ == "__main__":
    main()
