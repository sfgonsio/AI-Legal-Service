# Replay Vector Spec (Contract v1)

Purpose:
Replay vectors are minimal, versioned fixtures that allow the harness to re-run a deterministic workflow input and later verify outputs.
Stage 13 introduces ONLY SSOT structure + validator enforcement (no runtime replay logic yet).

Directory:
contract/v1/harness/replay_vectors/

Requirements (Stage 13 DoD):
- Directory must exist
- At least one replay vector file must exist
- Validator must fail if directory missing
- Validator must fail if zero vectors exist

Vector File Format:
- One file per vector
- Allowed extensions: .json (preferred), .yaml, .yml
- Files MUST be non-empty
- UTF-8 text (no silent encoding drift)

Minimal Required Fields (v1):
- vector_version: string (e.g., "1")
- vector_id: string (stable identifier, filename should match or contain it)
- description: string
- contract_version: string (e.g., "v1")
- request_path: string (relative path to a harness request payload under contract/v1/)
- notes: string (optional; may be empty)

Guidance:
- request_path MUST be relative to contract/v1/
- Replay vectors are SSOT artifacts and must be listed in contract_manifest.yaml
- Future stages may add expected outputs, fingerprints, and golden comparisons, but Stage 13 stops at presence + documentation + enforcement.
