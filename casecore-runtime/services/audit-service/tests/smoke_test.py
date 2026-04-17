from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from service import record_audit_event, get_audit_for_target

entity_id = "11111111-1111-1111-1111-111111111111"

inserted = record_audit_event(
    event_type="smoke_test_event",
    entity_type="artifact",
    entity_id=entity_id,
    payload={"message": "audit smoke test"},
    actor="system-smoke-test",
    run_id=None,
)

assert inserted["event_type"] == "smoke_test_event"
rows = get_audit_for_target("artifact", entity_id)
assert len(rows) >= 1

print("PASS: audit-service real DB smoke test")
print({"inserted_id": inserted["id"], "matching_rows": len(rows)})
