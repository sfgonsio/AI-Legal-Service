from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
AUTHORITATIVE_ROOT = PACKAGE_ROOT / "authoritative"
MANIFEST_PATH = AUTHORITATIVE_ROOT / "manifest" / "contract_manifest.yaml"


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_manifest() -> Dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")
    return load_yaml(MANIFEST_PATH)


def resolve_contract_path(contract_relative_path: str) -> Path:
    cleaned = contract_relative_path.replace("/casecore-spec/packages/contracts/", "")
    return AUTHORITATIVE_ROOT / cleaned


def load_schema(schema_filename: str) -> Dict[str, Any]:
    schema_path = AUTHORITATIVE_ROOT / "schemas" / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    return load_json(schema_path)


def list_schema_files() -> list[str]:
    return sorted([p.name for p in (AUTHORITATIVE_ROOT / "schemas").glob("*.json")])


def validate_manifest_paths() -> list[str]:
    manifest = load_manifest()
    missing: list[str] = []
    for _, paths in manifest.get("contract_sets", {}).items():
        for path in paths:
            resolved = resolve_contract_path(path)
            if not resolved.exists():
                missing.append(str(resolved))
    return missing
