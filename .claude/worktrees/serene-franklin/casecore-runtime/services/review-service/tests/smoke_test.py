from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from service import request_promotion

result = request_promotion(
    artifact_id="11111111-1111-1111-1111-111111111111",
    actor_id="USR-001",
    reason="Attorney requested promotion review",
)

assert result["accepted"] is True
assert result["review_request"]["artifact_type"] == "REVIEW_REQUEST"
assert result["review_request"]["status"] == "pending"
assert result["audit_event"]["event_type"] == "promotion_requested"

print("PASS: review-service real DB + audit smoke test")
print({
    "review_request_id": result["review_request"]["id"],
    "audit_event_id": result["audit_event"]["id"],
    "status": result["status"],
})
