from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

from bootstrap_validation import run_bootstrap_validation
from contract_loader import load_manifest, list_schema_files


def main() -> None:
    manifest = load_manifest()
    assert "contract_sets" in manifest, "Manifest missing contract_sets"
    schemas = list_schema_files()
    assert len(schemas) >= 6, "Expected at least 6 schema files"
    run_bootstrap_validation()
    print("PASS: Runtime contracts smoke test")


if __name__ == "__main__":
    main()
