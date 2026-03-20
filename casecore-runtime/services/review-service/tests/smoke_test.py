from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))
from service import request_promotion
assert request_promotion("FCT-001", "USR-001", "approve")["artifact_id"] == "FCT-001"
print("PASS: review-service smoke test")
