import hashlib
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SECTIONS_DIR = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current" / "sections"
SUMMARY_PATH = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current" / "extraction_summary.json"

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def normalize_encoding(text: str) -> str:
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
        "&nbsp;": " ",
        "&sect;": "§",
        "&amp;": "&",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text

def html_to_text(html_text: str) -> str:
    text = normalize_encoding(html_text)

    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<noscript.*?>.*?</noscript>", " ", text)

    text = re.sub(r"(?i)</?(div|p|br|li|tr|td|table|h1|h2|h3|h4|h5|h6|span|form|input|label|ul|ol)[^>]*>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)

    text = normalize_encoding(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()

def strip_site_chrome(text: str) -> str:
    bad_markers = [
        "California Legislative Information",
        "home page",
        "Bill Information",
        "California Law",
        "Publications",
        "Other Resources",
        "My Subscriptions",
        "My Favorites",
        "Advanced Search",
        "Search phrase",
        "billheaderinit_form",
        "Quick Search",
        "cross reference codes",
        "Save to My Favorites",
        "Related Documents",
        "Regulations",
    ]

    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lowered = line.lower()
        if any(marker.lower() in lowered for marker in bad_markers):
            continue

        # discard obvious JSF/form leftovers
        if re.search(r"(j_idt\d+|javax\.faces|faceletsDebug|changePlaceHolder|billheaderinit_form)", line, re.IGNORECASE):
            continue

        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    return cleaned.strip()

def extract_structured_text(raw_text: str, section_number: str) -> tuple[str, str]:
    text = strip_site_chrome(raw_text)

    title = ""

    title_patterns = [
        rf"California Code,\s*EVID\s*{re.escape(section_number)}\.\s*",
        rf"^{re.escape(section_number)}\.\s+",
    ]

    for pattern in title_patterns:
        text = re.sub(pattern, "", text, count=1, flags=re.IGNORECASE | re.MULTILINE)

    # Try to locate the actual section body by section number anchor
    body = ""

    patterns = [
        rf"(?s)\b{re.escape(section_number)}\.\s+(.*?)(?=\n\d{{1,5}}(?:\.\d+)?\.\s+|\Z)",
        rf"(?s)EVID\s+{re.escape(section_number)}\.\s+(.*?)(?=\n\d{{1,5}}(?:\.\d+)?\.\s+|\Z)",
    ]

    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 40:
                body = candidate
                break

    if not body:
        # Fallback: take everything after the title-ish header
        lines = text.splitlines()
        collected = []
        started = False

        for line in lines:
            if not started:
                if re.search(rf"\b{re.escape(section_number)}\b", line):
                    started = True
                    continue
                if re.search(rf"California Code,\s*EVID\s*{re.escape(section_number)}\.", line, re.IGNORECASE):
                    started = True
                    continue
            else:
                collected.append(line)

        if collected:
            body = "\n".join(collected).strip()

    # Final cleanup
    body = normalize_encoding(body)
    body = re.sub(r"\b(Credits|HISTORY:|Top)\b.*$", "", body, flags=re.IGNORECASE | re.DOTALL)
    body = re.sub(r"\s+", " ", body).strip()

    return title, body

def main() -> None:
    html_files = sorted(SECTIONS_DIR.glob("EVID_*.html"))

    updated = 0
    no_text = 0
    missing_json = 0
    processed = 0
    samples: list[dict[str, Any]] = []

    for html_path in html_files:
        processed += 1
        section_number = html_path.stem.replace("EVID_", "")
        json_path = SECTIONS_DIR / f"EVID_{section_number}.json"

        if not json_path.exists():
            missing_json += 1
            continue

        html_text = html_path.read_text(encoding="utf-8", errors="replace")
        text = html_to_text(html_text)
        title, body = extract_structured_text(text, section_number)

        data = json.loads(json_path.read_text(encoding="utf-8"))

        data["citation"] = f"Evid. Code § {section_number}"
        data["title"] = title
        data["text"] = body
        data["text_sha256"] = sha256_text(body) if body else ""

        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        if body:
            updated += 1
            if len(samples) < 10:
                samples.append({
                    "section_id": data.get("section_id", f"EVID_{section_number}"),
                    "section_number": section_number,
                    "text_preview": body[:250]
                })
            print(f"[UPDATED] EVID_{section_number}")
        else:
            no_text += 1
            print(f"[NO_TEXT] EVID_{section_number}")

    summary = {
        "processed_html_files": processed,
        "updated_json_files": updated,
        "no_text_count": no_text,
        "missing_json_count": missing_json,
        "sample_extractions": samples
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[CA_EVIDENCE_CODE_EXTRACT_CLEAN] updated={updated} no_text={no_text} missing_json={missing_json} summary={SUMMARY_PATH}")

if __name__ == "__main__":
    main()
