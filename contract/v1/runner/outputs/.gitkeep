
---

## B) `contract/v1/runner/run_pattern_pack_bundle.py`

```python
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

# -------------------------
# Helpers
# -------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def fail(msg: str) -> None:
    print(f"\nFAIL: {msg}", file=sys.stderr)
    sys.exit(1)

def ok(msg: str) -> None:
    print(f"OK: {msg}")

def read_text(path: Path) -> str:
    if not path.exists():
        fail(f"Missing file: {path}")
    return path.read_text(encoding="utf-8", errors="strict")

def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())

# -------------------------
# Ultra-light YAML extraction
# (We avoid full YAML parsing; we only need a small subset.)
# -------------------------

def extract_archetype_block(archetypes_text: str, archetype_id: str) -> str:
    """
    Extracts a block starting at '- archetype_id: <id>' until the next '- archetype_id:' or EOF.
    Works for our controlled archetypes.yaml shape.
    """
    pattern = re.compile(rf"(?ms)^\s*-\s*archetype_id:\s*{re.escape(archetype_id)}\s*$.*?(?=^\s*-\s*archetype_id:|\Z)")
    m = pattern.search(archetypes_text)
    if not m:
        fail(f"archetype_id not found in archetypes.yaml: {archetype_id}")
    return m.group(0)

def extract_list(block_text: str, key: str) -> list[str]:
    """
    Extracts YAML list values under a key like:
      jury_instruction_refs:
        - CACI_303
        - CACI_370
    Returns list of strings.
    """
    # find section for key:
    m = re.search(rf"(?ms)^\s*{re.escape(key)}\s*:\s*\n(?P<body>(?:^\s*-\s*.+\n)+)", block_text)
    if not m:
        return []
    body = m.group("body")
    items = []
    for line in body.splitlines():
        mm = re.match(r"^\s*-\s*(.+?)\s*$", line)
        if mm:
            items.append(mm.group(1).strip().strip('"').strip("'"))
    return items

def extract_scalar(block_text: str, key: str) -> str | None:
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", block_text)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'")

def authority_key_exists(authority_text: str, key: str) -> bool:
    # authority_catalog:
    #   CACI_303:
    #     title: ...
    return re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*$", authority_text) is not None

def extract_authority_elements(authority_text: str, key: str) -> list[dict]:
    """
    Very controlled extraction:
    Finds block:
      <key>:
        ...
        elements:
          - element_id: ...
            proof_types: [...]
    We only extract element_id and proof_types (either inline list or dash list).
    """
    # Extract the authority entry block
    entry_pat = re.compile(rf"(?ms)^\s*{re.escape(key)}\s*:\s*$.*?(?=^\s*[A-Z0-9_]+:\s*$|\Z)")
    entry_m = entry_pat.search(authority_text)
    if not entry_m:
        fail(f"authority_catalog missing key (unexpected): {key}")
    entry = entry_m.group(0)

    # Find elements block (dash items)
    elems = []
    # Match each "- element_id: X" and capture following indented lines until next "- element_id" or end of elements list
    elem_pat = re.compile(r"(?ms)^\s*-\s*element_id:\s*(?P<id>.+?)\s*$.*?(?=^\s*-\s*element_id:|\Z)")
    # First narrow to the 'elements:' section if present
    elements_section = None
    sec_m = re.search(r"(?ms)^\s*elements\s*:\s*\n(?P<body>.*)$", entry)
    if sec_m:
        elements_section = sec_m.group("body")
    else:
        return elems

    for m in elem_pat.finditer(elements_section):
        eid = m.group("id").strip().strip('"').strip("'")
        chunk = m.group(0)

        # proof_types as inline [a, b] or dash list under proof_types:
        proof_types = []
        inline = re.search(r"(?m)^\s*proof_types\s*:\s*\[(?P<inside>[^\]]+)\]\s*$", chunk)
        if inline:
            proof_types = [x.strip().strip('"').strip("'") for x in inline.group("inside").split(",") if x.strip()]
        else:
            pt_body = re.search(r"(?ms)^\s*proof_types\s*:\s*\n(?P<body>(?:^\s*-\s*.+\n)+)", chunk)
            if pt_body:
                for line in pt_body.group("body").splitlines():
                    mm = re.match(r"^\s*-\s*(.+?)\s*$", line)
                    if mm:
                        proof_types.append(mm.group(1).strip().strip('"').strip("'"))

        if not proof_types:
            # Keep deterministic: require at least 1 proof type.
            proof_types = ["unspecified"]

        elems.append({
            "element_id": eid,
            "authority_refs": [key],
            "proof_types": sorted(set(proof_types)),
        })

    return elems

# -------------------------
# Main runner
# -------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract_root", required=True)
    ap.add_argument("--run_id", required=True)
    ap.add_argument("--jurisdiction", default="CA")
    ap.add_argument("--mode", default="neutral_diagnostic")
    ap.add_argument("--case_signal_profile", required=True)
    ap.add_argument("--selected_archetype_id", required=True)
    args = ap.parse_args()

    contract_root = Path(args.contract_root).resolve()
    run_id = args.run_id.strip()
    if len(run_id) < 3:
        fail("run_id too short")

    out_root = contract_root / "runner" / "outputs" / "pattern_pack_bundles" / run_id
    out_root.mkdir(parents=True, exist_ok=True)

    # Paths
    archetypes_path = contract_root / "taxonomies" / "pattern_packs" / "archetypes.yaml"
    authority_path  = contract_root / "knowledge" / "authority_catalog.yaml"
    cov_schema_path = contract_root / "schemas" / "evaluation" / "coverage_report.schema.json"

    if not cov_schema_path.exists():
        fail("Missing coverage_report.schema.json (expected prior commit).")

    # Snapshot input
    in_signal = Path(args.case_signal_profile).resolve()
    if not in_signal.exists():
        fail(f"case_signal_profile not found: {in_signal}")
    snapshot_signal = out_root / "case_signal_profile.json"
    copy_file(in_signal, snapshot_signal)
    ok("Snapshotted case_signal_profile.json")

    # Load YAML-ish sources
    arch_text = read_text(archetypes_path)
    auth_text = read_text(authority_path)

    # Step B: Select archetype
    archetype_id = args.selected_archetype_id.strip()
    block = extract_archetype_block(arch_text, archetype_id)
    coa_family = extract_scalar(block, "coa_family") or "unknown"
    jury_refs = extract_list(block, "jury_instruction_refs")

    if not jury_refs:
        fail(f"Selected archetype has no jury_instruction_refs: {archetype_id}")

    # Step C: Authority coverage check
    missing = [r for r in jury_refs if not authority_key_exists(auth_text, r)]
    coverage_result = {
        "run_id": run_id,
        "jurisdiction": args.jurisdiction,
        "archetype_id": archetype_id,
        "checked_refs": jury_refs,
        "missing_refs": missing,
        "status": "pass" if not missing else "fail",
        "checked_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    write_json(out_root / "authority_coverage_result.json", coverage_result)

    if missing:
        fail("Missing authority_catalog entries: " + ", ".join(missing))
    ok("Authority coverage passed")

    # Step D: Burden map build (emit JSON to avoid YAML parsing downstream)
    elements_map = {}  # element_id -> {authority_refs:set, proof_types:set}
    ordered_elements = []

    for ref in jury_refs:
        elems = extract_authority_elements(auth_text, ref)
        for e in elems:
            eid = e["element_id"]
            if eid not in elements_map:
                elements_map[eid] = {"authority_refs": set(), "proof_types": set()}
                ordered_elements.append(eid)
            elements_map[eid]["authority_refs"].update(e["authority_refs"])
            elements_map[eid]["proof_types"].update(e["proof_types"])

    burden_map = {
        "run_id": run_id,
        "jurisdiction": args.jurisdiction,
        "archetype_id": archetype_id,
        "coa_family": coa_family,
        "jury_instruction_refs": jury_refs,
        "elements": [
            {
                "element_id": eid,
                "authority_refs": sorted(elements_map[eid]["authority_refs"]),
                "proof_types": sorted(elements_map[eid]["proof_types"]),
            }
            for eid in ordered_elements
        ],
        "modules": {
            "default_modules": extract_list(block, "default_modules"),
            "conditional_modules": extract_list(block, "conditional_modules"),
        }
    }
    write_json(out_root / "burden_map.json", burden_map)
    ok("Emitted burden_map.json")

    # Step E: Coverage report stub (schema-valid; unknowns until wired)
    coverage_report = {
        "run_id": run_id,
        "created_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "archetype_id": archetype_id,
        "overall_score": 0.0,
        "elements": [
            {
                "element_id": e["element_id"],
                "coverage_level": "unknown",
                "score": 0,
                "signal_citations": [],
                "missing_information_prompts": [],
                "requested_evidence_types": e.get("proof_types", []),
                "discovery_themes": [],
                "notes": "stub: coverage analysis not yet executed"
            }
            for e in burden_map["elements"]
        ]
    }
    write_json(out_root / "coverage_report.json", coverage_report)
    ok("Emitted stub coverage_report.json")

    # Step F: Bundle manifest
    artifacts = []
    for p in [
        snapshot_signal,
        out_root / "authority_coverage_result.json",
        out_root / "burden_map.json",
        out_root / "coverage_report.json",
    ]:
        artifacts.append({"path": str(p.relative_to(out_root)).replace("\\", "/"), "sha256": sha256_file(p)})

    weak_or_missing = sum(1 for el in coverage_report["elements"] if el["coverage_level"] in ("not_covered", "covered_weak", "unknown"))

    manifest = {
        "run_id": run_id,
        "jurisdiction": args.jurisdiction,
        "mode": args.mode,
        "archetype_id": archetype_id,
        "created_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "artifacts": artifacts,
        "headline_metrics": {
            "overall_score": coverage_report["overall_score"],
            "weak_or_missing_elements_count": weak_or_missing
        }
    }
    write_json(out_root / "bundle_manifest.json", manifest)
    ok("Emitted bundle_manifest.json")

    ok(f"BUNDLE COMPLETE: {out_root}")

if __name__ == "__main__":
    main()