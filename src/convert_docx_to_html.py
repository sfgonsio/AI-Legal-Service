#!/usr/bin/env python3
"""
convert_docx_to_html.py

Converts a .docx specification into clean HTML + CSS for publishing (GitHub Pages / website).
- Uses python-docx (no pandoc).
- Preserves headings (H1..H6), paragraphs, bullet/number lists, and tables.
- Adds stable anchor IDs for headings for easy linking.
- Strips common Word residue (divider lines, repeated underscores, empty paragraphs).
"""

import argparse
import html
import os
import re
import unicodedata
from typing import List, Tuple, Optional

from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P


# -----------------------------
# Helpers
# -----------------------------

DIVIDER_RE = re.compile(r"^\s*[_\-–—]{5,}\s*$")
WHITESPACE_RE = re.compile(r"\s+")
BULLET_GLYPHS = {"•", "‣", "∙", "◦", "▪", "–", "—", "●", "○"}

def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("\u00A0", " ")
    s = WHITESPACE_RE.sub(" ", s).strip()
    return s

def is_divider_line(s: str) -> bool:
    return bool(DIVIDER_RE.match(norm_text(s)))

def slugify(text: str, used: set) -> str:
    """
    Create stable-ish anchor IDs for headings.
    """
    t = norm_text(text).lower()
    t = re.sub(r"[^\w\s\-\.]", "", t)
    t = t.replace(".", "-")
    t = WHITESPACE_RE.sub("-", t).strip("-")
    if not t:
        t = "section"
    base = t
    i = 2
    while t in used:
        t = f"{base}-{i}"
        i += 1
    used.add(t)
    return t

def iter_block_items(parent):
    """
    Yield Paragraph and Table objects in document order.
    """
    parent_elm = parent.element.body
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def get_heading_level(p: Paragraph) -> Optional[int]:
    """
    Return 1..9 heading level if paragraph style is Heading N; else None.
    """
    style_name = (p.style.name or "").strip() if p.style else ""
    m = re.match(r"^Heading\s+(\d+)$", style_name, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

def paragraph_is_list_item(p: Paragraph) -> bool:
    """
    Detect if paragraph is a list item (bulleted or numbered) by checking numbering properties.
    python-docx doesn't expose list types well, but numbering properties exist in XML.
    """
    pPr = p._p.pPr
    if pPr is None:
        return False
    numPr = pPr.numPr
    return numPr is not None

def guess_list_kind(p: Paragraph) -> str:
    """
    Best-effort list kind detection: 'ul' or 'ol'.
    If text starts with bullet glyph, treat as ul.
    If text starts with like '1.' '1)' treat as ol.
    Otherwise default ul.
    """
    txt = norm_text(p.text)
    if not txt:
        return "ul"
    first = txt[0]
    if first in BULLET_GLYPHS:
        return "ul"
    if re.match(r"^\(?\d+[\.\)]\s+", txt):
        return "ol"
    # Many Word numbered lists lose explicit '1.' text because numbering is separate.
    # We conservatively default to ul unless text strongly indicates ol.
    return "ul"

def escape(s: str) -> str:
    return html.escape(s, quote=False)

def build_default_css() -> str:
    return """\
:root{
  --bg:#0b0f14;
  --fg:#e8eef6;
  --muted:#a7b2c1;
  --card:#111826;
  --border:#1e2a3a;
  --accent:#6aa6ff;
  --accent2:#7cf7c7;
  --code:#0f1724;
}

*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Apple Color Emoji","Segoe UI Emoji";
  background:var(--bg);
  color:var(--fg);
  line-height:1.45;
}
a{color:var(--accent); text-decoration:none}
a:hover{text-decoration:underline}
.container{
  max-width: 1100px;
  margin: 0 auto;
  padding: 28px 18px 60px;
}
.header{
  padding:18px 18px;
  border:1px solid var(--border);
  background:linear-gradient(180deg, rgba(106,166,255,0.08), rgba(17,24,38,0.35));
  border-radius:16px;
  margin-bottom:18px;
}
.header h1{margin:0 0 6px; font-size:28px; letter-spacing:0.2px}
.header .meta{color:var(--muted); font-size:13px}
.toc{
  border:1px solid var(--border);
  background:var(--card);
  border-radius:16px;
  padding:14px 16px;
  margin: 0 0 18px;
}
.toc h2{margin:0 0 10px; font-size:16px}
.toc ul{margin:0; padding-left:18px}
.toc li{margin:4px 0; color:var(--muted)}
hr{
  border:0;
  border-top:1px solid var(--border);
  margin:18px 0;
}
section{
  border:1px solid var(--border);
  background:rgba(17,24,38,0.55);
  border-radius:16px;
  padding:16px 16px 10px;
  margin: 0 0 14px;
}
h1,h2,h3,h4,h5,h6{
  margin: 14px 0 10px;
  line-height:1.2;
}
h2{font-size:22px}
h3{font-size:18px; color:var(--accent2)}
h4{font-size:16px}
h5{font-size:14px; color:var(--muted)}
p{margin: 8px 0}
ul,ol{margin: 8px 0 10px 20px}
li{margin: 4px 0}
blockquote{
  margin:10px 0;
  padding: 10px 12px;
  border-left: 3px solid var(--accent);
  background: rgba(106,166,255,0.08);
  border-radius: 10px;
}
table{
  width:100%;
  border-collapse: collapse;
  margin: 10px 0 12px;
  overflow:hidden;
  border-radius: 12px;
  border: 1px solid var(--border);
}
th,td{
  padding: 10px 10px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
th{
  text-align:left;
  background: rgba(255,255,255,0.04);
  color: var(--fg);
  font-weight: 600;
}
tr:last-child td{border-bottom:0}
.code{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  background: var(--code);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 12px;
  overflow:auto;
  margin: 10px 0;
  color: #d7e3f5;
}
.small{font-size:13px; color:var(--muted)}
"""

# -----------------------------
# Conversion
# -----------------------------

def build_toc(headings: List[Tuple[int, str, str]]) -> str:
    """
    headings: list of (level, text, id)
    We keep TOC to H2/H3 by default.
    """
    out = []
    out.append('<div class="toc">')
    out.append('<h2>Table of Contents</h2>')
    out.append("<ul>")
    for lvl, text, hid in headings:
        if lvl in (2, 3):
            indent = ""  # keep flat-ish for readability
            out.append(f'{indent}<li><a href="#{hid}">{escape(text)}</a></li>')
    out.append("</ul></div>")
    return "\n".join(out)

def convert_docx_to_html(docx_path: str) -> Tuple[str, str]:
    doc = Document(docx_path)

    used_ids = set()
    headings_for_toc: List[Tuple[int, str, str]] = []

    body_parts: List[str] = []
    open_section = False

    def open_new_section():
        nonlocal open_section
        if open_section:
            body_parts.append("</section>")
        body_parts.append("<section>")
        open_section = True

    # list state
    in_list = False
    list_kind = None  # 'ul' or 'ol'

    def close_list():
        nonlocal in_list, list_kind
        if in_list:
            body_parts.append(f"</{list_kind}>")
            in_list = False
            list_kind = None

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            raw = block.text or ""
            txt = norm_text(raw)

            # skip empty lines
            if not txt:
                close_list()
                continue

            # skip divider lines
            if is_divider_line(txt):
                close_list()
                body_parts.append("<hr/>")
                continue

            hlevel = get_heading_level(block)
            if hlevel is not None:
                close_list()

                # Start a new visual section on H2 (major section)
                if hlevel == 2:
                    open_new_section()

                safe_level = min(max(hlevel, 1), 6)
                hid = slugify(txt, used_ids)
                headings_for_toc.append((safe_level, txt, hid))
                body_parts.append(f'<h{safe_level} id="{hid}">{escape(txt)}</h{safe_level}>')
                continue

            # list handling
            if paragraph_is_list_item(block):
                kind = guess_list_kind(block)

                # normalize list marker residue like "• • thing"
                # we'll remove leading bullet glyphs that got duplicated in text
                cleaned = txt
                cleaned = re.sub(r"^([•\-\–—]\s*){2,}", "", cleaned).strip()
                cleaned = re.sub(r"^[•\-\–—]\s*", "", cleaned).strip()

                if not in_list:
                    # open list
                    in_list = True
                    list_kind = kind
                    body_parts.append(f"<{list_kind}>")
                else:
                    # if kind changes, close and reopen
                    if kind != list_kind:
                        close_list()
                        in_list = True
                        list_kind = kind
                        body_parts.append(f"<{list_kind}>")

                body_parts.append(f"<li>{escape(cleaned)}</li>")
                continue

            # normal paragraph
            close_list()

            # If a paragraph looks like "Label: content" with short label, style it slightly
            if re.match(r"^[A-Z][A-Za-z0-9 /&\-_]{1,40}:\s+", txt):
                body_parts.append(f"<p><strong>{escape(txt.split(':',1)[0])}:</strong> {escape(txt.split(':',1)[1].strip())}</p>")
            else:
                body_parts.append(f"<p>{escape(txt)}</p>")

        elif isinstance(block, Table):
            close_list()
            # Convert table
            rows = block.rows
            if not rows:
                continue

            body_parts.append("<table>")
            # treat first row as header if it looks like headers (non-empty, short-ish)
            first_cells = [norm_text(c.text) for c in rows[0].cells]
            is_header = all(first_cells) and all(len(c) <= 60 for c in first_cells)

            if is_header:
                body_parts.append("<thead><tr>")
                for cell in first_cells:
                    body_parts.append(f"<th>{escape(cell)}</th>")
                body_parts.append("</tr></thead>")
                start = 1
            else:
                start = 0

            body_parts.append("<tbody>")
            for r in rows[start:]:
                body_parts.append("<tr>")
                for c in r.cells:
                    body_parts.append(f"<td>{escape(norm_text(c.text))}</td>")
                body_parts.append("</tr>")
            body_parts.append("</tbody></table>")

    # close open structures
    if in_list:
        body_parts.append(f"</{list_kind}>")
    if open_section:
        body_parts.append("</section>")

    # Title heuristic: first Heading 1, else file name
    title = "AI Legal Services Specification"
    for lvl, text, hid in headings_for_toc:
        if lvl == 1:
            title = text
            break

    toc_html = build_toc(headings_for_toc)

    html_out = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="ai-legal-spec.css"/>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{escape(title)}</h1>
      <div class="meta">Generated from DOCX → HTML (deterministic conversion). Headings, lists, and tables preserved.</div>
    </div>
    {toc_html}
    {"".join(body_parts)}
    <p class="small">End of document.</p>
  </div>
</body>
</html>
"""
    css_out = build_default_css()
    return html_out, css_out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_docx", help="Path to input .docx")
    ap.add_argument("--out_dir", default="site", help="Output directory (default: site)")
    ap.add_argument("--html_name", default="ai-legal-spec.html", help="HTML filename")
    ap.add_argument("--css_name", default="ai-legal-spec.css", help="CSS filename")
    args = ap.parse_args()

    if not os.path.exists(args.input_docx):
        raise FileNotFoundError(args.input_docx)

    os.makedirs(args.out_dir, exist_ok=True)

    html_out, css_out = convert_docx_to_html(args.input_docx)

    html_path = os.path.join(args.out_dir, args.html_name)
    css_path = os.path.join(args.out_dir, args.css_name)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css_out)

    print(f"Saved HTML: {html_path}")
    print(f"Saved CSS : {css_path}")

if __name__ == "__main__":
    main()