# Stage 14 — Deterministic Replay Equivalence (Authoritative)

## Purpose
Stage 13 enforced that replay vectors exist.
Stage 14 enforces that replay vectors are **executably verifiable** and that replay runs **match committed canonical outputs**.

This converts determinism from:
- “Vectors exist”
to:
- “Vectors execute and match canonical expected outputs in CI”

## Definitions
**Replay Vector**
A JSON file under `contract/v1/harness/replay_vectors/` that specifies a replay input (and optionally, which contract artifacts to fingerprint).

**Canonical Expected Output**
A JSON file paired with each vector:
- `<vector>.expected.json`

It is produced only by an explicit freeze operation and committed to git.

**Replay Equivalence**
For each vector, the replay runner computes an output object and compares it to the canonical expected output.
The replay is equivalent if and only if these match exactly.

## Pairing rule
For a vector file:
- `X.json`
the expected file must be:
- `X.expected.json`

## Output schema (v1)
The replay runner produces an object with:
- `schema_version`: `"replay_equivalence_v1"`
- `vector_id`: string
- `fingerprints`: map of relative-path → sha256
- `missing_artifacts`: list of missing relative paths

**Determinism rules**
- Output JSON uses stable ordering (sorted keys, stable indentation).
- No timestamps or environment-dependent values are included.
- Paths are emitted with forward slashes.

## Fingerprints
A vector may include `include_paths` (relative to `contract/v1`) to specify which files to fingerprint.
If not provided, a conservative default set is used.

The runner also fingerprints the vector file itself to prevent silent vector mutation.

## Modes
**Verify (CI / default)**
- Computes outputs and compares to `<vector>.expected.json`
- Fails if mismatch, or if expected file is missing

**Freeze (manual)**
- Computes outputs and writes `<vector>.expected.json`
- This is the only allowed way to refresh canonical outputs

## Gate enforcement
Stage 14 is enforced via:
- `contract/v1/acceptance/validate_contract.ps1` calling `run_replay.py` in verify mode.

A mismatch must fail the validator, and therefore must fail CI.

## Failure modes (intended)
- Expected file missing → fail
- Fingerprint mismatch → fail
- Missing artifacts (if strict mode enabled) → fail
- No vectors present → fail