import re
from pathlib import Path

INDEX = Path("docs/index.html")

ARCH_BLOCK = """
<section id="architecture-visuals">
  <h2>Architecture Visuals</h2>

  <h3>Section 7 — Authoritative Architecture Map</h3>
  <div style="margin: 12px 0 28px 0;">
    <img
      src="assets/svg/section7-authoritative.svg"
      alt="Section 7 Authoritative Architecture Map"
      style="max-width:100%;height:auto;border:1px solid #ddd;border-radius:8px;"
    />
  </div>

  <h3>3 Layers — Figma Simplified Map</h3>
  <div style="margin: 12px 0 28px 0;">
    <img
      src="assets/svg/layer3-figma.svg"
      alt="3 Layers Figma Simplified Map"
      style="max-width:100%;height:auto;border:1px solid #ddd;border-radius:8px;"
    />
  </div>

  <h3>Bridge Map — Section 7 ↔ 3 Layers Mapping</h3>
  <div style="margin: 12px 0 40px 0;">
    <img
      src="assets/svg/bridge-mapping.svg"
      alt="Bridge Map Between Authoritative and Simplified Architecture"
      style="max-width:100%;height:auto;border:1px solid #ddd;border-radius:8px;"
    />
  </div>

  <hr/>
</section>
""".strip() + "\n"

TOC_LI = '<li><a href="#architecture-visuals">Architecture Visuals</a></li>\n'

def main():
    if not INDEX.exists():
        raise SystemExit("docs/index.html not found")

    html = INDEX.read_text(encoding="utf-8", errors="strict")

    # 1) Remove ALL existing architecture-visuals blocks (in case there are duplicates / misplaced).
    html_new = re.sub(
        r'\s*<section\s+id="architecture-visuals">.*?</section>\s*',
        "\n",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # 2) Ensure TOC contains a link (insert as last item in TOC list).
    if TOC_LI.strip() not in html_new:
        m = re.search(
            r'(<div\s+class="toc">.*?<ul>)(.*?)(</ul>)',
            html_new,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if m:
            prefix, items, suffix = m.group(1), m.group(2), m.group(3)
            # Avoid duplicates if a variant exists
            if 'href="#architecture-visuals"' not in items:
                items = items.rstrip() + "\n" + TOC_LI
            html_new = html_new[:m.start()] + prefix + items + suffix + html_new[m.end():]
        else:
            print("WARNING: TOC block not found; skipping TOC insertion.")

    # 3) Insert Architecture Visuals BEFORE the End-of-document marker.
    marker = '<p class="small">End of document.</p>'
    if marker not in html_new:
        raise SystemExit("Could not find End of document marker; aborting to avoid corruption.")

    html_new = html_new.replace(marker, ARCH_BLOCK + marker, 1)

    INDEX.write_text(html_new, encoding="utf-8", errors="strict")
    print("OK: normalized Architecture Visuals (removed old, inserted one canonical block).")

if __name__ == "__main__":
    main()