from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))
from service import connect
assert connect()["connected"] is True
print("PASS: persistence-service smoke test")
