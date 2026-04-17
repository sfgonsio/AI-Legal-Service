import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"
LAW_CODE = "EVID"

CURRENT_DIR = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current"
SECTIONS_DIR = CURRENT_DIR / "sections"
FAILURES_DIR = CURRENT_DIR / "failures"
MANIFEST_PATH = CURRENT_DIR / "section_sync_manifest_v2.json"

PACK_MANIFEST_PATH = REPO_ROOT / "authority_packs" / "ca_evidence_code" / "authority_pack_manifest.yaml"
RULESET_PATH = REPO_ROOT / "contract" / "v1" / "authority_packs" / "rulesets" / "ruleset_evid_v3.yaml"

SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
FAILURES_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; AI-Legal-Service/1.0; +official-source-sync)"
})

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_simple_yaml(path: Path) -> dict:
    data: dict = {}
    stack: list[tuple[int, object]] = [(-1, data)]

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        if line.startswith("- "):
            value = line[2:].strip().strip('"')
            if isinstance(parent, list):
                parent.append(value)
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if value == "":
                next_container: object = {}
                # peek heuristic based on known keys that hold lists
                if key in {"reject_patterns", "require_any_legal_markers", "require_legal_markers"}:
                    next_container = []

                if isinstance(parent, dict):
                    parent[key] = next_container
                    stack.append((indent, next_container))
            else:
                clean_value: object = value.strip('"')
                if clean_value.lower() == "true":
                    clean_value = True
                elif clean_value.lower() == "false":
                    clean_value = False
                else:
                    try:
                        clean_value = int(clean_value)
                    except Exception:
                        pass

                if isinstance(parent, dict):
                    parent[key] = clean_value

    return data

def normalize_text(text: str) -> str:
    fixes = {
        "Â§": "§",
        "Â": "",
        "\u00a0": " ",
        "&nbsp;": " ",
        "&lt;&lt;": "<<",
        "&gt;&gt;": ">>",
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def fetch_section_html(section_number: int) -> str:
    params = {
        "lawCode": LAW_CODE,
        "sectionNum": f"{section_number}."
    }
    response = SESSION.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.text

def strip_html(value: str) -> str:
    value = re.sub(r"(?is)<script.*?>.*?</script>", " ", value)
    value = re.sub(r"(?is)<style.*?>.*?</style>", " ", value)
    value = re.sub(r"(?is)<noscript.*?>.*?</noscript>", " ", value)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</p>|</div>|</li>|</h1>|</h2>|</h3>|</h4>|</h5>|</h6>|</tr>|</td>", "\n", value)
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    return normalize_text(value)

def apply_cleanup(text: str, ruleset: dict) -> str:
    cleanup = ruleset.get("cleanup", {})
    if cleanup.get("collapse_whitespace", True):
        text = re.sub(r"\s+", " ", text).strip()
    return text

def isolate_section_body(section_number: int, text: str, ruleset: dict) -> str:
    text = normalize_text(text)

    section_detection = ruleset.get("section_detection", {})
    start_pattern_template = section_detection.get("start_pattern_template", r"\b{section_number}\.\s")
    next_section_pattern_template = section_detection.get("next_section_pattern_template", r"\b{next_section_number}\.\s")

    start_pattern = start_pattern_template.format(section_number=section_number)
    start_match = re.search(start_pattern, text)
    if not start_match:
        return ""

    body = text[start_match.start():]

    next_section_pattern = next_section_pattern_template.format(next_section_number=section_number + 1)
    next_match = re.search(next_section_pattern, body)
    if next_match:
        body = body[:next_match.start()]

    body = apply_cleanup(body, ruleset)
    return body

def contains_reject_pattern_near_front(text: str, ruleset: dict) -> bool:
    reject_patterns = ruleset.get("reject_patterns", [])
    acceptance = ruleset.get("acceptance", {})
    front_window = acceptance.get("reject_front_window_chars", 250)

    front = text[:front_window].lower()
    for pattern in reject_patterns:
        if pattern.lower() in front:
            return True
    return False

def has_required_legal_marker(text: str, ruleset: dict) -> bool:
    acceptance = ruleset.get("acceptance", {})
    markers = acceptance.get("require_any_legal_markers", [])
    lowered = text.lower()
    for marker in markers:
        if marker.lower() in lowered:
            return True
    return False

def accept_text(section_number: int, text: str, ruleset: dict, pack_manifest: dict) -> tuple[bool, str]:
    acceptance = ruleset.get("acceptance", {})
    validation = pack_manifest.get("validation", {})

    min_length = validation.get("min_text_length", acceptance.get("min_length", 80))
    must_start = validation.get("must_start_with_section", acceptance.get("must_start_with_section", True))

    starts_ok = text.startswith(f"{section_number}.") if must_start else True
    len_ok = len(text) >= min_length
    reject_front = contains_reject_pattern_near_front(text, ruleset)
    legal_marker_ok = has_required_legal_marker(text, ruleset)

    accepted = starts_ok and len_ok and (not reject_front) and legal_marker_ok
    diagnostic = (
        f"starts_ok={starts_ok}; "
        f"len_ok={len_ok}; "
        f"reject_front={reject_front}; "
        f"legal_marker_ok={legal_marker_ok}; "
        f"len={len(text)}"
    )
    return accepted, diagnostic

def build_json_record(section_number: int, html: str, text: str, run_id: str) -> dict:
    citation = f"Evid. Code § {section_number}"
    return {
        "authority_id": "CA_EVIDENCE_CODE",
        "section_id": f"EVID_{section_number}",
        "section_number": str(section_number),
        "citation": citation,
        "title": "",
        "text": text,
        "source_url": f"{BASE_URL}?lawCode={LAW_CODE}&sectionNum={section_number}.",
        "source_label": "California Evidence Code",
        "captured_at": now_iso(),
        "html_sha256": sha256_text(html),
        "text_sha256": sha256_text(text) if text else "",
        "run_id": run_id,
        "raw_html_path": str((SECTIONS_DIR / f"EVID_{section_number}.html").resolve())
    }

def write_failure(section_number: int, html: str, reason: str, run_id: str) -> None:
    payload = {
        "authority_id": "CA_EVIDENCE_CODE",
        "section_id": f"EVID_{section_number}",
        "section_number": str(section_number),
        "run_id": run_id,
        "reason": reason,
        "captured_at": now_iso(),
        "source_url": f"{BASE_URL}?lawCode={LAW_CODE}&sectionNum={section_number}.",
        "html_sha256": sha256_text(html),
    }
    (FAILURES_DIR / f"EVID_{section_number}_failure.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def main() -> None:
    if not PACK_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing pack manifest: {PACK_MANIFEST_PATH}")
    if not RULESET_PATH.exists():
        raise FileNotFoundError(f"Missing ruleset: {RULESET_PATH}")

    pack_manifest = parse_simple_yaml(PACK_MANIFEST_PATH)
    ruleset = parse_simple_yaml(RULESET_PATH)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    section_files: list[str] = []
    failures: list[dict] = []

    for section_number in range(1, 2001):
        try:
            html = fetch_section_html(section_number)
            raw_text = strip_html(html)
            isolated_text = isolate_section_body(section_number, raw_text, ruleset)
            accepted, diagnostic = accept_text(section_number, isolated_text, ruleset, pack_manifest)

            if accepted:
                html_path = SECTIONS_DIR / f"EVID_{section_number}.html"
                json_path = SECTIONS_DIR / f"EVID_{section_number}.json"

                html_path.write_text(html, encoding="utf-8")
                record = build_json_record(section_number, html, isolated_text, run_id)
                json_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

                section_files.append(str(json_path.relative_to(REPO_ROOT)))
                print(f"[OK] EVID_{section_number} :: {diagnostic}")
            else:
                write_failure(section_number, html, diagnostic, run_id)
                failures.append({
                    "section_number": section_number,
                    "reason": diagnostic
                })
                print(f"[FAIL] EVID_{section_number} :: {diagnostic}")

            time.sleep(0.10)

        except requests.HTTPError as exc:
            failures.append({
                "section_number": section_number,
                "reason": f"http_error: {exc}"
            })
            print(f"[HTTP_FAIL] EVID_{section_number} :: {exc}")
        except Exception as exc:
            failures.append({
                "section_number": section_number,
                "reason": f"exception: {exc}"
            })
            print(f"[EXCEPTION] EVID_{section_number} :: {exc}")

    manifest = {
        "authority_id": "CA_EVIDENCE_CODE",
        "run_id": run_id,
        "captured_at": now_iso(),
        "source_label": "California Legislative Information",
        "source_scope": "official",
        "ruleset_id": ruleset.get("ruleset_id", "UNKNOWN"),
        "section_count": len(section_files),
        "failure_count": len(failures),
        "section_files": section_files[:2000],
        "failures_sample": failures[:100]
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[CA_EVIDENCE_CODE_SOURCE_ACQUISITION_V2] sections={len(section_files)} failures={len(failures)} manifest={MANIFEST_PATH}")

if __name__ == "__main__":
    main()
