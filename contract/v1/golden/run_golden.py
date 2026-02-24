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
    payload = f"{contract_manifest_sha}\n{fixtures_manifest_sha}\n{RUNNER_VERSION}\n{seed}".encode("utf-8")
    return sha256_bytes(payload)


def clean_dir(path: Path) -> None:
    if not path.exists():
        return
    for p in sorted(path.rglob("*"), reverse=True):
        if p.is_file():
            p.unlink()
        else:
            try:
                p.rmdir()
            except OSError:
                pass
    try:
        path.rmdir()
    except OSError:
        pass


def main() -> int:
    # Deterministic env (best effort)
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
        clean_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fixtures_dir = repo_root / "contract" / "v1" / "golden" / "fixtures"

    # Validate fixture presence per manifest
    fixture_map = read_manifest_json(fixtures_manifest)
    for rel in fixture_map.keys():
        fp = fixtures_dir / rel
        if not fp.exists():
            raise RuntimeError(f"Missing fixture file: {fp}")

    # Load fixtures
    interview = load_json(fixtures_dir / "interview_payload.json")
    case_meta = load_json(fixtures_dir / "case_meta.json")
    cap_mock = load_json(fixtures_dir / "capability_gateway_mock.json")

    tool_calls: List[Dict[str, Any]] = list(cap_mock.get("tool_calls", []))

    # Deterministic audit ledger lines (append-only)
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

    # Export bundle (contract-aligned minimal baseline)
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

    # Case snapshot (logical read model only)
    case_snapshot = {
        "case_id": case_meta.get("case_id"),
        "parties": case_meta.get("parties", []),
        "facts_summary": interview.get("facts_summary"),
        "documents": [],
    }

    # Write outputs
    write_canonical_json(out_dir / "export_bundle.json", export_bundle)
    write_canonical_json(out_dir / "case_snapshot.json", case_snapshot)
    write_canonical_jsonl(out_dir / "tool_calls.jsonl", tool_calls)
    write_canonical_jsonl(out_dir / "audit_ledger.jsonl", audit)

    # hashes.json (hash the core artifacts)
    hashes: Dict[str, str] = {}
    for name in ["export_bundle.json", "case_snapshot.json", "tool_calls.jsonl", "audit_ledger.jsonl"]:
        hashes[name] = sha256_file(out_dir / name)
    write_canonical_json(out_dir / "hashes.json", {"files": hashes})

    # workflow_report.json (summary)
    report = {
        "run_id": run_id,
        "runner_version": RUNNER_VERSION,
        "seed": seed,
        "contract_manifest_sha256": contract_sha,
        "fixtures_manifest_sha256": fixtures_sha,
        "outputs": hashes,
    }
    write_canonical_json(out_dir / "workflow_report.json", report)

    # Compare to expected unless explicitly skipped (bootstrap pin)
    skip_compare = os.environ.get("GOLDEN_SKIP_COMPARE", "").strip().lower() in {"1", "true", "yes"}

    if not skip_compare:
        expected = read_manifest_json(expected_manifest)
        assert_no_extra_or_missing_files(expected, out_dir)

        for rel, exp_hash in expected.items():
            actual_hash = sha256_file(out_dir / rel)
            if actual_hash.lower() != exp_hash.lower():
                raise RuntimeError(f"Golden mismatch: {rel} expected {exp_hash} got {actual_hash}")
    else:
        print("NOTE: GOLDEN_SKIP_COMPARE enabled (no expected-manifest enforcement for this run).")

    print(f"GOLDEN PASS ✅  RUN_ID={run_id}  OUT={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())