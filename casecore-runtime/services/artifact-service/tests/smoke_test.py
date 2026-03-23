from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from service import store_artifact, get_artifact

inserted = store_artifact(
    artifact_type="FACT",
    status="proposed",
    payload={"statement": "Payment was due on February 1 and remains unpaid."},
    created_by="system-smoke-test",
    source_reference="DOC-001:chunk-001",
    hash_value="smoke-hash-001",
)

fetched = get_artifact(inserted["id"])

assert inserted["artifact_type"] == "FACT"
assert fetched is not None
assert fetched["id"] == inserted["id"]
assert fetched["status"] == "proposed"

print("PASS: artifact-service real DB smoke test")
print({"artifact_id": inserted["id"], "artifact_type": fetched["artifact_type"]})
