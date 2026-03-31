import json
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contract" / "v1" / "authority_packs" / "authority_pack_registry.yaml"

def parse_registry(path: Path) -> List[Dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    packs: List[Dict[str, str]] = []
    current: Dict[str, str] = {}

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "authority_packs:":
            continue

        if stripped.startswith("- "):
            if current:
                packs.append(current)
            current = {}
            remainder = stripped[2:]
            if ":" in remainder:
                key, value = remainder.split(":", 1)
                current[key.strip()] = value.strip()
        else:
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                current[key.strip()] = value.strip()

    if current:
        packs.append(current)

    return packs

def parse_manifest(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    current_section: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        if indent == 0:
            if value == "":
                data[key] = {}
                current_section = key
            else:
                data[key] = value
                current_section = None
        else:
            if current_section is not None:
                if not isinstance(data.get(current_section), dict):
                    data[current_section] = {}
                data[current_section][key] = value

    return data

def main():
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Missing authority pack registry: {REGISTRY_PATH}")

    registry = parse_registry(REGISTRY_PATH)
    enabled_packs = [p for p in registry if p.get("enabled", "").lower() == "true"]
    if not enabled_packs:
        raise RuntimeError("No enabled authority packs found.")

    for pack in enabled_packs:
        manifest_path = (REPO_ROOT / pack["manifest_path"]).resolve()
        manifest = parse_manifest(manifest_path)

        authority_id = pack.get("authority_id", "").strip() or manifest.get("authority_id", "").strip()
        outputs = manifest.get("outputs", {})
        artifact_policy = manifest.get("artifact_policy", {})
        impact_path = REPO_ROOT / outputs["impact_path"]

        impact_payload = {
            "authority_id": authority_id,
            "impact_mode": "forward_only_supersession",
            "staleness_policy": {
                "legacy_label": artifact_policy.get("legacy_status_label", "LEGACY"),
                "authority_change_status": artifact_policy.get("stale_status_on_authority_change", "SUPERSEDED_BY_AUTHORITY")
            },
            "impacted_artifact_classes": [
                "deposition_workspace",
                "burden_map",
                "element_coverage",
                "evidence_to_element_mapping",
                "trial_theme_workspace"
            ],
            "rerun_guidance": [
                "preserve historical artifacts",
                "mark impacted artifacts as superseded or stale",
                "rerun from authority binding layer forward",
                "do not rewrite prior artifacts"
            ]
        }

        impact_path.parent.mkdir(parents=True, exist_ok=True)
        impact_path.write_text(json.dumps(impact_payload, indent=2), encoding="utf-8")

        print(f"[AUTHORITY_IMPACT_ANALYSIS] {authority_id} output={impact_path}")

if __name__ == "__main__":
    main()

