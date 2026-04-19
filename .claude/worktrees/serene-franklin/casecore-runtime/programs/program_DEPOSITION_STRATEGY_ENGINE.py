import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(r"C:\Users\sfgon\Documents\GitHub\AI Legal Service")

INPUTS = {
    "authority_binding": REPO_ROOT / "casecore-runtime" / "data" / "authority_binding" / "AUTHORITY_BINDING_DECISION.json",
    "coverage": REPO_ROOT / "casecore-runtime" / "data" / "coa" / "COA_ELEMENT_COVERAGE_MATRIX.json",
    "facts": REPO_ROOT / "casecore-runtime" / "data" / "facts" / "EVIDENCE_FACTS.json",
    "mapping": REPO_ROOT / "casecore-runtime" / "data" / "mapping" / "EVIDENCE_TO_ELEMENT_MAPPING.json",
    "discrepancies": REPO_ROOT / "casecore-runtime" / "data" / "discrepancies" / "DISCREPANCY_INVENTORY.json",
    "witness_roster": REPO_ROOT / "casecore-runtime" / "data" / "witness" / "WITNESS_ROSTER.json",
    "witness_profiles": REPO_ROOT / "casecore-runtime" / "data" / "witness" / "WITNESS_PROFILES.json",
}

OUTPUT_DIR = REPO_ROOT / "casecore-runtime" / "data" / "deposition"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUTS = {
    "workspace": OUTPUT_DIR / "DEPOSITION_BATTLEGROUND_WORKSPACE.json",
    "targets": OUTPUT_DIR / "DEPOSITION_TARGETS.json",
    "questions": OUTPUT_DIR / "DEPOSITION_QUESTION_SET.json",
    "summary": OUTPUT_DIR / "DEPOSITION_STRATEGY_SUMMARY.json",
}

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def load_json(path: Path, required: bool) -> Any:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Missing required input: {path}")
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))

def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return []

def normalize_witnesses(witness_roster: Any, witness_profiles: Any) -> list[dict[str, Any]]:
    roster = as_list(witness_roster.get("witnesses") if isinstance(witness_roster, dict) else witness_roster)
    profiles = as_list(witness_profiles.get("witnesses") if isinstance(witness_profiles, dict) else witness_profiles)

    profile_map = {
        str(item.get("witness_id")): item
        for item in profiles
        if isinstance(item, dict) and item.get("witness_id")
    }

    normalized = []
    for item in roster:
        if not isinstance(item, dict):
            continue
        witness_id = str(item.get("witness_id", "")).strip()
        if not witness_id:
            continue
        merged = dict(item)
        if witness_id in profile_map:
            merged["profile"] = profile_map[witness_id]
        normalized.append(merged)

    normalized.sort(key=lambda x: str(x.get("witness_id", "")))
    return normalized

def normalize_elements(coverage: Any) -> list[dict[str, Any]]:
    if isinstance(coverage, dict):
        for key in ["elements", "coverage", "rows"]:
            if isinstance(coverage.get(key), list):
                items = coverage[key]
                break
        else:
            items = []
    else:
        items = as_list(coverage)

    elements = []
    for item in items:
        if not isinstance(item, dict):
            continue
        element_id = str(item.get("element_id", "")).strip()
        if not element_id:
            continue
        elements.append(item)

    elements.sort(key=lambda x: str(x.get("element_id", "")))
    return elements

def normalize_facts(facts: Any) -> list[dict[str, Any]]:
    if isinstance(facts, dict):
        for key in ["facts", "items", "rows"]:
            if isinstance(facts.get(key), list):
                items = facts[key]
                break
        else:
            items = []
    else:
        items = as_list(facts)
    return [item for item in items if isinstance(item, dict)]

def normalize_mappings(mapping: Any) -> list[dict[str, Any]]:
    if isinstance(mapping, dict):
        for key in ["mappings", "items", "rows"]:
            if isinstance(mapping.get(key), list):
                items = mapping[key]
                break
        else:
            items = []
    else:
        items = as_list(mapping)
    return [item for item in items if isinstance(item, dict)]

def normalize_discrepancies(discrepancies: Any) -> list[dict[str, Any]]:
    if discrepancies is None:
        return []
    if isinstance(discrepancies, dict):
        for key in ["discrepancies", "items", "rows"]:
            if isinstance(discrepancies.get(key), list):
                return [x for x in discrepancies[key] if isinstance(x, dict)]
    return [x for x in as_list(discrepancies) if isinstance(x, dict)]

def collect_element_mappings(mappings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for item in mappings:
        element_id = str(item.get("element_id", "")).strip()
        if not element_id:
            continue
        out.setdefault(element_id, []).append(item)

    for value in out.values():
        value.sort(key=lambda x: (str(x.get("evidence_id", "")), str(x.get("fact_id", ""))))
    return out

def score_target(element: dict[str, Any], mappings: list[dict[str, Any]], discrepancies: list[dict[str, Any]]) -> int:
    coverage_status = str(element.get("coverage_status") or element.get("status") or "").lower()

    burden_weight = 3
    if "missing" in coverage_status or "weak" in coverage_status:
        burden_weight = 10
    elif "partial" in coverage_status or "medium" in coverage_status:
        burden_weight = 7

    evidence_strength = min(len(mappings), 10)
    contradiction_weight = min(len(discrepancies) * 2, 10)

    return burden_weight + evidence_strength + contradiction_weight

def build_targets(witnesses, elements, element_map, discrepancies):
    targets = []
    target_idx = 1

    for witness in witnesses:
        witness_id = str(witness.get("witness_id"))
        for element in elements:
            element_id = str(element.get("element_id"))
            mappings = element_map.get(element_id, [])

            related_discrepancies = [
                d for d in discrepancies
                if str(d.get("element_id", "")) == element_id
                or str(d.get("witness_id", "")) == witness_id
            ]

            if not mappings and not related_discrepancies:
                continue

            priority_score = score_target(element, mappings, related_discrepancies)

            targets.append({
                "target_id": f"DT{target_idx:05d}",
                "witness_id": witness_id,
                "element_id": element_id,
                "target_type": "element_pressure",
                "rationale": "Pressure this element through supporting evidence, gaps, and contradiction handling.",
                "evidence_ids": sorted({str(m.get("evidence_id", "")).strip() for m in mappings if m.get("evidence_id")}),
                "fact_ids": sorted({str(m.get("fact_id", "")).strip() for m in mappings if m.get("fact_id")}),
                "discrepancy_ids": sorted({str(d.get("discrepancy_id", "")).strip() for d in related_discrepancies if d.get("discrepancy_id")}),
                "priority_score": priority_score,
            })
            target_idx += 1

    targets.sort(key=lambda x: (-x["priority_score"], x["witness_id"], x["element_id"]))
    return targets

def build_questions(targets):
    questions = []
    q_idx = 1

    for target in targets:
        witness_id = target["witness_id"]
        element_id = target["element_id"]
        evidence_ids = target["evidence_ids"]
        fact_ids = target["fact_ids"]
        priority_score = target["priority_score"]

        templates = [
            ("lock_in", f"Please describe everything you know about {element_id}."),
            ("gap_exposure", f"What facts do you rely on to support {element_id}?"),
            ("contradiction_trap", f"Can you explain any inconsistency between your testimony and the documents tied to {element_id}?"),
            ("impeachment", f"Is there any reason the records tied to {element_id} would contradict your testimony today?"),
        ]

        local_ids = []

        for q_type, q_text in templates:
            q_id = f"DQ{q_idx:05d}"
            local_ids.append(q_id)

            questions.append({
                "question_id": q_id,
                "witness_id": witness_id,
                "element_id": element_id,
                "type": q_type,
                "question_text": q_text,
                "expected_answer": "Attorney to refine based on witness posture and record.",
                "evidence_ids": evidence_ids,
                "fact_ids": fact_ids,
                "follow_up_question_ids": [],
                "priority_score": priority_score,
            })
            q_idx += 1

        for i in range(len(local_ids) - 1):
            current_id = local_ids[i]
            next_id = local_ids[i + 1]
            for q in questions:
                if q["question_id"] == current_id:
                    q["follow_up_question_ids"] = [next_id]
                    break

    questions.sort(key=lambda x: (-x["priority_score"], x["witness_id"], x["element_id"], x["question_id"]))
    return questions

def build_workspace(witnesses, elements, targets):
    by_witness = {}
    for target in targets:
        by_witness.setdefault(target["witness_id"], []).append(target)

    witness_entries = []
    for witness in witnesses:
        witness_id = str(witness.get("witness_id"))
        witness_targets = sorted(by_witness.get(witness_id, []), key=lambda x: (-x["priority_score"], x["element_id"]))
        witness_entries.append({
            "witness_id": witness_id,
            "witness_name": witness.get("name", ""),
            "element_targets": witness_targets,
        })

    return {
        "generated_at": now_iso(),
        "witnesses": witness_entries,
        "element_count": len(elements),
        "witness_count": len(witnesses),
        "target_count": len(targets),
    }

def main():
    authority_binding = load_json(INPUTS["authority_binding"], required=True)
    coverage = load_json(INPUTS["coverage"], required=True)
    facts = load_json(INPUTS["facts"], required=True)
    mapping = load_json(INPUTS["mapping"], required=True)

    discrepancies = load_json(INPUTS["discrepancies"], required=False)
    witness_roster = load_json(INPUTS["witness_roster"], required=False)
    witness_profiles = load_json(INPUTS["witness_profiles"], required=False)

    witnesses = normalize_witnesses(witness_roster or {"witnesses": []}, witness_profiles or {"witnesses": []})
    elements = normalize_elements(coverage)
    facts_list = normalize_facts(facts)
    mappings = normalize_mappings(mapping)
    discrepancy_list = normalize_discrepancies(discrepancies)

    if not witnesses:
        witnesses = [{"witness_id": "UNASSIGNED", "name": "Unassigned Witness"}]

    element_map = collect_element_mappings(mappings)

    targets = build_targets(witnesses, elements, element_map, discrepancy_list)
    questions = build_questions(targets)
    workspace = build_workspace(witnesses, elements, targets)

    run_id = stable_hash({
        "authority_binding": authority_binding,
        "elements": elements,
        "facts": facts_list,
        "mappings": mappings,
        "discrepancies": discrepancy_list,
        "witnesses": witnesses,
    })[:16]

    workspace["run_id"] = run_id

    targets_payload = {"generated_at": now_iso(), "run_id": run_id, "targets": targets}
    questions_payload = {"generated_at": now_iso(), "run_id": run_id, "questions": questions}
    summary_payload = {
        "generated_at": now_iso(),
        "run_id": run_id,
        "witness_count": len(witnesses),
        "element_count": len(elements),
        "fact_count": len(facts_list),
        "mapping_count": len(mappings),
        "discrepancy_count": len(discrepancy_list),
        "target_count": len(targets),
        "question_count": len(questions),
        "authority_binding_present": True,
        "optional_inputs": {
            "discrepancies_present": discrepancies is not None,
            "witness_roster_present": witness_roster is not None,
            "witness_profiles_present": witness_profiles is not None,
        },
    }

    OUTPUTS["workspace"].write_text(json.dumps(workspace, indent=2, ensure_ascii=False), encoding="utf-8")
    OUTPUTS["targets"].write_text(json.dumps(targets_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    OUTPUTS["questions"].write_text(json.dumps(questions_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    OUTPUTS["summary"].write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[DEPOSITION_STRATEGY_ENGINE] run_id={run_id} targets={len(targets)} questions={len(questions)} workspace={OUTPUTS['workspace']}")

if __name__ == "__main__":
    main()

