from __future__ import annotations

from contract_loader import list_schema_files, validate_manifest_paths


def run_bootstrap_validation() -> None:
    missing = validate_manifest_paths()
    if missing:
        raise RuntimeError("Missing manifest paths: " + " | ".join(missing))

    schemas = list_schema_files()
    if not schemas:
        raise RuntimeError("No schemas found in runtime contracts package.")

    print("PASS: Contract manifest paths resolved")
    print(f"PASS: {len(schemas)} schema files available")
