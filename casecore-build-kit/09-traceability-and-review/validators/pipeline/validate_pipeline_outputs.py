import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema package is not installed. Run: python -m pip install jsonschema")
    sys.exit(2)

ROOT = Path(r"C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-spec")
SCHEMA_DIR = ROOT / "packages" / "contracts" / "schemas"
OUTPUT_DIR = ROOT / "validators" / "pipeline" / "sample_outputs"

PIPELINE_MAP = [
    ("fact_normalization.output.json", "casecore.fact.schema.json"),
    ("tagging.output.json", "casecore.tag.schema.json"),
    ("event_mapping.output.json", "casecore.event.schema.json"),
    ("coa_engine.output.json", "casecore.coa-element-coverage.schema.json"),
    ("proposal.output.json", "casecore.proposal-envelope.schema.json"),
]

def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def validate_pair(instance_path: Path, schema_path: Path):
    schema = load_json(schema_path)
    instance = load_json(instance_path)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        print(f"FAIL: {instance_path.name} against {schema_path.name}")
        for err in errors:
            loc = ".".join(str(x) for x in err.path) if err.path else "<root>"
            print(f" - {loc}: {err.message}")
        return False
    print(f"PASS: {instance_path.name} -> {schema_path.name}")
    return True

def main():
    ok = True
    for output_name, schema_name in PIPELINE_MAP:
        instance_path = OUTPUT_DIR / output_name
        schema_path = SCHEMA_DIR / schema_name
        try:
            valid = validate_pair(instance_path, schema_path)
            if not valid:
                ok = False
        except Exception as e:
            print(f"FAIL: {output_name}: {e}")
            ok = False
    if not ok:
        sys.exit(1)
    print("ALL PIPELINE OUTPUT VALIDATIONS PASSED")

if __name__ == "__main__":
    main()
