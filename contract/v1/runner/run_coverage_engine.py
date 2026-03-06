import json
import argparse
from pathlib import Path
from datetime import datetime, timezone


def load_json(path: str):
    # utf-8-sig safely handles BOM if present (common on Windows)
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(data, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def extract_values(case_data, path: str):
    """
    Resolves dotted paths including list wildcards.

    Example:
      signals.agreements[*].attributes.exists

    Semantics:
      - Each segment walks "nodes" forward.
      - "[*]" expands lists.
      - Returns a flat list of resolved values (possibly empty).
    """
    parts = path.split(".")
    nodes = [case_data]

    for part in parts:
        next_nodes = []

        if part.endswith("[*]"):
            key = part[:-3]
            for node in nodes:
                if isinstance(node, dict):
                    v = node.get(key)
                    if isinstance(v, list):
                        next_nodes.extend(v)
        else:
            for node in nodes:
                if isinstance(node, dict) and part in node:
                    next_nodes.append(node[part])

        nodes = next_nodes
        if not nodes:
            return []

    return nodes


def evaluate_predicate(case_data, predicate: dict) -> bool:
    values = extract_values(case_data, predicate["path"])
    operator = predicate["operator"]
    value = predicate.get("value")

    if operator == "exists":
        return len(values) > 0

    if operator == "non_empty":
        return any(v not in (None, "", [], {}) for v in values)

    if operator == "equals":
        return any(v == value for v in values)

    if operator == "contains":
        # stringify safely
        return any(value in str(v) for v in values)

    return False


def evaluate_element(case_data, element: dict) -> str:
    required = element.get("required_predicates", [])
    supporting = element.get("supporting_predicates", [])

    required_matches = sum(1 for p in required if evaluate_predicate(case_data, p))
    supporting_matches = sum(1 for p in supporting if evaluate_predicate(case_data, p))

    strong_threshold = element["strong_threshold"]["min_required_matches"]
    weak_threshold = element["weak_threshold"]["min_required_matches"]

    if required_matches >= strong_threshold:
        return "strong"

    if required_matches >= weak_threshold:
        return "weak"

    if required_matches == 0 and supporting_matches == 0:
        return "unknown"

    return "not_supported"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract_root", required=True)  # reserved for future validation hooks
    parser.add_argument("--case", required=True)
    parser.add_argument("--modules", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    case_data = load_json(args.case)
    module = load_json(args.modules)

    results = []
    for element in module.get("elements", []):
        status = evaluate_element(case_data, element)
        results.append({"element_id": element["element_id"], "status": status})

    report = {
        "schema_version": "coverage_report.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "module_id": module.get("module_id", "unknown_module"),
        "results": results,
    }

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / "coverage_report.json"
    save_json(report, outfile)
    print(f"Coverage report written to {outfile}")


if __name__ == "__main__":
    main()