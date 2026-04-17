import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECTIONS_DIR = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current" / "sections"

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def clean_text(text: str) -> str:
    replacements = {
        "Â§": "§",
        "Â": "",
        "\u00a0": " ",
        "\r": "\n",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<noscript.*?>.*?</noscript>", " ", text)
    text = re.sub(r"(?i)</?(div|p|br|li|tr|td|table|h1|h2|h3|h4|h5|h6|span)[^>]*>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&sect;", "§", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t\f\v]+", " ", text)
    return text.strip()

def extract_section_text(html_text: str, section_number: str) -> str:
    text = clean_text(html_text)

    patterns = [
        rf"California Code,?\s+EVID\s+{re.escape(section_number)}\.(.*?)(?=Credits|HISTORY:|Top|$)",
        rf"^{re.escape(section_number)}\.\s+(.*?)(?=Credits|HISTORY:|Top|$)",
    ]

    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if m:
            extracted = re.sub(r"\s+", " ", m.group(1)).strip()
            if len(extracted) > 40:
                return extracted

    # fallback: take text after title marker
    title_marker = f"California Code, EVID {section_number}."
    idx = text.find(title_marker)
    if idx >= 0:
        extracted = text[idx + len(title_marker):]
        extracted = re.sub(r"\s+", " ", extracted).strip()
        if len(extracted) > 40:
            return extracted

    return ""

def main():
    html_files = sorted(SECTIONS_DIR.glob("EVID_*.html"))
    updated = 0
    skipped = 0

    for html_path in html_files:
        section_number = html_path.stem.replace("EVID_", "")
        json_path = SECTIONS_DIR / f"EVID_{section_number}.json"

        if not json_path.exists():
            skipped += 1
            continue

        html_text = html_path.read_text(encoding="utf-8", errors="replace")
        extracted_text = extract_section_text(html_text, section_number)

        data = json.loads(json_path.read_text(encoding="utf-8"))
        data["citation"] = f"Evid. Code § {section_number}"
        data["text"] = extracted_text
        data["text_sha256"] = sha256_text(extracted_text) if extracted_text else ""

        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        if extracted_text:
            updated += 1
            print(f"[UPDATED] EVID_{section_number}")
        else:
            skipped += 1
            print(f"[NO TEXT] EVID_{section_number}")

    print(f"[CA_EVIDENCE_CODE_EXTRACT_TEXT] updated={updated} skipped={skipped}")

if __name__ == "__main__":
    main()
