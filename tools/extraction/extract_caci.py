"""CACI extraction pipeline.

Reads pdftotext -layout output of the Judicial Council of California Civil Jury
Instructions 2026 PDF and emits canonical per-instruction JSON + MD into
authority_store/ca/caji/current/instructions/.

Also writes manifest.json and source_index.json.

This script is idempotent: re-running overwrites outputs.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Optional

# ---- Paths ----
REPO_ROOT = pathlib.Path(
    r"C:\Users\sfgon\Documents\GitHub\AI Legal Service"
)
WORKTREE_ROOT = pathlib.Path(
    r"C:\Users\sfgon\Documents\GitHub\AI Legal Service\.claude\worktrees\youthful-johnson-1ee1a2"
)
# Authority store lives in the REAL repo root (user's spec). Worktree shares it
# because worktrees use the same working dir pattern. We write to worktree path.
AUTH_ROOT = WORKTREE_ROOT / "authority_store" / "ca" / "caji" / "current"
INSTR_DIR = AUTH_ROOT / "instructions"
AUTH_ROOT.mkdir(parents=True, exist_ok=True)
INSTR_DIR.mkdir(parents=True, exist_ok=True)

LAYOUT_TXT = WORKTREE_ROOT / "tmp_extraction" / "caci_all_layout.txt"
SOURCE_PDF_ABS = pathlib.Path(
    r"C:\Users\sfgon\Downloads\judicial_council_of_california_civil_jury_instructions_2026.pdf"
)
SOURCE_LABEL = (
    "Judicial Council of California Civil Jury Instructions (2026 edition) "
    "- LexisNexis Matthew Bender Official Publisher"
)

# ---- Regex ----
HDR_RE = re.compile(r"^[ \t]*(\d{3,4}[A-Z]?)\.\s+(.+?)\s*$")
VF_RE = re.compile(r"^[ \t]*VF-(\d{3,4}[A-Z]?)\.\s+(.+?)\s*$")

# Footer / chrome line patterns to strip from body text.
FOOTER_PATTERNS = [
    re.compile(r"^\s*This version provided by LexisNexis.*$", re.I),
    re.compile(r"^\s*store\.lexisnexis\.com.*$", re.I),
    re.compile(r"^\s*Volume\s+\d+\s+Table of Contents\s*$", re.I),
    re.compile(r"^\s*\(\d+/\d+\s*[\u2014\-]\s*Pub\..*\)\s*$"),
    re.compile(r"^\s*for public and internal court use\s*$", re.I),
    # Running headers: "<SERIES>  CACI No. <N>" or "CACI No. <N>  <SERIES>"
    re.compile(r"^\s*[A-Z][A-Z'\-\.,\s]{2,80}\s{2,}CACI No\.\s*(?:VF-)?\d{3,4}[A-Z]?\s*$"),
    re.compile(r"^\s*CACI No\.\s*(?:VF-)?\d{3,4}[A-Z]?\s{2,}[A-Z][A-Z'\-\.,\s]{2,80}\s*$"),
]
# Patterns for bare-number page footers: only stripped when at the very end of a
# page, never mid-body (e.g. "2025" as year in "...December\n2025").
PAGE_NUM_RE = re.compile(r"^\s*\d{1,4}\s*$")
ROMAN_NUM_RE = re.compile(r"^\s*[ivxlcdm]+\s*$", re.I)

SECTION_HEADERS = [
    "Directions for Use",
    "Sources and Authority",
    "Secondary Sources",
]
SECTION_RE = re.compile(
    r"^\s*(Directions for Use|Sources and Authority|Secondary Sources)\s*$"
)


@dataclass
class Instruction:
    authority_id: str = "CA_CACI"
    family_id: str = "CACI"
    instruction_id: str = ""
    instruction_number: str = ""
    kind: str = "instruction"  # or "verdict_form"
    citation: str = ""
    title: str = ""
    instruction_text: str = ""
    directions_for_use: str = ""
    sources_and_authority: str = ""
    secondary_sources: str = ""
    effective_notes: str = ""
    source_label: str = SOURCE_LABEL
    source_pdf: str = str(SOURCE_PDF_ABS)
    page_start: int = 0
    page_end: int = 0
    captured_at: str = ""
    text_sha256: str = ""
    validation_status: str = "pending"
    validation_notes: list = field(default_factory=list)


def load_pages() -> list[str]:
    txt = LAYOUT_TXT.read_text(encoding="utf-8", errors="replace")
    pages = txt.split("\f")
    # pdftotext often produces a trailing empty page — ok
    return pages


def find_instruction_starts(pages: list[str]) -> list[tuple[int, str, str, str]]:
    """Return list of (pdf_page_index_0based, instruction_id, title_first_line, kind)."""
    starts: list[tuple[int, str, str, str]] = []
    for i, pg in enumerate(pages):
        non_empty = [ln for ln in pg.splitlines() if ln.strip()]
        if not non_empty:
            continue
        first = non_empty[0]
        # Only match on the FIRST non-empty line. This prevents matching
        # series-title pages (e.g. "EQUITABLE INDEMNITY" appears first).
        mvf = VF_RE.match(first)
        mhdr = HDR_RE.match(first)
        if mvf:
            starts.append((i, f"VF-{mvf.group(1)}", mvf.group(2), "verdict_form"))
            continue
        if not mhdr:
            continue
        # TOC guard: if many header-like lines appear in the first 15 non-empty
        # lines, it's likely a TOC page.
        hdr_like = sum(
            1 for ln in non_empty[:15] if HDR_RE.match(ln) or VF_RE.match(ln)
        )
        if hdr_like >= 3:
            continue
        starts.append((i, mhdr.group(1), mhdr.group(2), "instruction"))
    return starts


def clean_footer_lines(lines: list[str]) -> list[str]:
    """Strip LexisNexis footers and running headers. Strip bare page-number
    lines ONLY when they appear as the last non-empty line on the page (this
    prevents gobbling standalone years like "2025" in a revision note).
    """
    out = []
    for ln in lines:
        if any(p.match(ln) for p in FOOTER_PATTERNS):
            continue
        out.append(ln)
    # Strip trailing page-number line (if last non-empty is bare number/roman)
    # and also any trailing blank-only lines after.
    # Walk from end backwards to find the last non-empty.
    trailing_blanks = 0
    while out and out[-1].strip() == "":
        out.pop()
        trailing_blanks += 1
    if out and (PAGE_NUM_RE.match(out[-1]) or ROMAN_NUM_RE.match(out[-1])):
        out.pop()
    # Also handle leading page-number (some pages start with a page header number)
    while out and out[0].strip() == "":
        out.pop(0)
    if out and (PAGE_NUM_RE.match(out[0]) or ROMAN_NUM_RE.match(out[0])):
        # But only strip leading number if it's short (1-3 digits) — this is
        # a page number at top of a continuation page. Avoid stripping "2025".
        leading = out[0].strip()
        if len(leading) <= 3:
            out.pop(0)
    return out


def extract_title_block(raw_lines: list[str]) -> tuple[str, int]:
    """Return (title, index_after_title_block). Title can span multi-line until
    the first blank line after the header line."""
    # Find header line (first non-blank)
    hdr_i = 0
    while hdr_i < len(raw_lines) and not raw_lines[hdr_i].strip():
        hdr_i += 1
    if hdr_i >= len(raw_lines):
        return "", hdr_i
    m = HDR_RE.match(raw_lines[hdr_i]) or VF_RE.match(raw_lines[hdr_i])
    if not m:
        return "", hdr_i
    title_parts = [m.group(2).strip()]
    j = hdr_i + 1
    # Continuation: non-blank lines with significant indentation (centered)
    while j < len(raw_lines) and raw_lines[j].strip():
        cand = raw_lines[j].strip()
        # Stop if this is a section header or body start.
        if SECTION_RE.match(raw_lines[j]):
            break
        # Heuristic: title continuation is typically centered (>15 leading spaces)
        # OR a very short phrase without ending punctuation
        indent = len(raw_lines[j]) - len(raw_lines[j].lstrip())
        is_short = len(cand.split()) <= 10 and not cand.endswith(".")
        if indent >= 15 or is_short:
            title_parts.append(cand)
            j += 1
            continue
        break
    title = " ".join(title_parts).strip()
    # Normalize unicode section sign and en-dashes
    title = title.replace("\u00a7", "\u00a7")  # keep §
    return title, j


def split_sections(body_text: str) -> dict:
    """Split a multi-line body string into instruction_text, directions_for_use,
    sources_and_authority, secondary_sources, effective_notes.
    """
    lines = body_text.splitlines()
    # Look for the effective/revision note (e.g., "New September 2003; Revised December 2012")
    # which typically appears just before "Directions for Use".
    buckets = {
        "instruction_text": [],
        "directions_for_use": [],
        "sources_and_authority": [],
        "secondary_sources": [],
    }
    current = "instruction_text"
    header_map = {
        "Directions for Use": "directions_for_use",
        "Sources and Authority": "sources_and_authority",
        "Secondary Sources": "secondary_sources",
    }
    for ln in lines:
        m = SECTION_RE.match(ln)
        if m:
            current = header_map[m.group(1)]
            continue
        buckets[current].append(ln)

    # Post-process: extract effective note from tail of instruction_text.
    # The note is the LAST block (separated by blank lines) and begins with one
    # of the effective-date keywords. It may wrap across lines.
    instr = "\n".join(buckets["instruction_text"]).rstrip()
    eff = ""
    blocks = re.split(r"\n\s*\n", instr)
    if blocks:
        last = blocks[-1].strip()
        if re.match(
            r"^(New|Derived|Revised|Renumbered|Revoked)\b[\s\S]{0,400}\b\d{4}\s*$",
            last,
        ):
            eff = re.sub(r"\s+", " ", last).strip()
            instr = "\n\n".join(blocks[:-1]).rstrip()

    def norm(lst: list[str]) -> str:
        # Collapse trailing whitespace, remove runs of 3+ blank lines
        out = []
        blank_run = 0
        for ln in lst:
            if ln.strip() == "":
                blank_run += 1
                if blank_run <= 1:
                    out.append("")
            else:
                blank_run = 0
                out.append(ln.rstrip())
        # Trim leading/trailing blanks
        while out and out[0].strip() == "":
            out.pop(0)
        while out and out[-1].strip() == "":
            out.pop()
        return "\n".join(out)

    return {
        "instruction_text": instr.strip(),
        "directions_for_use": norm(buckets["directions_for_use"]),
        "sources_and_authority": norm(buckets["sources_and_authority"]),
        "secondary_sources": norm(buckets["secondary_sources"]),
        "effective_notes": eff,
    }


def build_instruction(
    pages: list[str],
    start_idx: int,
    end_idx: int,
    ident: str,
    kind: str,
) -> Instruction:
    # end_idx is exclusive
    raw_pages = pages[start_idx:end_idx]
    # Strip each page's footer lines
    combined_lines: list[str] = []
    for pg in raw_pages:
        cleaned = clean_footer_lines(pg.splitlines())
        combined_lines.extend(cleaned)
        # Preserve blank line between original pages
        combined_lines.append("")
    # Remove excess trailing blanks
    while combined_lines and combined_lines[-1].strip() == "":
        combined_lines.pop()

    title, after_title_i = extract_title_block(combined_lines)
    body_lines = combined_lines[after_title_i:]
    body_text = "\n".join(body_lines)
    sections = split_sections(body_text)

    # Citation string
    if kind == "verdict_form":
        citation = f"CACI No. VF-{ident[3:]}"  # ident is 'VF-####'
    else:
        citation = f"CACI No. {ident}"

    inst_text = sections["instruction_text"]
    sha = hashlib.sha256(
        (title + "\n" + inst_text).encode("utf-8", errors="replace")
    ).hexdigest()

    # Validation
    notes: list[str] = []
    status = "valid"
    # Revoked-instruction detection: either the instruction body or the
    # effective_notes field begins with "Revoked <Month Year>" and there is
    # little/no other body content.
    revoked_re = re.compile(
        r"^\s*Revoked\s+[A-Za-z]+\s+\d{4}",
        re.I,
    )
    eff_note = sections["effective_notes"]
    is_revoked = (
        revoked_re.match(inst_text.strip())
        or revoked_re.match(eff_note.strip())
    ) and len(inst_text.strip()) < 200
    if is_revoked:
        status = "revoked"
        notes.append("instruction is revoked (no body content)")
    elif len(inst_text.strip()) < 20:
        status = "quarantine"
        notes.append("instruction_text too short (<20 chars)")
    # Flag if site chrome somehow crept in
    chrome_tokens = [
        "skip to content",
        "sitemap",
        "quick search",
        "My Subscriptions",
        "leginfo.legislature",
    ]
    joined = (inst_text + sections["directions_for_use"] + sections["sources_and_authority"]).lower()
    if any(t.lower() in joined for t in chrome_tokens):
        status = "quarantine"
        notes.append("detected web chrome tokens in body")
    if not title:
        status = "quarantine"
        notes.append("missing title")

    return Instruction(
        instruction_id=f"CACI_{ident}",
        instruction_number=ident,
        kind=kind,
        citation=citation,
        title=title,
        instruction_text=inst_text,
        directions_for_use=sections["directions_for_use"],
        sources_and_authority=sections["sources_and_authority"],
        secondary_sources=sections["secondary_sources"],
        effective_notes=sections["effective_notes"],
        page_start=start_idx + 1,  # 1-based
        page_end=end_idx,  # end_idx is exclusive, so last_page=end_idx in 1-based
        captured_at=datetime.now(timezone.utc).isoformat(),
        text_sha256=sha,
        validation_status=status,
        validation_notes=notes,
    )


def write_md(inst: Instruction, md_path: pathlib.Path) -> None:
    out = []
    out.append(f"# {inst.citation}")
    out.append("")
    out.append(f"**Title:** {inst.title}")
    out.append("")
    out.append(f"**Source:** {inst.source_label}")
    out.append(f"**Source PDF:** {pathlib.Path(inst.source_pdf).name}")
    out.append(f"**Pages:** {inst.page_start}\u2013{inst.page_end}")
    if inst.effective_notes:
        out.append(f"**Effective:** {inst.effective_notes}")
    out.append("")
    out.append("## Instruction")
    out.append("")
    out.append(inst.instruction_text or "(empty)")
    if inst.directions_for_use:
        out.append("")
        out.append("## Directions for Use")
        out.append("")
        out.append(inst.directions_for_use)
    if inst.sources_and_authority:
        out.append("")
        out.append("## Sources and Authority")
        out.append("")
        out.append(inst.sources_and_authority)
    if inst.secondary_sources:
        out.append("")
        out.append("## Secondary Sources")
        out.append("")
        out.append(inst.secondary_sources)
    md_path.write_text("\n".join(out), encoding="utf-8")


def main(argv: list[str]) -> int:
    only_ids = set(argv[1:]) if len(argv) > 1 else set()

    pages = load_pages()
    print(f"[info] pages loaded: {len(pages)}")
    starts = find_instruction_starts(pages)
    print(f"[info] instruction starts found: {len(starts)}")

    # Build end boundaries
    items = []
    for i, (pidx, ident, _title, kind) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(pages)
        items.append((pidx, end, ident, kind))

    if only_ids:
        items = [x for x in items if x[2] in only_ids]
        print(f"[info] filtered to {len(items)} targets: {sorted(only_ids)}")

    manifest_instructions = []
    source_index_entries = []
    valid_count = 0
    quarantine_count = 0
    revoked_count = 0

    for pidx, end, ident, kind in items:
        inst = build_instruction(pages, pidx, end, ident, kind)
        # File path
        json_path = INSTR_DIR / f"CACI_{ident}.json"
        md_path = INSTR_DIR / f"CACI_{ident}.md"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(inst), f, ensure_ascii=False, indent=2)
        write_md(inst, md_path)
        if inst.validation_status == "valid":
            valid_count += 1
        elif inst.validation_status == "quarantine":
            quarantine_count += 1
        elif inst.validation_status == "revoked":
            revoked_count += 1
        manifest_instructions.append(
            {
                "instruction_id": inst.instruction_id,
                "instruction_number": inst.instruction_number,
                "kind": inst.kind,
                "citation": inst.citation,
                "title": inst.title,
                "page_start": inst.page_start,
                "page_end": inst.page_end,
                "text_sha256": inst.text_sha256,
                "validation_status": inst.validation_status,
                "json_path": f"instructions/{json_path.name}",
                "md_path": f"instructions/{md_path.name}",
            }
        )
        source_index_entries.append(
            {
                "instruction_id": inst.instruction_id,
                "source_pdf": inst.source_pdf,
                "source_label": inst.source_label,
                "page_start": inst.page_start,
                "page_end": inst.page_end,
            }
        )

    # Only write manifest if doing a full run
    if not only_ids:
        manifest = {
            "authority_id": "CA_CACI",
            "family_id": "CACI",
            "family_label": "California Civil Jury Instructions",
            "edition": "2026",
            "source_label": SOURCE_LABEL,
            "source_pdf": str(SOURCE_PDF_ABS),
            "source_pdf_page_count": len(pages),
            "built_at": datetime.now(timezone.utc).isoformat(),
            "instruction_count": len(manifest_instructions),
            "valid_count": valid_count,
            "quarantine_count": quarantine_count,
            "revoked_count": revoked_count,
            "instructions": manifest_instructions,
        }
        (AUTH_ROOT / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        source_index = {
            "authority_id": "CA_CACI",
            "family_id": "CACI",
            "edition": "2026",
            "source_pdf": str(SOURCE_PDF_ABS),
            "source_label": SOURCE_LABEL,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "entries": source_index_entries,
        }
        (AUTH_ROOT / "source_index.json").write_text(
            json.dumps(source_index, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(
        f"[done] wrote {len(manifest_instructions)} instructions "
        f"(valid={valid_count}, revoked={revoked_count}, quarantine={quarantine_count})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
