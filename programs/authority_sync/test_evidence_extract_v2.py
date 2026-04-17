from pathlib import Path
from bs4 import BeautifulSoup
import hashlib

repo_root = Path(r"C:\Users\sfgon\Documents\GitHub\AI Legal Service")
html_path = repo_root / "authority_store" / "ca" / "evidence_code" / "current" / "sections" / "EVID_1699.html"

def fix_encoding(text: str) -> str:
    return (
        text.replace("Â§", "§")
            .replace("Â", "")
            .replace("\u00a0", " ")
    )

def extract_section(html: str):
    soup = BeautifulSoup(html, "html.parser")

    section_div = soup.find("div", class_="section")
    if not section_div:
        return None

    h6 = section_div.find("h6")
    section_number = h6.get_text(strip=True).replace(".", "") if h6 else None

    spans = section_div.find_all("span", class_="codeDisplayText")
    text_parts = [s.get_text(" ", strip=True) for s in spans]
    full_text = " ".join(text_parts).strip()
    full_text = fix_encoding(full_text)

    text_sha256 = hashlib.sha256(full_text.encode("utf-8")).hexdigest() if full_text else ""

    return {
        "section_number": section_number,
        "text": full_text,
        "text_sha256": text_sha256
    }

html = html_path.read_text(encoding="utf-8", errors="replace")
result = extract_section(html)

print(result)
