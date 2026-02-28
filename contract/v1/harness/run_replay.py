#!/usr/bin/env python3
"""
Stage 14 — Deterministic Replay Equivalence

Verifies that each replay vector's computed outputs match the committed canonical
expected outputs (*.expected.json). Supports --freeze to generate/refresh the
expected outputs deterministically.

Contract constraints:
- Reads only contract/v1 content
- Produces deterministic JSON output (stable ordering; no timestamps)
- Does not mutate any contract artifacts unless --freeze is explicitly used
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple


SCHEMA_VERSION = "replay_equivalence_v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json_dumps(obj: Any) -> str:
    # Deterministic JSON formatting
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(stable_json_dumps(obj))


def normalize_relpath(p: Path) -> str:
    # Always forward slashes in outputs for cross-platform stability
    return str(p).replace("\\", "/")


def default_artifact_paths(contract_root: Path) -> List[Path]:
    """
    A conservative default set. These are expected to exist in your repo based
    on earlier gates. Vectors can override via include_paths.
    """
    candidates = [
        contract_root / "contract_manifest.yaml",
        contract_root / "lanes.yaml",
        contract_root / "acceptance" / "validate_contract.ps1",
        contract_root / "acceptance" / "build_integrity_checklist",
        contract_root / "schemas" / "ddl.sql",
        contract_root / "tools" / "tool_registry.yaml",
        contract_root / "roles" / "roles.yaml",
    ]
    return candidates


def vector_artifact_paths(vector: Dict[str, Any], contract_root: Path) -> List[Path]:
    include_paths = vector.get("include_paths")
    if include_paths is None:
        return default_artifact_paths(contract_root)

    if not isinstance(include_paths, list) or not all(isinstance(x, str) for x in include_paths):
        raise ValueError("Vector include_paths must be a list of strings when provided.")

    return [contract_root / Path(p) for p in include_paths]


def compute_outputs(vector_path: Path, contract_root: Path, vector: Dict[str, Any]) -> Dict[str, Any]:
    artifacts = vector_artifact_paths(vector, contract_root)

    fingerprints: Dict[str, str] = {}
    missing: List[str] = []

    for p in artifacts:
        if not p.exists() or not p.is_file():
            missing.append(normalize_relpath(p.relative_to(contract_root)))
            continue
        rel = normalize_relpath(p.relative_to(contract_root))
        fingerprints[rel] = sha256_file(p)

    # Include the vector itself to prevent silent vector mutation.
    fingerprints[normalize_relpath(vector_path.relative_to(contract_root.parent.parent))] = sha256_file(vector_path)

    outputs: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "vector_id": vector.get("id") or vector_path.stem,
        "fingerprints": dict(sorted(fingerprints.items(), key=lambda kv: kv[0])),
        "missing_artifacts": sorted(missing),
    }
    return outputs


def diff_expected(computed: Dict[str, Any], expected: Dict[str, Any]) -> List[str]:
    """
    Returns list of human-readable differences. Empty list = match.
    We require exact match of:
      - schema_version
      - vector_id
      - fingerprints (keys + values)
      - missing_artifacts (must be empty ideally, but compared exactly)
    """
    diffs: List[str] = []

    def cmp(key: str) -> None:
        if computed.get(key) != expected.get(key):
            diffs.append(f"Mismatch at '{key}': computed != expected")

    cmp("schema_version")
    cmp("vector_id")
    cmp("missing_artifacts")
    cmp("fingerprints")

    return diffs


def discover_vectors(vectors_dir: Path) -> List[Path]:
    # Pairing rule:
    #   <name>.json            = vector input
    #   <name>.expected.json   = canonical expected outputs
    # We treat files ending in ".expected.json" as expected files, not vectors.
    vectors = []
    for p in sorted(vectors_dir.glob("*.json")):
        if p.name.endswith(".expected.json"):
            continue
        vectors.append(p)
    return vectors


def expected_path_for_vector(vector_path: Path) -> Path:
    return vector_path.with_name(vector_path.name.replace(".json", ".expected.json"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract_root", required=True, help="Path to contract/v1")
    ap.add_argument("--vectors_dir", required=True, help="Path to contract/v1/harness/replay_vectors")
    ap.add_argument("--freeze", action="store_true", help="Write/overwrite expected outputs (*.expected.json)")
    ap.add_argument("--strict_missing", action="store_true", help="Fail if any artifacts are missing")
    args = ap.parse_args()

    contract_root = Path(args.contract_root).resolve()
    vectors_dir = Path(args.vectors_dir).resolve()

    if not contract_root.exists():
        print(f"ERROR: contract_root not found: {contract_root}")
        return 2
    if not vectors_dir.exists():
        print(f"ERROR: vectors_dir not found: {vectors_dir}")
        return 2

    vectors = discover_vectors(vectors_dir)
    if not vectors:
        print(f"ERROR: No replay vectors found in {vectors_dir}")
        return 3

    failures: List[Tuple[str, List[str]]] = []

    for vpath in vectors:
        vector = load_json(vpath)

        computed = compute_outputs(vpath, contract_root, vector)

        if args.strict_missing and computed.get("missing_artifacts"):
            failures.append((vpath.name, [f"Missing artifacts: {computed['missing_artifacts']}"]))
            continue

        exp_path = expected_path_for_vector(vpath)

        if args.freeze:
            write_json(exp_path, computed)
            print(f"FREEZE OK: wrote {exp_path.name} for {vpath.name}")
            continue

        if not exp_path.exists():
            failures.append((vpath.name, [f"Expected file missing: {exp_path.name}"]))
            continue

        expected = load_json(exp_path)
        diffs = diff_expected(computed, expected)
        if diffs:
            failures.append((vpath.name, diffs))
        else:
            print(f"OK: {vpath.name} matches {exp_path.name}")

    if failures:
        print("\nREPLAY EQUIVALENCE FAILED:")
        for name, diffs in failures:
            print(f"- Vector: {name}")
            for d in diffs:
                print(f"  - {d}")
        return 10

    if not args.freeze:
        print("\nREPLAY EQUIVALENCE PASSED ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())