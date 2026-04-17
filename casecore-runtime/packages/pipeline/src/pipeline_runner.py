from __future__ import annotations

from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
PACKAGE_ROOT = HERE.parent
REPO_ROOT = PACKAGE_ROOT.parent.parent.parent

sys.path.insert(0, str(REPO_ROOT / "casecore-runtime" / "packages" / "validators" / "src"))
from run_validators import run_all  # type: ignore

def load_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)

def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def run_stage(stage_name: str, input_path: Path, output_path: Path):
    payload = load_json(input_path)

    if stage_name == "FACT_NORMALIZATION":
        out = {
            "id": "FCT-PIPE-RUN-001",
            "matter_id": payload["matter_id"],
            "artifact_type": "FACT",
            "schema_version": "1.0.0",
            "statement": payload["text"],
            "source_refs": [payload["source_ref"]],
            "status": "proposed",
            "run_id": payload["run_id"],
            "created_at": payload["created_at"],
            "confidence": 0.95
        }
    elif stage_name == "TAGGING":
        out = {
            "id": "TAG-PIPE-RUN-001",
            "matter_id": payload["matter_id"],
            "artifact_type": "TAG_ASSIGNMENT",
            "schema_version": "1.0.0",
            "label": "payment",
            "taxonomy_group": "issue_tags",
            "target_ref": payload["target_ref"],
            "status": "proposed",
            "created_at": payload["created_at"]
        }
    elif stage_name == "COMPOSITE_ENGINE":
        out = {
            "id": "EVT-PIPE-RUN-001",
            "matter_id": payload["matter_id"],
            "artifact_type": "EVENT",
            "schema_version": "1.0.0",
            "label": "Payment Due",
            "fact_refs": payload["fact_refs"],
            "entity_refs": ["ENT-001"],
            "source_refs": payload["source_refs"],
            "status": "proposed",
            "run_id": payload["run_id"],
            "created_at": payload["created_at"]
        }
    elif stage_name == "COA_ENGINE":
        out = {
            "id": "COA-PIPE-RUN-001",
            "matter_id": payload["matter_id"],
            "artifact_type": "COA_ELEMENT_COVERAGE",
            "schema_version": "1.0.0",
            "case_type": "civil",
            "coa_name": "breach_of_contract",
            "element_name": "breach",
            "coverage_status": "supported",
            "support_refs": payload["support_refs"],
            "run_id": payload["run_id"],
            "created_at": payload["created_at"]
        }
    else:
        raise ValueError(f"Unknown stage: {stage_name}")

    write_json(output_path, out)

def main():
    run_all()
    print("PASS: Validator stack callable from pipeline runner")

if __name__ == "__main__":
    main()
