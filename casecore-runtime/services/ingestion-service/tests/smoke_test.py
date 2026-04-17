from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))
from service import register_document
assert register_document("MTR-001", "contract.pdf")["accepted"] is True
print("PASS: ingestion-service smoke test")
