import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]

INPUT_CANDIDATES = [
    REPO_ROOT / "casecore-runtime" / "data" / "authority_store",
    REPO_ROOT / "authority_store",
    REPO_ROOT / "data" / "authority_store",
    REPO_ROOT / "casecore-runtime" / "authority_store",
]

OUTPUT_DIR = REPO_ROOT / "casecore-runtime" / "data" / "law_normalized"
OUTPUT_FILE = OUTPUT_DIR / "LAW_NORMALIZED.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFINITION_PATTERNS = [
    re.compile(r'“([^”]+)”\s+(means|refers to|is defined as)\s+(.*?)(?=(?:\.\s|;|$))', re.IGNORECASE | re.DOTALL),
    re.compile(r'"([^"]+)"\s+(means|refers to|is defined as)\s+(.*?)(?=(?:\.\s|;|$))', re.IGNORECASE | re.DOTALL),
]

OBLIGATION_PATTERN = re.compile(r'\b(shall|must|required to|is required to)\b', re.IGNORECASE)
PROHIBITION_PATTERN = re.compile(r'\b(shall not|may not|is unlawful to|unlawful to)\b', re.IGNORECASE)
CONDITION_PATTERN = re.compile(r'\b(if|unless|except|provided that)\b', re.IGNORECASE)

def resolve_input_dir() -> Path:
    for candidate in INPUT_CANDIDATES:
        if candidate.exists() and candidate.is_dir():
            json_files = list(candidate.glob("*.json"))
            if json_files:
                print(f"[LAW_NORMALIZATION] Using authority input directory: {candidate}")
                return candidate

    # fallback: search repo for authority_store dirs containing json
    matches: List[Path] = []
    for path in REPO_ROOT.rglob("authority_store"):
        if path.is_dir() and list(path.glob("*.json")):
            matches.append(path)

    if len(matches) == 1:
        print(f"[LAW_NORMALIZATION] Using discovered authority input directory: {matches[0]}")
        return matches[0]

    if len(matches) > 1:
        message = "\n".join(str(p) for p in matches)
        raise FileNotFoundError(
            "Multiple authority_store directories with JSON files found. "
            "Narrow the binding explicitly. Candidates:\n" + message
        )

    searched = "\n".join(str(p) for p in INPUT_CANDIDATES)
    raise FileNotFoundError(
        "No authority_store directory with JSON files found.\n"
        f"Searched common locations:\n{searched}\n"
        "And recursive repo search found none."
    )

def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    normalized = re.sub(r'\s+', ' ', text).strip()
    parts = re.split(r'(?<=[.;])\s+(?=(?:\(|[A-Z0-9"]))', normalized)
    return [p.strip() for p in parts if p.strip()]

def split_subsections(text: str) -> List[Dict[str, str]]:
    if not text:
        return []
    matches = list(re.finditer(r'(\([a-zA-Z0-9]+\))', text))
    if not matches:
        return []

    subsections: List[Dict[str, str]] = []
    for idx, match in enumerate(matches):
        label = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip(" ;\n\t")
        subsections.append({
            "label": label,
            "text": body
        })
    return subsections

def infer_actor(sentence: str) -> str:
    lowered = sentence.lower()

    actor_patterns = [
        (r'\ba licensee\b', 'licensee'),
        (r'\ban applicant\b', 'applicant'),
        (r'\ba person\b', 'person'),
        (r'\bthe bureau\b', 'bureau'),
        (r'\bthe department\b', 'department'),
        (r'\ba retailer\b', 'retailer'),
        (r'\ba distributor\b', 'distributor'),
        (r'\ba cultivator\b', 'cultivator'),
        (r'\ba manufacturer\b', 'manufacturer'),
        (r'\ba testing laboratory\b', 'testing_laboratory'),
    ]

    for pattern, actor in actor_patterns:
        if re.search(pattern, lowered):
            return actor

    first_words = sentence.split()[:8]
    return " ".join(first_words).strip() if first_words else "unknown"

def extract_definitions(text: str, section_id: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for pattern in DEFINITION_PATTERNS:
        for match in pattern.finditer(text):
            term = match.group(1).strip()
            trigger = match.group(2).strip()
            definition = match.group(3).strip(" .;")
            results.append({
                "term": term,
                "definition": definition,
                "scope": "section",
                "trigger_text": trigger,
                "source_section": section_id
            })
    return results

def extract_obligations(sentences: List[str], section_id: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for sentence in sentences:
        if PROHIBITION_PATTERN.search(sentence):
            continue
        if OBLIGATION_PATTERN.search(sentence):
            results.append({
                "actor": infer_actor(sentence),
                "action": sentence,
                "conditions": [],
                "trigger_text": sentence,
                "source_section": section_id
            })
    return results

def extract_prohibitions(sentences: List[str], section_id: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for sentence in sentences:
        if PROHIBITION_PATTERN.search(sentence):
            results.append({
                "actor": infer_actor(sentence),
                "action": sentence,
                "exceptions": [],
                "trigger_text": sentence,
                "source_section": section_id
            })
    return results

def extract_conditions(sentences: List[str], section_id: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for sentence in sentences:
        if CONDITION_PATTERN.search(sentence):
            results.append({
                "trigger": sentence,
                "result": "",
                "dependencies": [],
                "trigger_text": sentence,
                "source_section": section_id
            })
    return results

def build_burden_map(
    section_id: str,
    obligations: List[Dict[str, Any]],
    prohibitions: List[Dict[str, Any]],
    conditions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for item in obligations:
        results.append({
            "element": item["action"],
            "burden_type": "defendant",
            "proof_requirements": [],
            "failure_effect": "non-compliance",
            "rule_class": "obligation",
            "source_section": section_id
        })

    for item in prohibitions:
        results.append({
            "element": item["action"],
            "burden_type": "plaintiff",
            "proof_requirements": [],
            "failure_effect": "violation",
            "rule_class": "prohibition",
            "source_section": section_id
        })

    for item in conditions:
        results.append({
            "element": item["trigger"],
            "burden_type": "shifting",
            "proof_requirements": [],
            "failure_effect": "conditional failure",
            "rule_class": "condition",
            "source_section": section_id
        })

    return results

def normalize_section(section: Dict[str, Any]) -> Dict[str, Any]:
    section_id = section.get("section_id")
    if not section_id:
        raise ValueError("Section missing section_id")

    text = (section.get("text") or "").strip()
    title = section.get("title") or ""

    sentences = split_sentences(text)
    subsections = split_subsections(text)
    definitions = extract_definitions(text, section_id)
    obligations = extract_obligations(sentences, section_id)
    prohibitions = extract_prohibitions(sentences, section_id)
    conditions = extract_conditions(sentences, section_id)
    burden_map = build_burden_map(section_id, obligations, prohibitions, conditions)

    return {
        "section_id": section_id,
        "title": title,
        "text": text,
        "subsections": subsections,
        "defined_terms": definitions,
        "obligations": obligations,
        "prohibitions": prohibitions,
        "conditions": conditions,
        "burden_map": burden_map
    }

def iter_sections(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if isinstance(payload, dict):
        if isinstance(payload.get("sections"), list):
            return [x for x in payload["sections"] if isinstance(x, dict)]
        return [payload]

    return []

def main() -> None:
    input_dir = resolve_input_dir()

    results: List[Dict[str, Any]] = []
    processed_files = 0
    processed_sections = 0

    for file_path in sorted(input_dir.glob("*.json")):
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        sections = iter_sections(payload)
        processed_files += 1

        for section in sections:
            if not section.get("text"):
                continue

            normalized = normalize_section(section)
            results.append(normalized)
            processed_sections += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(
        f"LAW_NORMALIZATION complete. "
        f"files={processed_files} sections={processed_sections} output={OUTPUT_FILE}"
    )

if __name__ == "__main__":
    main()
