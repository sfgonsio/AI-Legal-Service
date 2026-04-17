from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE_ROOT = HERE.parent
SRC = PACKAGE_ROOT / "src"
sys.path.insert(0, str(SRC))

from pipeline_runner import run_stage  # type: ignore

def main():
    run_stage(
        "FACT_NORMALIZATION",
        PACKAGE_ROOT / "sample_inputs" / "fact_normalization.input.json",
        PACKAGE_ROOT / "sample_outputs" / "fact_normalization.output.json",
    )
    run_stage(
        "TAGGING",
        PACKAGE_ROOT / "sample_inputs" / "tagging.input.json",
        PACKAGE_ROOT / "sample_outputs" / "tagging.output.json",
    )
    run_stage(
        "COMPOSITE_ENGINE",
        PACKAGE_ROOT / "sample_inputs" / "composite_engine.input.json",
        PACKAGE_ROOT / "sample_outputs" / "event_mapping.output.json",
    )
    run_stage(
        "COA_ENGINE",
        PACKAGE_ROOT / "sample_inputs" / "coa_engine.input.json",
        PACKAGE_ROOT / "sample_outputs" / "coa_engine.output.json",
    )

    out_dir = PACKAGE_ROOT / "sample_outputs"
    assert (out_dir / "fact_normalization.output.json").exists()
    assert (out_dir / "tagging.output.json").exists()
    assert (out_dir / "event_mapping.output.json").exists()
    assert (out_dir / "coa_engine.output.json").exists()

    print("PASS: Pipeline stage shells generated sample outputs")

if __name__ == "__main__":
    main()
