from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(r"C:\Users\sfgon\Documents\GitHub\AI Legal Service")
SPEC_ROOT = REPO_ROOT / "casecore-spec"

SCHEMA_EXAMPLE_VALIDATOR = SPEC_ROOT / "validators" / "validate_schema_examples.ps1"
PIPELINE_VALIDATOR = SPEC_ROOT / "validators" / "pipeline" / "validate_pipeline_outputs.ps1"
RUNTIME_VALIDATOR = SPEC_ROOT / "validators" / "runtime" / "validate_runtime_output.ps1"
