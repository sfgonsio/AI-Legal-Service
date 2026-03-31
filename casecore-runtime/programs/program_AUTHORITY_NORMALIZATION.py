import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contract" / "v1" / "authority_packs" / "authority_pack_registry.yaml"

CONTROLLED_ACTORS: List[Tuple[str, str]] = [
    (r"\ba licensed manufacturer\b", "licensed_manufacturer"),
    (r"\ba manufacturer\b", "manufacturer"),
    (r"\ba licensee\b", "licensee"),
    (r"\ban? applicant\b", "applicant"),
    (r"\ba person\b", "person"),
    (r"\bthe department\b", "department"),
    (r"\bthe bureau\b", "bureau"),
    (r"\ba distributor\b", "distributor"),
    (r"\ba retailer\b", "retailer"),
    (r"\ba cultivator\b", "cultivator"),
    (r"\ba licensed testing laboratory\b", "licensed_testing_laboratory"),
    (r"\ba testing laboratory\b", "testing_laboratory"),
    (r"\bthe governor\b", "governor"),
    (r"\bthe director\b", "director"),
    (r"\ba cannabis event organizer\b", "cannabis_event_organizer"),
    (r"\bthe legislature\b", "legislature"),
    (r"\bthis division\b", "statute"),
]

OBLIGATION_PATTERN = re.compile(r"\b(shall|must|required to|is required to)\b", re.IGNORECASE)
PROHIBITION_PATTERN = re.compile(r"\b(shall not|may not|unlawful|prohibited)\b", re.IGNORECASE)
CONDITION_PATTERN = re.compile(r"\b(if|unless|except|provided that|subject to)\b", re.IGNORECASE)
SUBSECTION_TOKEN_PATTERN = re.compile(r"(\([a-zA-Z0-9]+\))")

DEFINITION_PATTERNS = [
    re.compile(r'["“](.+?)["”]\s+means\s+(.*)', re.IGNORECASE),
    re.compile(r'["“](.+?)["”]\s+has the same meaning as\s+(.*)', re.IGNORECASE),
    re.compile(r'^([A-Z][A-Za-z0-9\-\s]{1,80}?)\s+means\s+(.*)', re.IGNORECASE),
    re.compile(r'^([A-Z][A-Za-z0-9\-\s]{1,80}?)\s+has the same meaning as\s+(.*)', re.IGNORECASE),
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    replacements = {
        "Â§": "§",
        "Â": "",
        "â€œ": '"',
        "â€\u009d": '"',
        "â€": '"',
        "â€˜": "'",
        "â€™": "'",
        "â€“": "-",
        "â€”": "-",
        "\u00a0": " ",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def strip_trailing_history(text: str) -> str:
    history_markers = [
        " (Amended by Stats.",
        " (Added by Stats.",
        " BPC Business and Professions Code - BPC",
    ]
    for marker in history_markers:
        idx = text.find(marker)
        if idx >= 0:
            return text[:idx].strip()
    return text

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

def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    return [s.strip() for s in re.split(r'(?<=[.;])\s+', text) if s.strip()]

def split_subsections(text: str) -> List[Dict[str, str]]:
    cleaned = clean_text(text)
    matches = list(SUBSECTION_TOKEN_PATTERN.finditer(cleaned))
    if not matches:
        return []

    subsections: List[Dict[str, str]] = []
    for idx, match in enumerate(matches):
        label = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(cleaned)
        body = cleaned[start:end].strip(" ;")
        if body:
            subsections.append({"label": label, "text": body})
    return subsections

def normalize_term(term: str) -> str:
    term = clean_text(term)
    return term.strip(' "\'')

def infer_actor(text: str) -> str:
    lowered = clean_text(text).lower()
    for pattern, actor in CONTROLLED_ACTORS:
        if re.search(pattern, lowered):
            return actor
    return "unspecified_actor"

def looks_like_definition_section(section_text: str) -> bool:
    lowered = clean_text(section_text).lower()
    return (
        "the following definitions apply" in lowered
        or "for purposes of this division" in lowered
        or "means" in lowered
    )

def extract_definitions_from_subsections(subsections: List[Dict[str, str]], section_id: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    seen = set()

    for subsection in subsections:
        body = strip_trailing_history(clean_text(subsection["text"]))
        for pattern in DEFINITION_PATTERNS:
            match = pattern.search(body)
            if not match:
                continue

            term = normalize_term(match.group(1))
            definition = strip_trailing_history(clean_text(match.group(2)))
            if not term or not definition:
                continue

            key = (term.lower(), definition[:140].lower())
            if key in seen:
                continue
            seen.add(key)

            results.append({
                "term": term,
                "definition": definition,
                "definition_type": "explicit_subsection",
                "subsection_label": subsection["label"],
                "source_section": section_id
            })
            break

    return results

def extract_definitions_from_text(text: str, section_id: str) -> List[Dict[str, Any]]:
    cleaned = strip_trailing_history(clean_text(text))
    results: List[Dict[str, Any]] = []
    seen = set()

    for pattern in DEFINITION_PATTERNS:
        for match in pattern.finditer(cleaned):
            term = normalize_term(match.group(1))
            definition = strip_trailing_history(clean_text(match.group(2)))
            if not term or not definition:
                continue

            key = (term.lower(), definition[:140].lower())
            if key in seen:
                continue
            seen.add(key)

            results.append({
                "term": term,
                "definition": definition,
                "definition_type": "explicit_text",
                "source_section": section_id
            })

    return results

def extract_definitions(text: str, section_id: str, subsections: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if looks_like_definition_section(text):
        results.extend(extract_definitions_from_subsections(subsections, section_id))
    if not results:
        results.extend(extract_definitions_from_text(text, section_id))
    return results

def classify_burden(rule_type: str):
    if rule_type == "obligation":
        return ("defendant", "defense-compliance", "duty")
    if rule_type == "prohibition":
        return ("plaintiff", "prima-facie", "violation")
    return ("shifting", "exception-or-condition", "condition")

def build_element_id(section_id: str, rule_type: str, index: int) -> str:
    return f"{section_id}__{rule_type.upper()}__{index:03d}"

def build_rule_record(section_id: str, rule_type: str, text: str, index: int, subsection_label: str = ""):
    burden_type, burden_stage, element_role = classify_burden(rule_type)
    record = {
        "element_id": build_element_id(section_id, rule_type, index),
        "actor": infer_actor(text),
        "rule_type": rule_type,
        "element_role": element_role,
        "text": clean_text(text),
        "source_section": section_id,
        "burden_type": burden_type,
        "burden_stage": burden_stage,
        "proof_requirements": []
    }
    if subsection_label:
        record["subsection_label"] = subsection_label
    return record

def extract_rules_from_subsections(subsections: List[Dict[str, str]], section_id: str):
    obligation_texts = []
    prohibition_texts = []
    condition_texts = []

    for subsection in subsections:
        label = subsection["label"]
        text = clean_text(strip_trailing_history(subsection["text"]))
        if not text:
            continue

        if PROHIBITION_PATTERN.search(text):
            prohibition_texts.append((text, label))
        elif OBLIGATION_PATTERN.search(text):
            obligation_texts.append((text, label))
        elif CONDITION_PATTERN.search(text):
            condition_texts.append((text, label))

    obligations = [build_rule_record(section_id, "obligation", t, i + 1, lbl) for i, (t, lbl) in enumerate(obligation_texts)]
    prohibitions = [build_rule_record(section_id, "prohibition", t, i + 1, lbl) for i, (t, lbl) in enumerate(prohibition_texts)]
    conditions = [build_rule_record(section_id, "condition", t, i + 1, lbl) for i, (t, lbl) in enumerate(condition_texts)]
    return obligations, prohibitions, conditions

def extract_rules_from_sentences(sentences: List[str], section_id: str):
    obligations = []
    prohibitions = []
    conditions = []

    for sentence in sentences:
        sentence = clean_text(strip_trailing_history(sentence))
        if not sentence:
            continue
        if PROHIBITION_PATTERN.search(sentence):
            prohibitions.append(sentence)
        elif OBLIGATION_PATTERN.search(sentence):
            obligations.append(sentence)
        elif CONDITION_PATTERN.search(sentence):
            conditions.append(sentence)

    obligation_records = [build_rule_record(section_id, "obligation", t, i + 1) for i, t in enumerate(obligations)]
    prohibition_records = [build_rule_record(section_id, "prohibition", t, i + 1) for i, t in enumerate(prohibitions)]
    condition_records = [build_rule_record(section_id, "condition", t, i + 1) for i, t in enumerate(conditions)]
    return obligation_records, prohibition_records, condition_records

def build_burden_map(section_id: str, obligations, prohibitions, conditions):
    burden_map = []
    for item in obligations + prohibitions + conditions:
        burden_map.append({
            "element_id": item["element_id"],
            "actor": item["actor"],
            "rule_type": item["rule_type"],
            "element_role": item["element_role"],
            "burden_type": item["burden_type"],
            "burden_stage": item["burden_stage"],
            "source_section": section_id,
            "proof_requirements": item.get("proof_requirements", []),
        })
    return burden_map

def normalize_pack(pack_manifest_path: Path, registry_pack: Dict[str, str]) -> Dict[str, Any]:
    manifest = parse_manifest(pack_manifest_path)

    authority_id = registry_pack.get("authority_id", "").strip() or manifest.get("authority_id", "").strip()
    inputs = manifest.get("inputs", {})
    outputs = manifest.get("outputs", {})

    sections_path = REPO_ROOT / inputs["sections_path"]
    output_path = REPO_ROOT / outputs["normalized_path"]

    if not sections_path.exists():
        raise FileNotFoundError(f"Missing sections path for {authority_id}: {sections_path}")

    files = sorted(sections_path.glob("*.json"))
    if not files:
        raise RuntimeError(f"No section files found for {authority_id}: {sections_path}")

    results: List[Dict[str, Any]] = []
    skipped: List[Dict[str, str]] = []

    for file_path in files:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:
            skipped.append({"file": str(file_path), "reason": f"json_read_error: {exc}"})
            continue

        section_id = data.get("section_id")
        if not section_id:
            skipped.append({"file": str(file_path), "reason": "missing_section_id"})
            continue

        text = strip_trailing_history(clean_text(data.get("text", "")))
        if not text:
            skipped.append({"file": str(file_path), "reason": "empty_text"})
            continue

        subsections = split_subsections(text)
        defined_terms = extract_definitions(text, section_id, subsections)

        if subsections:
            obligations, prohibitions, conditions = extract_rules_from_subsections(subsections, section_id)
        else:
            sentences = split_sentences(text)
            obligations, prohibitions, conditions = extract_rules_from_sentences(sentences, section_id)

        elements = obligations + prohibitions + conditions
        burden_map = build_burden_map(section_id, obligations, prohibitions, conditions)

        results.append({
            "authority_id": data.get("authority_id", authority_id),
            "section_id": section_id,
            "section_number": data.get("section_number", ""),
            "citation": clean_text(data.get("citation", "")),
            "title": clean_text(data.get("title", "")),
            "text": text,
            "subsections": subsections,
            "defined_terms": defined_terms,
            "obligations": obligations,
            "prohibitions": prohibitions,
            "conditions": conditions,
            "elements": elements,
            "burden_map": burden_map
        })

    payload = {
        "normalization_scope": authority_id,
        "generated_from": str(sections_path),
        "section_count": len(results),
        "skipped_count": len(skipped),
        "skipped": skipped,
        "sections": results
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "authority_id": authority_id,
        "pack_manifest": str(pack_manifest_path),
        "sections_path": str(sections_path),
        "output_path": str(output_path),
        "section_count": len(results),
        "skipped_count": len(skipped),
    }

def main():
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Missing authority pack registry: {REGISTRY_PATH}")

    registry = parse_registry(REGISTRY_PATH)
    enabled_packs = [p for p in registry if p.get("enabled", "").lower() == "true"]

    if not enabled_packs:
        raise RuntimeError("No enabled authority packs found.")

    summaries = []
    for pack in enabled_packs:
        manifest_rel = pack["manifest_path"]
        manifest_path = (REPO_ROOT / manifest_rel).resolve()
        summary = normalize_pack(manifest_path, pack)
        summaries.append(summary)
        print(
            f"[AUTHORITY_NORMALIZATION] {summary['authority_id']} "
            f"sections={summary['section_count']} skipped={summary['skipped_count']} "
            f"output={summary['output_path']}"
        )

    consolidated_path = REPO_ROOT / "casecore-runtime" / "data" / "law_normalized" / "AUTHORITY_NORMALIZATION_SUMMARY.json"
    consolidated_path.parent.mkdir(parents=True, exist_ok=True)
    consolidated_path.write_text(json.dumps({"packs": summaries}, indent=2), encoding="utf-8")

    print(f"[AUTHORITY_NORMALIZATION] complete packs={len(summaries)} summary={consolidated_path}")

if __name__ == "__main__":
    main()

