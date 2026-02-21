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
"""

def main():
    if not INDEX.exists():
        raise SystemExit("docs/index.html not found")

    html = INDEX.read_text(encoding="utf-8")

    # Prevent duplicate insertion
    if 'id="architecture-visuals"' in html:
        print("Architecture Visuals section already exists. Aborting.")
        return

    marker = '<p class="small">End of document.</p>'

    if marker not in html:
        raise SystemExit("Could not find End of document marker")

    html = html.replace(marker, ARCH_BLOCK + "\n" + marker)

    INDEX.write_text(html, encoding="utf-8")

    print("Architecture Visuals inserted safely.")

if __name__ == "__main__":
    main()