import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema package is not installed. Run: python -m pip install jsonschema")
    sys.exit(2)

ALLOWED_ARTIFACT_TRANSITIONS = {
    ("proposed", "canonical"),
    ("proposed", "rejected"),
    ("pending", "approved"),
    ("pending", "rejected"),
    ("approved", "overridden"),
}

REPO_ROOT = Path(r"C:\Users\sfgon\Documents\GitHub\AI Legal Service")
SPEC_ROOT = REPO_ROOT / "casecore-spec"
SCHEMA_DIR = SPEC_ROOT / "packages" / "contracts" / "schemas"
RUNTIME_DIR = SPEC_ROOT / "validators" / "runtime" / "sample_runtime"

SCHEMA_MAP = {
    "FACT": "casecore.fact.schema.json",
    "EVENT": "casecore.event.schema.json",
    "ENTITY": "casecore.entity.schema.json",
    "TAG_ASSIGNMENT": "casecore.tag.schema.json",
    "COA_ELEMENT_COVERAGE": "casecore.coa-element-coverage.schema.json",
    "PROPOSAL": "casecore.proposal-envelope.schema.json",
}

def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)

def validate_schema(instance: dict):
    artifact_type = instance.get("artifact_type")
    if artifact_type == "PROPOSAL" or "proposal_id" in instance:
        schema_name = SCHEMA_MAP["PROPOSAL"]
    else:
        if artifact_type not in SCHEMA_MAP:
            raise ValueError(f"Unsupported artifact_type: {artifact_type}")
        schema_name = SCHEMA_MAP[artifact_type]

    schema = load_json(SCHEMA_DIR / schema_name)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        msgs = []
        for err in errors:
            loc = ".".join(str(x) for x in err.path) if err.path else "<root>"
            msgs.append(f"{loc}: {err.message}")
        raise ValueError("Schema validation failed: " + " | ".join(msgs))

def validate_transition(request: dict):
    from_state = request.get("from_state")
    to_state = request.get("to_state")
    if (from_state, to_state) not in ALLOWED_ARTIFACT_TRANSITIONS:
        raise ValueError(f"Invalid transition: {from_state} -> {to_state}")

def validate_audit_record(audit: dict):
    required = ["event_id", "timestamp", "actor_id", "action", "target_id", "run_id"]
    missing = [k for k in required if k not in audit or audit[k] in (None, "", [])]
    if missing:
        raise ValueError(f"Audit validation failed. Missing fields: {missing}")

def main():
    artifact = load_json(RUNTIME_DIR / "runtime_artifact.json")
    transition = load_json(RUNTIME_DIR / "runtime_transition.json")
    audit = load_json(RUNTIME_DIR / "runtime_audit.json")

    validate_schema(artifact)
    validate_transition(transition)
    validate_audit_record(audit)

    print("PASS: Runtime artifact schema valid")
    print("PASS: Runtime transition valid")
    print("PASS: Runtime audit record valid")
    print("ALL RUNTIME ENFORCEMENT CHECKS PASSED")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
