from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))
from service import get_artifact
assert get_artifact("FCT-001")["artifact_id"] == "FCT-001"
print("PASS: artifact-service smoke test")
