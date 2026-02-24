from __future__ import annotations

import hashlib
import os
from pathlib import Path

from lib.canonical import sha256_file, write_manifest_json

RUNNER_VERSION = "v1.0.0"
DEFAULT_SEED = "1337"


def repo_root_from_this_file() -> Path:
    # contract/v1/golden/pin_golden_hashes.py -> up 3 => repo root
    return Path(__file__).resolve().parents[3]


def compute_run_id(contract_sha: str, fixtures_sha: str, seed: str) -> str:
    payload = f"{contract_sha}\n{fixtures_sha}\n{RUNNER_VERSION}\n{seed}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    os.environ.setdefault("TZ", "UTC")
    seed = os.environ.get("GOLDEN_SEED", DEFAULT_SEED)

    repo_root = repo_root_from_this_file()
    fixtures_dir = repo_root / "contract" / "v1" / "golden" / "fixtures"
    expected_dir = repo_root / "contract" / "v1" / "golden" / "expected"
    out_root = repo_root / "contract" / "v1" / "golden" / "out"

    contract_manifest = repo_root / "contract" / "v1" / "contract_manifest.yaml"

    # 1) Pin fixtures manifest
    fixtures_manifest_path = fixtures_dir / "fixtures_manifest.json"
    fixtures = {
        "interview_payload.json": sha256_file(fixtures_dir / "interview_payload.json"),
        "case_meta.json": sha256_file(fixtures_dir / "case_meta.json"),
        "capability_gateway_mock.json": sha256_file(fixtures_dir / "capability_gateway_mock.json"),
    }
    write_manifest_json(fixtures_manifest_path, fixtures)

    # 2) Run golden runner WITHOUT compare (bootstrap)
    from run_golden import main as run_main  # type: ignore

    os.environ["GOLDEN_SKIP_COMPARE"] = "1"
    run_main()
    os.environ.pop("GOLDEN_SKIP_COMPARE", None)

    # 3) Compute RUN_ID so we can locate out dir deterministically
    contract_sha = sha256_file(contract_manifest)
    fixtures_sha = sha256_file(fixtures_manifest_path)
    run_id = compute_run_id(contract_sha, fixtures_sha, seed)
    out_dir = out_root / run_id

    # 4) Pin expected manifest from outputs
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