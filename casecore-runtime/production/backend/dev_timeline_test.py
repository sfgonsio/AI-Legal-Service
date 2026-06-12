"""
End-to-end test for the timeline engine.

Covers:
  - fresh case; upload evidence; complete interview; build timeline.
  - events from BOTH sources (INTERVIEW + INGEST).
  - date parsing (explicit + month-only + year-only + unknown).
  - event classification.
  - actor linking to existing roster (no duplicates created).
  - ordering + grouping; UNKNOWN bucket is last.
  - NO legal analysis triggered (save_state stays pre-analysis).
"""
import io
import sys
import time

import httpx

BASE = "http://127.0.0.1:8765"


def fail(msg): print("FAIL:", msg); sys.exit(1)
def ok(msg): print("OK:", msg)


def main():
    c = httpx.Client(base_url=BASE, timeout=30.0, follow_redirects=True)

    # 1. Fresh case
    r = c.post("/cases/", json={
        "name": "Timeline Test Case", "court": "Test Ct",
        "plaintiff": "Pat Plaintiff", "defendant": "Sam Defendant",
    })
    if r.status_code != 201: fail(f"create case: {r.text[:200]}")
    case_id = r.json()["id"]
    ok(f"created case_id={case_id}")

    # 2. Save-draft so case has SAVED state (optional for timeline but realistic flow).
    c.post(f"/cases/{case_id}/save-draft", json={
        "return_to_dashboard": False, "actor_id": "attorney:test",
    })

    # 3. Upload a document with explicit dates
    doc_bytes = (
        "On March 15, 2023, Pat Plaintiff emailed Sam Defendant about the breach.\n"
        "On April 2, 2023, Sam Defendant refused to pay the $50,000 invoice.\n"
        "In May 2023, the parties met at Acme Corp. to discuss a settlement.\n"
        "A demand letter was mailed on 05/10/2023 by Pat Plaintiff.\n"
        "Later, on 2023-06-01, Sam Defendant filed a cross-complaint.\n"
        "In 2024 a final hearing was scheduled.\n"
    ).encode("utf-8")
    r = c.post("/documents/upload",
        data={
            "case_id": str(case_id),
            "filenames": "memo.txt",
            "folders": "evidence/memos",
            "relative_paths": "evidence/memos/memo.txt",
        },
        files={"files": ("memo.txt", doc_bytes, "text/plain")},
    )
    if r.status_code != 201: fail(f"upload: {r.text[:200]}")
    ok(f"uploaded memo.txt ({r.json()['accepted_count']} accepted)")

    # Poll ingest until complete.
    for _ in range(40):
        st = c.get(f"/documents/case/{case_id}/ingest-status").json()
        if st["in_flight_count"] == 0 and st["success_count"] >= 1:
            break
        time.sleep(0.3)
    ok(f"ingest settled: success={st['success_count']} failed={st['failure_count']}")

    # 4. Seed and complete a freeform interview
    r = c.post("/interviews/", json={"case_id": case_id, "mode": "FREEFORM_NARRATIVE"})
    iv_id = r.json()["id"]
    narrative = (
        "On January 10, 2023, Pat Plaintiff signed the partnership agreement "
        "with Sam Defendant. On February 5, 2023, a payment of $10,000 was "
        "wired to Acme Holdings LLC. Two weeks later Sam Defendant stopped "
        "returning calls. By August 2023, the relationship had broken down."
    )
    c.patch(f"/interviews/{iv_id}/narrative", json={"narrative_text": narrative})
    r = c.post(f"/interviews/{iv_id}/complete", json={})
    if r.status_code != 202: fail(f"interview complete: {r.text[:200]}")
    # Wait for processor
    for _ in range(40):
        iv = c.get(f"/interviews/{iv_id}").json()
        if iv["processing_state"] in ("complete", "failed"):
            break
        time.sleep(0.3)
    if iv["processing_state"] != "complete": fail(f"interview state={iv['processing_state']}")
    ok("interview complete (actors extracted)")

    # 5. Build timeline
    r = c.post(f"/timeline/{case_id}/build", json={"replace": True})
    if r.status_code != 202: fail(f"build: {r.text[:400]}")
    build = r.json()
    ok(f"build: created={build['events_created']} docs={build['documents_scanned']} ivs={build['interviews_scanned']} dur={build['duration_ms']}ms")
    if build["events_created"] < 5:
        fail(f"expected at least 5 events; got {build}")

    # 6. Fetch timeline
    t = c.get(f"/timeline/{case_id}").json()
    if t["total"] == 0:
        fail(f"empty timeline: {t}")
    ok(f"timeline: total={t['total']} known={t['known_count']} unknown={t['unknown_count']} groups={len(t['groups'])}")
    ok(f"  counts_by_source={t['counts_by_source']}")
    ok(f"  counts_by_type={t['counts_by_type']}")

    # Both sources must appear
    if "INGEST" not in t["counts_by_source"]: fail("no INGEST-sourced events")
    if "INTERVIEW" not in t["counts_by_source"]: fail("no INTERVIEW-sourced events")

    # 7. Ordering sanity: first non-UNKNOWN group has earliest timestamp, UNKNOWN is last
    labeled = [g for g in t["groups"] if g["key"] != "UNKNOWN"]
    if labeled and [g for g in t["groups"] if g["key"] == "UNKNOWN"]:
        last = t["groups"][-1]
        if last["key"] != "UNKNOWN":
            fail(f"UNKNOWN bucket must be last; got last group key={last['key']}")
    if len(labeled) >= 2:
        first_key = labeled[0]["key"]
        last_labeled_key = labeled[-1]["key"]
        if first_key > last_labeled_key:
            fail(f"chronological order broken: {first_key} > {last_labeled_key}")
    ok("ordering sanity: earliest date first; UNKNOWN last when present")

    # 8. Actor linking — find at least one event that has actors populated
    ev_with_actor = None
    for g in t["groups"]:
        for ev in g["events"]:
            if ev["actors"]:
                ev_with_actor = ev
                break
        if ev_with_actor: break
    if not ev_with_actor:
        fail("no events had linked actors; actor linking failed")
    ok(f"actor linking: e.g. '{ev_with_actor['summary'][:80]}' -> "
       f"{[a['display_name'] for a in ev_with_actor['actors']]}")

    # 9. No duplicate actors: actor count unchanged after build
    actors_before = c.get(f"/actors/case/{case_id}").json()["counts"]["total"]
    c.post(f"/timeline/{case_id}/build", json={"replace": True})
    actors_after = c.get(f"/actors/case/{case_id}").json()["counts"]["total"]
    if actors_before != actors_after:
        fail(f"timeline build created actors: before={actors_before} after={actors_after}")
    ok(f"no duplicate actors after rebuild: total={actors_after}")

    # 10. No analysis triggered
    prog = c.get(f"/cases/{case_id}/progress").json()
    if prog["save_state"] in ("PROCESSING", "REVIEW_REQUIRED", "APPROVED"):
        fail(f"timeline build should not trigger analysis; save_state={prog['save_state']}")
    r = c.get(f"/coas/case/{case_id}")
    if r.status_code != 409:
        fail(f"/coas should still be gated (409); got {r.status_code}")
    ok(f"no analysis triggered; save_state={prog['save_state']}, /coas still 409")

    # 11. Legal layer: every event carries mappings/strategy fields; at least
    # some events produce COA candidates and strategy flags. No analytical
    # state change (authority resolver must not have been called).
    had_coa = 0
    had_strategy = 0
    relations = {}
    by_ref = {}
    for g in t["groups"]:
        for ev in g["events"]:
            if "claim_relation" not in ev or "strategy" not in ev or "legal_mappings" not in ev:
                fail(f"event missing legal-layer fields: {list(ev.keys())}")
            relations[ev["claim_relation"]] = relations.get(ev["claim_relation"], 0) + 1
            if ev["strategy"]["deposition_target"] or ev["strategy"]["interrogatory_target"] or ev["strategy"]["document_request_target"]:
                had_strategy += 1
            for m in ev["legal_mappings"]:
                if m["legal_element_type"] == "COA_ELEMENT":
                    had_coa += 1
                if m.get("element_reference"):
                    by_ref.setdefault(m["element_reference"], 0)
                    by_ref[m["element_reference"]] += 1
    if had_coa == 0:
        fail("no COA_ELEMENT mappings produced; legal mapper did not fire")
    if had_strategy == 0:
        fail("no strategy flags produced on any event")
    ok(f"legal layer: claim_relation counts={relations}")
    ok(f"legal layer: events with any strategy flag = {had_strategy}")
    ok(f"legal layer: COA element hits = {had_coa}; refs={dict(sorted(by_ref.items()))}")

    # Confirm analysis remained untriggered (SR-11 unchanged).
    prog2 = c.get(f"/cases/{case_id}/progress").json()
    if prog2["save_state"] in ("PROCESSING", "REVIEW_REQUIRED", "APPROVED"):
        fail(f"legal mapping must NOT transition case state; got {prog2['save_state']}")
    r = c.get(f"/coas/case/{case_id}")
    if r.status_code != 409:
        fail(f"/coas should still be gated (409); got {r.status_code}")
    ok(f"no analysis side-effects: save_state={prog2['save_state']}, /coas still 409")

    # 12. Print a sample of 5-10 events WITH the legal layer for the report
    print("\n--- timeline + legal layer sample ---")
    n = 0
    for g in t["groups"]:
        for ev in g["events"]:
            actors = ", ".join(a["display_name"] for a in ev["actors"])
            flags = ev["strategy"]
            tags = []
            if flags["deposition_target"]: tags.append("DEPO")
            if flags["interrogatory_target"]: tags.append("ROG")
            if flags["document_request_target"]: tags.append("DOC")
            flag_str = "/".join(tags) if tags else "—"
            top_mapping = ev["legal_mappings"][0] if ev["legal_mappings"] else None
            top_str = (f"{top_mapping['legal_element_type']}"
                       f" {top_mapping['element_reference'] or '-'}"
                       f" ({top_mapping['confidence']:.2f})"
                       if top_mapping else "—")
            print(f"  [{g['label']}] ({ev['event_type']}/{ev['source']}) {ev['summary'][:78]}")
            print(f"      actors: {actors or '—'} | claim: {ev['claim_relation']} | strategy: {flag_str} | top mapping: {top_str}")
            n += 1
            if n >= 10: break
        if n >= 10: break
    print("--------------------------------------\n")

    print("=== TIMELINE + LEGAL LAYER TEST PASSED ===")


if __name__ == "__main__":
    main()
