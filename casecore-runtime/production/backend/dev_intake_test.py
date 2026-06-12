"""
End-to-end test for intake interview + actor CRUD.

Covers:
  - create interview (returns existing on re-create per case)
  - guided-mode question listing + per-question progress
  - answer question, progress updates, is_question_answered logic
  - switch to freeform, narrative update, narrative preserved
  - complete interview (explicit trigger) -> background actor extraction
  - actor roster populated from interview with source=INTERVIEW
  - full actor CRUD: create, read, update, promote, delete, merge
  - NO analysis triggered (save_state remains pre-analysis, /coas still 409)
"""
import sys
import time

import httpx

BASE = "http://127.0.0.1:8765"


def fail(msg): print("FAIL:", msg); sys.exit(1)
def ok(msg): print("OK:", msg)


def main():
    client = httpx.Client(base_url=BASE, timeout=15.0, follow_redirects=True)

    # Create a FRESH case so this test is isolated from prior state/tests.
    r = client.post("/cases/", json={
        "name": "Intake Test Case", "court": "Test Ct",
        "plaintiff": "Alex Plaintiff", "defendant": "Sam Defendant",
    })
    if r.status_code != 201:
        fail(f"create case: {r.status_code}: {r.text[:200]}")
    case_id = r.json()["id"]
    ok(f"created fresh case_id={case_id}")
    progress0 = client.get(f"/cases/{case_id}/progress").json()
    ok(f"pre-intake save_state={progress0['save_state']}")

    # 1. Create interview (returns existing if any)
    r = client.post("/interviews/", json={"case_id": case_id, "mode": "GUIDED_QUESTIONS"})
    if r.status_code not in (200, 201):
        fail(f"/interviews/ {r.status_code}: {r.text[:400]}")
    iv = r.json()
    ok(f"interview id={iv['id']} mode={iv['mode']} questions={len(iv['questions'])}")
    if len(iv["questions"]) < 10:
        fail("expected default question set to have 10+ entries")

    # 2. Initial progress
    p = client.get(f"/interviews/{iv['id']}/progress").json()
    ok(f"initial progress: {p['answered_count']}/{p['total_count']} display='{p['display']}' mode={p['mode']}")
    if p["answered_count"] != 0 or p["total_count"] == 0:
        fail(f"expected 0/N answered, got {p}")

    # 3. Answer 2 questions (one short TEXT, one LONG_TEXT >= 20 chars)
    qs = sorted(iv["questions"], key=lambda x: x["order_index"])
    short_q = next((q for q in qs if q["completion_kind"] == "TEXT"), qs[0])
    long_q = next((q for q in qs if q["completion_kind"] == "LONG_TEXT"), qs[-1])
    r = client.patch(f"/interviews/questions/{short_q['id']}", json={"answer_text": "CA Sup"})
    if r.status_code != 200: fail(f"patch short q: {r.text[:200]}")
    if not r.json()["answered"]: fail("short TEXT with 6 chars should be answered")
    r = client.patch(f"/interviews/questions/{long_q['id']}",
                     json={"answer_text": "Plaintiff Jeremy Mills alleges breach of contract by David Polley at ACME Corp."})
    if r.status_code != 200: fail(f"patch long q: {r.text[:200]}")
    if not r.json()["answered"]: fail("LONG_TEXT >= 20 chars should be answered")
    ok("answered 2 questions")

    p = client.get(f"/interviews/{iv['id']}/progress").json()
    ok(f"after answers: {p['answered_count']}/{p['total_count']} display='{p['display']}'")
    if p["answered_count"] != 2:
        fail(f"expected 2 answered, got {p}")

    # 4. Short-answer that's too short for LONG_TEXT does NOT count as answered
    r = client.patch(f"/interviews/questions/{long_q['id']}", json={"answer_text": "brief"})
    if r.json()["answered"]: fail("LONG_TEXT with 5 chars should not count as answered")
    p2 = client.get(f"/interviews/{iv['id']}/progress").json()
    if p2["answered_count"] != 1:
        fail(f"answered count should drop to 1, got {p2}")
    ok("completion logic respects completion_kind thresholds")

    # 5. Restore the long answer
    client.patch(f"/interviews/questions/{long_q['id']}",
                 json={"answer_text": "Plaintiff Jeremy Mills alleges breach of contract by David Polley at ACME Corp."})

    # 6. Switch to FREEFORM, preserves narrative_text
    r = client.patch(f"/interviews/{iv['id']}/mode", json={"mode": "FREEFORM_NARRATIVE"})
    if r.status_code != 200: fail(f"switch mode: {r.text[:200]}")
    ok(f"switched to mode={r.json()['mode']}")

    p3 = client.get(f"/interviews/{iv['id']}/progress").json()
    if p3["mode"] != "FREEFORM_NARRATIVE": fail("progress should reflect new mode")
    if "Freeform" not in p3["display"] and "Narrative" not in p3["display"]:
        fail(f"freeform display should not show N/N count; got '{p3['display']}'")
    ok(f"freeform display: '{p3['display']}'")

    # 7. Set narrative, then switch back and guided answers preserved
    client.patch(f"/interviews/{iv['id']}/narrative",
                 json={"narrative_text": "Case against David Polley involving Polley Holdings LLC and Ms. Rachel Adams."})
    r = client.patch(f"/interviews/{iv['id']}/mode", json={"mode": "GUIDED_QUESTIONS"})
    iv2 = r.json()
    if not any(q["answer_text"] for q in iv2["questions"]):
        fail("guided answers should be preserved across mode switch")
    if not iv2["narrative_text"]:
        fail("narrative should be preserved when switching back to guided")
    ok("mode switch preserves both narrative and question answers")

    # 8. Complete interview (FREEFORM mode). Switch back to freeform first.
    client.patch(f"/interviews/{iv['id']}/mode", json={"mode": "FREEFORM_NARRATIVE"})
    r = client.post(f"/interviews/{iv['id']}/complete", json={})
    if r.status_code != 202:
        fail(f"complete {r.status_code}: {r.text[:300]}")
    ok(f"interview completion accepted; state now={r.json()['processing_state']}")

    # Poll until complete or failed
    done = False
    for _ in range(40):
        iv_now = client.get(f"/interviews/{iv['id']}").json()
        if iv_now["processing_state"] in ("complete", "failed"):
            done = True
            break
        time.sleep(0.3)
    if not done:
        fail(f"interview processing did not settle; last state={iv_now}")
    if iv_now["processing_state"] != "complete":
        fail(f"expected complete, got {iv_now['processing_state']}: {iv_now.get('last_error_detail')}")
    ok(f"interview processing complete at {iv_now['processed_at']}")

    # 9. Actor roster reflects interview processing. In a fresh DB the interview
    # is the sole source and actors carry source=INTERVIEW. If upload also
    # populated actors previously, interview mentions are added to the shared
    # rows. Either way, at least one ActorMention with source_kind=INTERVIEW
    # MUST exist after processing.
    actors = client.get(f"/actors/case/{case_id}").json()
    all_actor_rows = actors["resolved"] + actors["candidate"] + actors["ambiguous"] + actors["organizations"]
    iv_mention_found = False
    iv_sourced = [a for a in all_actor_rows if a.get("source") == "INTERVIEW"]
    for a in all_actor_rows:
        mres = client.get(f"/actors/{a['id']}/mentions").json()
        if any(m.get("source_kind") == "INTERVIEW" for m in mres):
            iv_mention_found = True
            break
    if not iv_mention_found:
        fail(f"no ActorMention with source_kind=INTERVIEW; actor counts={actors['counts']}")
    ok(f"interview mentions recorded; INTERVIEW-sourced actor rows: {[a['display_name'] for a in iv_sourced] or '(existing rows were augmented)'}")

    # 10. Create actor via API (CRUD: create)
    r = client.post("/actors/", json={
        "case_id": case_id, "display_name": "Attorney Pat Williams",
        "entity_type": "PERSON", "resolution_state": "RESOLVED", "role_hint": "opposing_counsel",
    })
    if r.status_code != 201:
        fail(f"actor create {r.status_code}: {r.text[:200]}")
    manual = r.json()
    if manual["source"] != "MANUAL":
        fail(f"manual actor source should be MANUAL, got {manual['source']}")
    ok(f"manually created actor id={manual['id']} source={manual['source']}")

    # 11. Update (CRUD: update)
    r = client.patch(f"/actors/{manual['id']}", json={"notes": "Filed notice of appearance 2026-04-22"})
    if r.status_code != 200 or r.json()["notes"] is None:
        fail("actor update failed")
    ok("actor update applied")

    # 12. Promote a CANDIDATE if any, else skip
    cand_list = actors["candidate"]
    if cand_list:
        target = cand_list[0]
        r = client.patch(f"/actors/{target['id']}", json={"resolution_state": "RESOLVED"})
        if r.status_code != 200 or r.json()["resolution_state"] != "RESOLVED":
            fail("promote failed")
        ok(f"promoted candidate {target['display_name']} -> RESOLVED")

    # 13. Merge: create a duplicate then merge it into manual
    r = client.post("/actors/", json={
        "case_id": case_id, "display_name": "Pat R. Williams",
        "entity_type": "PERSON", "resolution_state": "CANDIDATE",
    })
    dup = r.json()
    r = client.post("/actors/merge", json={
        "source_actor_ids": [dup["id"]], "target_actor_id": manual["id"],
    })
    if r.status_code != 200:
        fail(f"merge {r.status_code}: {r.text[:200]}")
    mr = r.json()
    if mr["target_actor_id"] != manual["id"] or dup["id"] not in mr["merged_actor_ids"]:
        fail(f"merge response unexpected: {mr}")
    # Verify duplicate is gone
    r = client.get(f"/actors/{dup['id']}")
    if r.status_code != 404:
        fail("merged actor should be 404")
    ok(f"merge moved {mr['moved_mentions']} mention(s) to actor {mr['target_actor_id']}")

    # 14. Delete
    r = client.delete(f"/actors/{manual['id']}")
    if r.status_code != 204:
        fail(f"delete {r.status_code}: {r.text[:200]}")
    r = client.get(f"/actors/{manual['id']}")
    if r.status_code != 404:
        fail("deleted actor should be 404")
    ok("delete + post-delete 404 confirmed")

    # 15. Verify no analysis was triggered
    prog2 = client.get(f"/cases/{case_id}/progress").json()
    if prog2["save_state"] in ("PROCESSING", "REVIEW_REQUIRED", "APPROVED"):
        fail(f"interview must NOT trigger analysis; save_state={prog2['save_state']}")
    r = client.get(f"/coas/case/{case_id}")
    if r.status_code != 409:
        fail(f"/coas should still be gated (409); got {r.status_code}")
    ok(f"save_state={prog2['save_state']} (no analysis); /coas still 409 -- ingest/interview did not trigger analysis")

    # 16. Double-complete guard
    r = client.post(f"/interviews/{iv['id']}/complete", json={})
    if r.status_code not in (409,):
        fail(f"double-complete should 409, got {r.status_code}")
    ok("double-complete correctly blocked (409)")

    print("\n=== INTAKE + ACTOR CRUD TEST PASSED ===")


if __name__ == "__main__":
    main()
