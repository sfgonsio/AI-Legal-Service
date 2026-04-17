from pathlib import Path
from bs4 import BeautifulSoup

repo_root = Path(r"C:\Users\sfgon\Documents\GitHub\AI Legal Service")
html_path = repo_root / "authority_store" / "ca" / "evidence_code" / "current" / "sections" / "EVID_1699.html"

html = html_path.read_text(encoding="utf-8", errors="replace")
soup = BeautifulSoup(html, "html.parser")

print("=== DIVS WITH CLASS CONTAINING 'section' ===")
matches = []
for div in soup.find_all("div"):
    classes = div.get("class", [])
    if any("section" in c.lower() for c in classes):
        spans = div.find_all("span", class_="codeDisplayText")
        text = " ".join(s.get_text(" ", strip=True) for s in spans).strip()
        matches.append((classes, len(spans), text[:300]))

print(f"count={len(matches)}")
for i, (classes, span_count, preview) in enumerate(matches[:20], start=1):
    print(f"[{i}] classes={classes} span_count={span_count}")
    print(f"preview={preview}")
    print("---")

print("")
print("=== GLOBAL span.codeDisplayText ===")
all_spans = soup.find_all("span", class_="codeDisplayText")
print(f"count={len(all_spans)}")
for i, s in enumerate(all_spans[:40], start=1):
    txt = s.get_text(" ", strip=True)
    print(f"[{i}] {txt[:250]}")

print("")
print("=== H6 TAGS ===")
h6s = soup.find_all("h6")
print(f"count={len(h6s)}")
for i, h in enumerate(h6s[:20], start=1):
    print(f"[{i}] {h.get_text(' ', strip=True)}")
