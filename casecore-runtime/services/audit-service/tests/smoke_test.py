from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))
from service import record_audit_event

event = {
    "event_id": "AUD-001",
    "timestamp": "2026-03-20T10:00:00Z",
    "actor_id": "USR-001",
    "action": "promote_artifact",
    "target_id": "FCT-001",
    "run_id": "RUN-001"
}
assert record_audit_event(event)["recorded"] is True
print("PASS: audit-service smoke test")
