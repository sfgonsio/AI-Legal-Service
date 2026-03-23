from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from service import create_run, get_run

created = create_run(
    run_type="fact_normalization",
    status="created",
    input_reference="DOC-001:chunk-001",
    output_reference=None,
)

fetched = get_run(created["id"])

assert created["run_type"] == "fact_normalization"
assert fetched is not None
assert fetched["id"] == created["id"]
assert fetched["status"] == "created"

print("PASS: workflow-service real DB smoke test")
print({"run_id": created["id"], "run_type": fetched["run_type"]})
