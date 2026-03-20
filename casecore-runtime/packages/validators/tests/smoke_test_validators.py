from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from run_validators import run_all

def main() -> None:
    run_all()
    print("PASS: Runtime validators smoke test")

if __name__ == "__main__":
    main()
