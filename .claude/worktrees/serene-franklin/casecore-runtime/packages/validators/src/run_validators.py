from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from validator_paths import SCHEMA_EXAMPLE_VALIDATOR, PIPELINE_VALIDATOR, RUNTIME_VALIDATOR

def run_ps1(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing validator script: {path}")
    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(path)],
        capture_output=True,
        text=True,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Validator failed: {path.name}")

def run_all() -> None:
    run_ps1(SCHEMA_EXAMPLE_VALIDATOR)
    run_ps1(PIPELINE_VALIDATOR)
    run_ps1(RUNTIME_VALIDATOR)
    print("PASS: Runtime validators package executed all validator layers")

if __name__ == "__main__":
    run_all()
