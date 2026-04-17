from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from app import app  # type: ignore

def main():
    routes = {route.path for route in app.routes}
    required = {
        "/health",
        "/runs",
        "/runs/{run_id}",
        "/artifacts/{artifact_id}",
        "/artifacts/promote",
        "/audit/{target_id}",
    }

    missing = required - routes
    assert not missing, f"Missing routes: {missing}"
    print("PASS: Runtime API routes scaffolded")

if __name__ == "__main__":
    main()
