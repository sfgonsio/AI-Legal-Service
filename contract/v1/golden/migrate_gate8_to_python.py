from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List, Tuple


# -----------------------------
# Helpers
# -----------------------------
def repo_root_from_this_file() -> Path:
    # contract/v1/golden/migrate_gate8_to_python.py -> up 3 => repo root
    return Path(__file__).resolve().parents[3]


def ensure_dir(path: Path, apply: bool, actions: List[str]) -> None:
    if path.exists():
        return
    actions.append(f"MKDIR  {path}")
    if apply:
        path.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str, apply: bool, actions: List[str], overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        actions.append(f"SKIP   {path} (exists)")
        return
    actions.append(f"WRITE  {path}{' (overwrite)' if path.exists() else ''}")
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def move_to_archive(src: Path, archive_root: Path, apply: bool, actions: List[str]) -> None:
    if not src.exists():
        actions.append(f"SKIP   {src} (missing)")
        return
    rel = src.relative_to(repo_root_from_this_file())
    dst = archive_root / rel
    actions.append(f"MOVE   {src} -> {dst}")
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def remove_path(path: Path, apply: bool, actions: List[str]) -> None:
    if not path.exists():
        actions.append(f"SKIP   {path} (missing)")
        return
    actions.append(f"DELETE {path}")
    if apply:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


# -----------------------------
# Canonical Python files
# -----------------------------
CANONICAL_PY = """\
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    \"""
    Canonical JSON bytes:
      - UTF-8
      - keys sorted
      - stable separators
      - indent=2
      - newline at EOF
    \"""
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), indent=2)
    return (s + "\\n").encode("utf-8")


def canonical_jsonl_bytes(objs: Iterable[Any]) -> bytes:
    \"""
    Canonical JSONL bytes:
      - each line is canonical JSON object compressed to one line with sorted keys
      - newline at EOF
    \"""
    lines: List[str] = []
    for obj in objs:
        line = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        lines.append(line)
    return ("\\n".join(lines) + "\\n").encode("utf-8")


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_canonical_json(path: Path, obj: Any) -> None:
    write_bytes(path, canonical_json_bytes(obj))


def write_canonical_jsonl(path: Path, objs: Iterable[Any]) -> None:
    write_bytes(path, canonical_jsonl_bytes(objs))


def read_manifest_json(path: Path) -> Dict[str, str]:
    raw = load_json(path)
    if not isinstance(raw, dict):
        raise ValueError(f"Manifest must be a JSON object: {path}")
    out: Dict[str, str] = {}
    for k, v in raw.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError(f"Manifest entries must be string:string in {path}")
        out[k] = v.lower()
    return out


def write_manifest_json(path: Path, mapping: Dict[str, str]) -> None:
    ordered = {k: mapping[k] for k in sorted(mapping.keys())}
    write_canonical_json(path, ordered)


def assert_no_extra_or_missing_files(expected: Dict[str, str], out_dir: Path) -> None:
    actual_files = sorted(
        str(p.relative_to(out_dir)).replace("\\\\", "/")
        for p in out_dir.rglob("*")
        if p.is_file()
    )
    expected_files = sorted(expected.keys())

    missing = [f for f in expected_files if f not in actual_files]
    extra = [f for f in actual_files if f not in expected_files]

    if missing:
        raise RuntimeError(f"Missing output files: {', '.join(missing)}")
    if extra:
        raise RuntimeError(f"Unexpected extra output files: {', '.join(extra)}")
"""

RUN_GOLDEN_PY = """\
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from lib.canonical import (
    assert_no_extra_or_missing_files,
    load_json,
    read_manifest_json,
    sha256_bytes,
    sha256_file,
    write_canonical_json,
    write_canonical_jsonl,
)

RUNNER_VERSION = "v1.0.0"
DEFAULT_SEED = "1337"


def repo_root_from_this_file() -> Path:
    # contract/v1/golden/run_golden.py -> up 3 => repo root
    return Path(__file__).resolve().parents[3]


def compute_run_id(contract_manifest_sha: str, fixtures_manifest_sha: str, seed: str) -> str:
    payload = f"{contract_manifest_sha}\\n{fixtures_manifest_sha}\\n{RUNNER_VERSION}\\n{seed}".encode("utf-8")
    return sha256_bytes(payload)


def main() -> int:
    os.environ.setdefault("TZ", "UTC")
    seed = os.environ.get("GOLDEN_SEED", DEFAULT_SEED)

    repo_root = repo_root_from_this_file()

    contract_manifest = repo_root / "contract" / "v1" / "contract_manifest.yaml"
    fixtures_manifest = repo_root / "contract" / "v1" / "golden" / "fixtures" / "fixtures_manifest.json"
    expected_manifest = repo_root / "contract" / "v1" / "golden" / "expected" / "golden_expected_manifest.json"

    contract_sha = sha256_file(contract_manifest)
    fixtures_sha = sha256_file(fixtures_manifest)

    run_id = compute_run_id(contract_sha, fixtures_sha, seed)

    out_dir = repo_root / "contract" / "v1" / "golden" / "out" / run_id
    if out_dir.exists():
        # clean out dir
        for p in sorted(out_dir.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            else:
                try:
                    p.rmdir()
                except OSError:
                    pass
        try:
            out_dir.rmdir()
        except OSError:
            pass
    out_dir.mkdir(parents=True, exist_ok=True)

    fixtures_dir = repo_root / "contract" / "v1" / "golden" / "fixtures"

    fixture_map = read_manifest_json(fixtures_manifest)
    for rel in fixture_map.keys():
        fp = fixtures_dir / rel
        if not fp.exists():
            raise RuntimeError(f"Missing fixture file: {fp}")

    interview = load_json(fixtures_dir / "interview_payload.json")
    case_meta = load_json(fixtures_dir / "case_meta.json")
    cap_mock = load_json(fixtures_dir / "capability_gateway_mock.json")

    tool_calls: List[Dict[str, Any]] = list(cap_mock.get("tool_calls", []))

    audit = [
        {
            "ts": "1970-01-01T00:00:00Z",
            "event": "GOLDEN_RUN_START",
            "run_id": run_id,
            "seed": seed,
            "runner_version": RUNNER_VERSION,
        },
        {
            "ts": "1970-01-01T00:00:01Z",
            "event": "FIXTURES_LOADED",
            "fixtures_manifest_sha256": fixtures_sha,
            "contract_manifest_sha256": contract_sha,
        },
        {
            "ts": "1970-01-01T00:00:02Z",
            "event": "TOOL_CALLS_MOCKED",
            "count": len(tool_calls),
        },
        {
            "ts": "1970-01-01T00:00:03Z",
            "event": "EXPORT_BUNDLE_WRITTEN",
        },
    ]

    export_bundle = {
        "bundle_version": "v1",
        "run_id": run_id,
        "case": {
            "case_id": case_meta.get("case_id"),
            "caption": case_meta.get("caption"),
            "jurisdiction": case_meta.get("jurisdiction"),
        },
        "intake": {
            "interview_payload_id": interview.get("interview_payload_id"),
            "received_at": interview.get("received_at"),
        },
        "mediated_tool_calls": tool_calls,
        "invariants": [
            "case_isolation_required",
            "no_direct_db_writes",
            "supersession_only",
            "audit_ledger_required",
        ],
    }

    case_snapshot = {
        "case_id": case_meta.get("case_id"),
        "parties": case_meta.get("parties", []),
        "facts_summary": interview.get("facts_summary"),
        "documents": [],
    }

    write_canonical_json(out_dir / "export_bundle.json", export_bundle)
    write_canonical_json(out_dir / "case_snapshot.json", case_snapshot)
    write_canonical_jsonl(out_dir / "tool_calls.jsonl", tool_calls)
    write_canonical_jsonl(out_dir / "audit_ledger.jsonl", audit)

    hashes: Dict[str, str] = {}
    for name in ["export_bundle.json", "case_snapshot.json", "tool_calls.jsonl", "audit_ledger.jsonl"]:
        hashes[name] = sha256_file(out_dir / name)
    write_canonical_json(out_dir / "hashes.json", {"files": hashes})

    report = {
        "run_id": run_id,
        "runner_version": RUNNER_VERSION,
        "seed": seed,
        "contract_manifest_sha256": contract_sha,
        "fixtures_manifest_sha256": fixtures_sha,
        "outputs": hashes,
    }
    write_canonical_json(out_dir / "workflow_report.json", report)

    expected = read_manifest_json(expected_manifest)
    assert_no_extra_or_missing_files(expected, out_dir)

    for rel, exp_hash in expected.items():
        actual_hash = sha256_file(out_dir / rel)
        if actual_hash.lower() != exp_hash.lower():
            raise RuntimeError(f"Golden mismatch: {rel} expected {exp_hash} got {actual_hash}")

    print(f"GOLDEN PASS ✅  RUN_ID={run_id}  OUT={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

PIN_GOLDEN_PY = """\
from __future__ import annotations

import os
from pathlib import Path
import hashlib

from lib.canonical import sha256_file, write_manifest_json

RUNNER_VERSION = "v1.0.0"
DEFAULT_SEED = "1337"


def repo_root_from_this_file() -> Path:
    # contract/v1/golden/pin_golden_hashes.py -> up 3 => repo root
    return Path(__file__).resolve().parents[3]


def compute_run_id(contract_sha: str, fixtures_sha: str, seed: str) -> str:
    payload = f"{contract_sha}\\n{fixtures_sha}\\n{RUNNER_VERSION}\\n{seed}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    os.environ.setdefault("TZ", "UTC")
    seed = os.environ.get("GOLDEN_SEED", DEFAULT_SEED)

    repo_root = repo_root_from_this_file()
    fixtures_dir = repo_root / "contract" / "v1" / "golden" / "fixtures"
    expected_dir = repo_root / "contract" / "v1" / "golden" / "expected"
    out_root = repo_root / "contract" / "v1" / "golden" / "out"

    contract_manifest = repo_root / "contract" / "v1" / "contract_manifest.yaml"

    # Pin fixtures manifest
    fixtures_manifest_path = fixtures_dir / "fixtures_manifest.json"
    fixtures = {
        "interview_payload.json": sha256_file(fixtures_dir / "interview_payload.json"),
        "case_meta.json": sha256_file(fixtures_dir / "case_meta.json"),
        "capability_gateway_mock.json": sha256_file(fixtures_dir / "capability_gateway_mock.json"),
    }
    write_manifest_json(fixtures_manifest_path, fixtures)

    # Run golden runner
    from run_golden import main as run_main  # type: ignore
    run_main()

    # Locate deterministic out dir
    contract_sha = sha256_file(contract_manifest)
    fixtures_sha = sha256_file(fixtures_manifest_path)
    run_id = compute_run_id(contract_sha, fixtures_sha, seed)
    out_dir = out_root / run_id

    # Pin expected manifest from outputs
    expected_manifest_path = expected_dir / "golden_expected_manifest.json"
    expected = {
        "export_bundle.json": sha256_file(out_dir / "export_bundle.json"),
        "case_snapshot.json": sha256_file(out_dir / "case_snapshot.json"),
        "tool_calls.jsonl": sha256_file(out_dir / "tool_calls.jsonl"),
        "audit_ledger.jsonl": sha256_file(out_dir / "audit_ledger.jsonl"),
        "hashes.json": sha256_file(out_dir / "hashes.json"),
        "workflow_report.json": sha256_file(out_dir / "workflow_report.json"),
    }
    write_manifest_json(expected_manifest_path, expected)

    print("PIN COMPLETE ✅")
    print(f"RUN_ID={run_id}")
    print(f"OUT={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


INIT_PY = """\
# Package marker for golden harness library.
"""

EMPTY_MANIFEST_JSON = "{\n}\n"


# -----------------------------
# Main migration
# -----------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gate 8 migration: create Python+JSON golden harness and quarantine legacy PowerShell/YAML harness artifacts."
    )
    parser.add_argument("--apply", action="store_true", help="Actually perform changes. Default is dry-run.")
    parser.add_argument("--purge-archive", action="store_true", help="Delete the legacy archive after moving files (destructive).")
    parser.add_argument(
        "--archive-dir",
        default="contract/v1/golden/_legacy_archive",
        help="Archive directory (relative to repo root) where legacy files will be moved.",
    )
    parser.add_argument(
        "--overwrite-python",
        action="store_true",
        help="Overwrite existing Python harness files if they already exist.",
    )
    args = parser.parse_args()

    apply = args.apply
    overwrite_py = args.overwrite_python

    repo_root = repo_root_from_this_file()
    golden_dir = repo_root / "contract" / "v1" / "golden"
    lib_dir = golden_dir / "lib"
    fixtures_dir = golden_dir / "fixtures"
    expected_dir = golden_dir / "expected"
    out_dir = golden_dir / "out"

    archive_root = repo_root / args.archive_dir

    actions: List[str] = []

    # Ensure dirs
    ensure_dir(golden_dir, apply, actions)
    ensure_dir(lib_dir, apply, actions)
    ensure_dir(fixtures_dir, apply, actions)
    ensure_dir(expected_dir, apply, actions)
    ensure_dir(out_dir, apply, actions)
    ensure_dir(archive_root, apply, actions)

    # Write python harness files
    write_file(lib_dir / "__init__.py", INIT_PY, apply, actions, overwrite=overwrite_py)
    write_file(lib_dir / "canonical.py", CANONICAL_PY, apply, actions, overwrite=overwrite_py)
    write_file(golden_dir / "run_golden.py", RUN_GOLDEN_PY, apply, actions, overwrite=overwrite_py)
    write_file(golden_dir / "pin_golden_hashes.py", PIN_GOLDEN_PY, apply, actions, overwrite=overwrite_py)

    # Ensure JSON manifests exist (pin will overwrite fixtures_manifest.json; expected may be filled after pin)
    write_file(fixtures_dir / "fixtures_manifest.json", EMPTY_MANIFEST_JSON, apply, actions, overwrite=False)
    write_file(expected_dir / "golden_expected_manifest.json", EMPTY_MANIFEST_JSON, apply, actions, overwrite=False)

    # Quarantine legacy Gate 8 artifacts (safe move to archive)
    legacy_paths: List[Path] = [
        golden_dir / "run_golden.ps1",
        golden_dir / "pin_golden_hashes.ps1",
        lib_dir / "golden_common.ps1",
        fixtures_dir / "fixtures_manifest.yaml",
        expected_dir / "golden_expected_manifest.yaml",
        expected_dir / "golden_expected_manifest.yml",
    ]

    for p in legacy_paths:
        move_to_archive(p, archive_root, apply, actions)

    # Optionally purge archive (destructive)
    if args.purge_archive:
        remove_path(archive_root, apply, actions)

    # Print plan / result
    header = "APPLY MODE ✅ (changes executed)" if apply else "DRY RUN 🟡 (no changes made)"
    print(header)
    print("-" * 80)
    for a in actions:
        print(a)
    print("-" * 80)

    if not apply:
        print("Next: re-run with --apply to execute the migration.")
    else:
        print("Next: run the golden pin + run commands:")
        print("  python contract/v1/golden/pin_golden_hashes.py")
        print("  python contract/v1/golden/run_golden.py")
        print("Then update CI job to call python scripts (if not already).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())