import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema package is not installed. Run: python -m pip install jsonschema")
    sys.exit(2)

def load_json(path_str: str):
    path = Path(path_str)
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def main():
    if len(sys.argv) != 3:
        print("Usage: validate_json_artifact.py <schema.json> <instance.json>")
        sys.exit(1)

    schema_path = sys.argv[1]
    instance_path = sys.argv[2]

    schema = load_json(schema_path)
    instance = load_json(instance_path)

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)

    if errors:
        print(f"FAIL: {Path(instance_path).name} did not validate against {Path(schema_path).name}")
        for err in errors:
            loc = ".".join(str(x) for x in err.path) if err.path else "<root>"
            print(f" - {loc}: {err.message}")
        sys.exit(1)

    print(f"PASS: {Path(instance_path).name} validated against {Path(schema_path).name}")

if __name__ == "__main__":
    main()
