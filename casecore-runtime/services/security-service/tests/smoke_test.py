from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))
from service import authorize
assert authorize("USR-001", "read", "FCT-001")["authorized"] is True
print("PASS: security-service smoke test")
