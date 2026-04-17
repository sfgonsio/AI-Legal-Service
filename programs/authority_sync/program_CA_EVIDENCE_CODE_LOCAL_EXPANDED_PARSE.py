import json
import re
import hashlib
from html import unescape
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(r"C:\Users\sfgon\Documents\GitHub\AI Legal Service")
PAGE_FILE = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current" / "pages" / "evidence_code_expanded.html"
OUT_DIR = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current" / "sections_local_expanded"
MANIFEST = REPO_ROOT / "authority_store" / "ca" / "evidence_code" / "current" / "section_sync_manifest_local_expanded.json"

OUT_DIR.mkdir(parents=True, exist_ok=True)

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def clean_html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style.*?>.*?</style>", " ", raw)
    raw = re.sub(r"(?is)<noscript.*?>.*?</noscript>", " ", raw)

    raw = re.sub(r"(?i)</?(div|p|br|li|tr|td|table|h1|h2|h3|h4|h5|h6|span|ul|ol)[^>]*>", "\n", raw)
    raw = re.sub(r"(?is)<[^>]+>", " ", raw)

    raw = unescape(raw)
    raw = raw.replace("Â§", "§").replace("Â", "")
    raw = raw.replace("\r", "\n")
    raw = re.sub(r"[ \t\f\v]+", " ", raw)
    raw = re.sub(r"\n{2,}", "\n", raw)
    return raw.strip()

def strip_ui_noise(lines):
    bad_markers = [
        "skip to content",
        "quick search",
        "bill information",
        "my favorites",
        "select code",
        "keyword(s):",
        "code search",
        "text search",
        "home accessibility faq feedback sitemap login",
        "california law >> >> code section",
        "add to my favorites",
        "cross-reference chaptered bills pdf",
    ]
    kept = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        lowered = s.lower()
        if any(marker in lowered for marker in bad_markers):
            continue
        if "j_idt" in lowered or "javax.faces" in lowered or "faceletsdebug" in lowered:
            continue
        kept.append(s)
    return kept

def extract_sections(text: str):
    lines = strip_ui_noise(text.splitlines())

    joined = "\n".join(lines)
    joined = re.sub(r"\n{2,}", "\n", joined)

    # Section starts like:
    # 100.
    # 100.5.
    # 100a.
    pattern = re.compile(r"(?m)^(?P<num>\d+[A-Za-z]?(?:\.\d+)?)\.\s")

    matches = list(pattern.finditer(joined))
    sections = []

    for i, m in enumerate(matches):
        section_number = m.group("num")
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(joined)
        body = joined[start:end].strip()

        if len(body) < 80:
            continue

        lowered_front = body[:250].lower()
        if any(bad in lowered_front for bad in [
            "quick search", "bill information", "my favorites",
            "select code", "skip to content", "keyword(s):"
        ]):
            continue

        sections.append((section_number, body))

    return sections

def main():
    if not PAGE_FILE.exists():
        raise FileNotFoundError(f"Missing source page: {PAGE_FILE}")

    raw_html = PAGE_FILE.read_text(encoding="utf-8", errors="replace")
    text = clean_html_to_text(raw_html)
    sections = extract_sections(text)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    written = []

    for section_number, body in sections:
        record = {
            "authority_id": "CA_EVIDENCE_CODE",
            "section_id": f"EVID_{section_number}",
            "section_number": section_number,
            "citation": f"Evid. Code § {section_number}",
            "title": "",
            "text": body,
            "source_url": str(PAGE_FILE),
            "source_label": "California Evidence Code (local expanded page)",
            "captured_at": now_iso(),
            "html_sha256": sha256_text(raw_html),
            "text_sha256": sha256_text(body),
            "run_id": run_id,
            "raw_html_path": str(PAGE_FILE),
        }

        out_file = OUT_DIR / f"EVID_{section_number}.json"
        out_file.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(str(out_file))

    manifest = {
        "authority_id": "CA_EVIDENCE_CODE",
        "run_id": run_id,
        "captured_at": now_iso(),
        "source_scope": "local_expanded_page",
        "source_file": str(PAGE_FILE),
        "section_count": len(written),
        "section_files_sample": written[:25],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[LOCAL_EXPANDED_PARSE] sections={len(written)} manifest={MANIFEST}")

if __name__ == "__main__":
    main()
