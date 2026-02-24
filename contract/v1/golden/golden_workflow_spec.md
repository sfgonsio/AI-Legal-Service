# Golden Workflow Spec — Contract v1 (Authoritative)

Purpose: Deterministic, end-to-end “happy path” run that proves platform behavior cannot regress.

## Scope
- This spec defines ONLY: inputs, steps, outputs, acceptance criteria, deterministic naming, and comparison rules.
- This spec does NOT define implementation logic for agents, DB, or tools.

## Determinism Rules
The golden workflow MUST run with:
- No network access (runner enforces; CI denies network by policy + no external calls).
- Fixed timezone: UTC
- Fixed culture/locale for serialization: invariant (enforced by runner)
- Pinned seed: `GOLDEN_SEED=1337`
- Stable ordering rules:
  - All lists that are not semantically ordered MUST be sorted lexicographically by stable keys before writing outputs.
  - JSON must be canonicalized (key ordering + whitespace rules defined below).

## Golden Run ID
A run is uniquely identified by:

`RUN_ID = SHA256( contract_manifest_sha256 + "\n" + fixtures_manifest_sha256 + "\n" + runner_version + "\n" + GOLDEN_SEED )`

- `contract_manifest_sha256` is SHA256 of `contract/v1/contract_manifest.yaml` file bytes.
- `fixtures_manifest_sha256` is SHA256 of `contract/v1/golden/fixtures/fixtures_manifest.yaml` file bytes.
- `runner_version` is a string constant in the runner script (e.g., `v1.0.0`).
- `GOLDEN_SEED` is a required env var or defaults to 1337.

## Inputs (Fixtures)
Authoritative fixture set is defined in:
- `contract/v1/golden/fixtures/fixtures_manifest.yaml`
- Each fixture file is immutable once promoted to golden.

Minimum required fixtures:
1. `interview_payload.json` (client intake transcript/payload)
2. `case_meta.json` (case identifier, parties, venue, etc.)
3. `capability_gateway_mock.json` (tool mediation mock responses)

## Steps (Happy Path)
The runner executes these stages, producing artifacts at each stage:

S1. Load fixtures
- Validate fixture schema presence (not correctness beyond required fields).
- Compute `fixtures_manifest_sha256`.

S2. Establish deterministic runtime
- Set TZ=UTC, invariant culture
- Set seed
- Disable network (best-effort locally; mandatory in CI by policy)

S3. Execute “Golden Orchestration” (mocked / pinned)
- Invoke orchestration entrypoint (contract-defined interface)
- Tool access must route through capability gateway mock
- No direct DB writes; only produce planned actions + mediated tool calls in outputs

S4. Produce Evidence Bundle
- Emit deterministic export bundle:
  - `export_bundle.json`
  - `audit_ledger.jsonl` (append-only)
  - `case_snapshot.json` (logical read model, no DB writes)
  - `tool_calls.jsonl` (mediated, capability-scoped)
  - `workflow_report.json` (stage metrics + hashes)

S5. Compare outputs to Golden Expected
- Compare file hashes against `contract/v1/golden/expected/golden_expected_manifest.yaml`
- Any deviation FAILS.

## Output Bundle Layout
Output root:
`contract/v1/golden/out/<RUN_ID>/`

Files:
- `export_bundle.json`
- `audit_ledger.jsonl`
- `case_snapshot.json`
- `tool_calls.jsonl`
- `workflow_report.json`
- `hashes.json` (computed SHA256 for each file)

## Canonical JSON Rules
All `.json` outputs MUST be written as:
- UTF-8 (no BOM)
- Keys sorted ascending
- 2-space indentation
- Newline at EOF

All `.jsonl` outputs MUST be:
- UTF-8 (no BOM)
- Each line a canonical JSON object per above rules (single-line, keys sorted)
- Newline at EOF

## Acceptance Criteria (Gate 8 PASS ✅)
A run is considered a PASS iff:
1. Runner completes without error
2. Network access is not used (CI environment guarantees; local runner best-effort detection)
3. Outputs are produced in the required bundle layout
4. Output hashes match `golden_expected_manifest.yaml`
5. `workflow_report.json` includes:
   - RUN_ID
   - contract_manifest_sha256
   - fixtures_manifest_sha256
   - runner_version
   - seed
   - output file hashes
6. The job fails if any output deviates (hash mismatch, missing file, extra file)

End.