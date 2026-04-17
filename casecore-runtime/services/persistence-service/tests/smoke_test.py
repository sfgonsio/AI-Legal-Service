from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from service import connect

result = connect()
assert result["connected"] is True
assert result["database"]
assert result["user"]

print("PASS: persistence-service real DB connectivity smoke test")
print(result)
