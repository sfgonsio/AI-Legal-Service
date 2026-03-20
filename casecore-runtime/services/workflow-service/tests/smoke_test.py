from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))
from service import create_run
assert create_run("MTR-001", "USR-001")["accepted"] is True
print("PASS: workflow-service smoke test")
