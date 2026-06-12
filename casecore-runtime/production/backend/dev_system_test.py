"""
End-to-end system test for case-scoped provisional CACI decisioning.

Flow:
  1. Use the seeded case (Mills v. Polley) — no manual CACI content created here.
  2. Insert one test COA whose caci_ref matches an existing provisional record
     in authority_packs/ca_caci_provisional/ (the provisional record was
     produced in the earlier phases, not in this step).
  3. GET /coas → verify authority.effective_grounding == PROPOSED,
                case_decision.state == PENDING_REVIEW.
  4. POST /case-authority/decisions → ACCEPTED against the active pinned record.
  5. GET /coas → verify effective_grounding == GROUNDED.
  6. GET /case-authority/case/{id}/map → verify tri-signal block.
  7. Verify a RecomputeEvent row was written.

No manual CACI seeding. The provisional store is read via the implemented
Brain resolver path (routes + brain/*.py + authority_packs/ca_caci_provisional).
"""
import asyncio
import json
import os
import sqlite3
import sys
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))

PORT = int(os.getenv("DEV_PORT", "8765"))
BASE = f"http://127.0.0.1:{PORT}"

# CACI id matching an existing provisional record (produced by prior phases, not this step).
TEST_CACI_ID = "CACI_303"

DB_FILE = HERE / "casecore.db"


async def insert_test_coa(case_id: int) -> int:
    """Insert a test COA referencing the existing provisional CACI_303 record."""
    from database import AsyncSessionLocal
    from models import COA
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(COA).where(COA.case_id == case_id).where(COA.caci_ref == TEST_CACI_ID)
        )
        row = existing.scalar_one_or_none()
        if row:
            return row.id

        coa = COA(
            case_id=case_id,
            name="TEST Breach of Contract (CACI_303 provisional test)",
            caci_ref=TEST_CACI_ID,
            strength=0.0,
            evidence_count=0,
            coverage_pct=0.0,
            status="pending",
        )
        db.add(coa)
        await db.commit()
        await db.refresh(coa)
        return coa.id


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg):
    print(f"OK: {msg}")


async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=10.0, follow_redirects=True) as client:
        # --- Step 1: case ---
        r = await client.get("/cases")
        r.raise_for_status()
        cases = r.json()
        if not cases:
            fail("no cases seeded")
        case_id = cases[0]["id"]
        ok(f"using case_id={case_id} name={cases[0]['name']}")

        # --- Step 2: insert test COA ---
        coa_id = await insert_test_coa(case_id)
        ok(f"test COA inserted id={coa_id} caci_ref={TEST_CACI_ID}")

        # --- Step 3: verify initial PROPOSED / PENDING_REVIEW ---
        r = await client.get(f"/coas/case/{case_id}")
        r.raise_for_status()
        coas = r.json()
        target = next((c for c in coas if c["id"] == coa_id), None)
        if not target:
            fail("test COA not returned")
        authority = target.get("authority") or {}
        print(f"[step3] initial authority:\n{json.dumps(authority, indent=2)}")
        if authority.get("effective_grounding") != "PROPOSED":
            fail(f"expected PROPOSED, got {authority.get('effective_grounding')}")
        if authority.get("case_decision", {}).get("state") != "PENDING_REVIEW":
            fail(f"expected PENDING_REVIEW, got {authority.get('case_decision')}")
        pinned_for_accept = authority.get("pinned_record_id")
        if not pinned_for_accept:
            fail("no pinned_record_id returned for PENDING_REVIEW")
        ok(f"PROPOSED / PENDING_REVIEW confirmed; pinned_record_id={pinned_for_accept}")

        # --- Step 4: ACCEPTED decision ---
        decision_body = {
            "case_id": case_id,
            "caci_id": TEST_CACI_ID,
            "state": "ACCEPTED",
            "pinned_record_id": pinned_for_accept,
            "decided_by_actor_type": "ATTORNEY",
            "decided_by_actor_id": "attorney:system_test",
            "decided_by_role": "lead_attorney",
            "rationale": "System test acceptance against active provisional record",
            "source_event": "dev_system_test",
        }
        r = await client.post("/case-authority/decisions", json=decision_body)
        if r.status_code != 201:
            fail(f"decision POST failed: {r.status_code} {r.text}")
        decision = r.json()
        ok(f"decision written decision_id={decision['decision_id']} state={decision['state']}")

        # --- Step 5: verify GROUNDED ---
        r = await client.get(f"/coas/case/{case_id}")
        r.raise_for_status()
        coas = r.json()
        target = next((c for c in coas if c["id"] == coa_id), None)
        authority = (target or {}).get("authority") or {}
        print(f"[step5] post-decision authority:\n{json.dumps(authority, indent=2)}")
        if authority.get("effective_grounding") != "GROUNDED":
            fail(f"expected GROUNDED, got {authority.get('effective_grounding')}")
        if authority.get("case_decision", {}).get("state") != "ACCEPTED":
            fail(f"expected ACCEPTED, got {authority.get('case_decision')}")
        if authority.get("decision_id") != decision["decision_id"]:
            fail(f"decision_id mismatch")
        if authority.get("pinned_record_id") != pinned_for_accept:
            fail(f"pinned_record_id drifted")
        ok("GROUNDED with correct decision_id + pinned_record_id")

        # --- Step 6: case-to-authority map ---
        r = await client.get(f"/case-authority/case/{case_id}/map")
        r.raise_for_status()
        mp = r.json()
        row = next((x for x in mp if x["caci_id"] == TEST_CACI_ID), None)
        if not row:
            fail(f"{TEST_CACI_ID} missing from case map")
        row_auth = row["authority"]
        if row_auth["effective_grounding"] != "GROUNDED":
            fail(f"map row not GROUNDED: {row_auth}")
        ok(f"case-to-authority map shows tri-signal: certified={row_auth['certified']['present']} "
           f"prov_status={row_auth['provisional_candidate']['status']} "
           f"decision={row_auth['case_decision']['state']}")

        # --- Step 7: verify RecomputeEvent recorded ---
        conn = sqlite3.connect(DB_FILE)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, case_id, caci_id, triggered_by_decision_id, scope_json, status "
                "FROM recompute_events WHERE case_id=? AND caci_id=?",
                (case_id, TEST_CACI_ID),
            )
            rows = cur.fetchall()
            if not rows:
                fail("no RecomputeEvent row found")
            print(f"[step7] recompute events: {rows}")
            ok(f"{len(rows)} RecomputeEvent row(s) recorded")

            # Also check COA snapshot columns populated
            cur.execute(
                "SELECT authority_decision_id, authority_pinned_record_id, authority_effective_grounding, status "
                "FROM coas WHERE id=?",
                (coa_id,),
            )
            snap = cur.fetchone()
            print(f"[step7] COA snapshot: {snap}")
            if snap[0] != decision["decision_id"]:
                fail(f"COA authority_decision_id not snapshotted: {snap}")
            if snap[1] != pinned_for_accept:
                fail(f"COA authority_pinned_record_id not snapshotted: {snap}")
            if snap[2] != "GROUNDED":
                fail(f"COA authority_effective_grounding not snapshotted: {snap}")
            if snap[3] != "grounded":
                fail(f"COA status not updated: {snap}")
            ok("COA snapshot columns populated")
        finally:
            conn.close()

    print("\n=== SYSTEM TEST PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
