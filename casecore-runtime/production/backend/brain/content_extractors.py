"""
Content extractors for the ingest pipeline.

Dispatch by file_type. Plain text / email / html are handled natively.
PDF and DOCX use optional imports (pypdf, python-docx); if those libraries
are missing at runtime, the extractor raises ExtractorUnsupported and the
ingest pipeline marks the document extract_skipped (not failed).

No module in this file imports anything analytical (no resolver-adjacent
code). Enforced by SR-12.
"""
from __future__ import annotations

import email
import html
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ExtractorUnsupported(Exception):
    """Raised when an extractor cannot run (missing dep or unknown format)."""


@dataclass
class ExtractionResult:
    text: str
    char_count: int
    engine: str
    # Reliability signals (see contract rules: no silent "empty text" success):
    #   status: TEXT_EXTRACTION_COMPLETE | OCR_REQUIRED | OCR_NOT_AVAILABLE
    #         | EXTRACTION_FAILED | UNSUPPORTED_TYPE | NOT_ATTEMPTED
    status: str = "TEXT_EXTRACTION_COMPLETE"
    confidence: float = 0.0
    is_scanned_pdf: bool = False
    notes: str = ""


# ----------- type detection -----------

_EXT_MAP = {
    ".txt": "text", ".md": "text", ".log": "text", ".csv": "text",
    ".eml": "email", ".msg": "email",
    ".html": "html", ".htm": "html",
    ".pdf": "pdf",
    ".docx": "docx",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image", ".tif": "image", ".tiff": "image",
    ".zip": "archive",
}


def detect_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return _EXT_MAP.get(ext, "binary")


# ----------- extractors -----------

def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def _read_text_best_effort(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def extract_text(storage_path: str, file_type: str) -> ExtractionResult:
    """Dispatch to the right extractor based on file_type."""
    if file_type == "text":
        return _extract_plain(storage_path)
    if file_type == "email":
        return _extract_email(storage_path)
    if file_type == "html":
        return _extract_html(storage_path)
    if file_type == "pdf":
        return _extract_pdf(storage_path)
    if file_type == "docx":
        return _extract_docx(storage_path)
    raise ExtractorUnsupported(f"no extractor for file_type={file_type}")


def _extract_plain(path: str) -> ExtractionResult:
    text = _read_text_best_effort(_read_bytes(path))
    status = "TEXT_EXTRACTION_COMPLETE" if text.strip() else "EXTRACTION_FAILED"
    conf = 0.95 if text.strip() else 0.0
    return ExtractionResult(
        text=text, char_count=len(text), engine="plain",
        status=status, confidence=conf,
        notes="" if status == "TEXT_EXTRACTION_COMPLETE" else "file was empty or unreadable",
    )


def _extract_email(path: str) -> ExtractionResult:
    raw = _read_bytes(path)
    msg = email.message_from_bytes(raw)
    parts = []
    # headers
    for h in ("From", "To", "Cc", "Subject", "Date"):
        v = msg.get(h)
        if v:
            parts.append(f"{h}: {v}")
    # body
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                parts.append(_read_text_best_effort(payload))
    else:
        payload = msg.get_payload(decode=True) or b""
        parts.append(_read_text_best_effort(payload))
    text = "\n".join(p for p in parts if p)
    status = "TEXT_EXTRACTION_COMPLETE" if text.strip() else "EXTRACTION_FAILED"
    conf = 0.9 if text.strip() else 0.0
    return ExtractionResult(
        text=text, char_count=len(text), engine="email",
        status=status, confidence=conf,
    )


def _extract_html(path: str) -> ExtractionResult:
    raw = _read_text_best_effort(_read_bytes(path))
    # very simple tag strip; attorney-facing text-only. Preserve line breaks.
    no_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", no_scripts)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    clean = text.strip()
    status = "TEXT_EXTRACTION_COMPLETE" if clean else "EXTRACTION_FAILED"
    conf = 0.85 if clean else 0.0
    return ExtractionResult(
        text=clean, char_count=len(clean), engine="html-basic",
        status=status, confidence=conf,
    )


def _extract_pdf(path: str) -> ExtractionResult:
    """
    Extract text from a PDF via pypdf. Also detect likely scanned-only PDFs
    (image-rendered pages with ~0 extractable text) and return
    status=OCR_REQUIRED so the ingest pipeline does not silently mark the
    document "complete" with an empty body.
    """
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as e:
        raise ExtractorUnsupported(f"pypdf not installed: {e}")
    reader = PdfReader(path)
    pages = []
    per_page_chars = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        pages.append(t)
        per_page_chars.append(len(t.strip()))
    text = "\n\n".join(pages).strip()
    total_chars = len(text)
    n_pages = len(pages) or 1
    avg_per_page = total_chars / n_pages

    # Heuristic: scanned PDF signature.
    # - No extractable text across any page, OR
    # - fewer than 20 text chars per page on average AND at least 3 pages.
    # A single short text page legitimately has low chars so we require >=3
    # pages before flagging "scanned" on the <20 avg signal.
    scanned = False
    if total_chars == 0 and n_pages >= 1:
        scanned = True
    elif n_pages >= 3 and avg_per_page < 20:
        scanned = True

    if scanned:
        return ExtractionResult(
            text=text, char_count=total_chars, engine="pypdf",
            status="OCR_REQUIRED", confidence=0.0, is_scanned_pdf=True,
            notes=f"{n_pages} page(s), {total_chars} chars total, avg {avg_per_page:.1f}/page",
        )
    # Confidence scales with char density, capped at 0.9 for pypdf.
    conf = min(0.9, 0.3 + (avg_per_page / 400.0))
    return ExtractionResult(
        text=text, char_count=total_chars, engine="pypdf",
        status="TEXT_EXTRACTION_COMPLETE", confidence=conf, is_scanned_pdf=False,
        notes=f"{n_pages} page(s), avg {avg_per_page:.0f} chars/page",
    )


def _extract_docx(path: str) -> ExtractionResult:
    try:
        import docx  # type: ignore  # python-docx
    except ImportError as e:
        raise ExtractorUnsupported(f"python-docx not installed: {e}")
    doc = docx.Document(path)
    paras = [p.text for p in doc.paragraphs if p.text]
    text = "\n".join(paras)
    status = "TEXT_EXTRACTION_COMPLETE" if text.strip() else "EXTRACTION_FAILED"
    conf = 0.9 if text.strip() else 0.0
    return ExtractionResult(
        text=text, char_count=len(text), engine="python-docx",
        status=status, confidence=conf,
        notes="" if status == "TEXT_EXTRACTION_COMPLETE" else "docx contained no paragraph text (likely image-only)",
    )


# ----------- normalization + indexing -----------

def normalize(text: str) -> str:
    """Whitespace + encoding normalization. Deterministic."""
    if not text:
        return ""
    # unify line endings
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    # strip trailing whitespace per line
    t = "\n".join(line.rstrip() for line in t.split("\n"))
    # collapse runs of 3+ blank lines
    t = re.sub(r"\n{3,}", "\n\n", t)
    # collapse runs of spaces/tabs
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


_INDEX_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']{2,}")


def build_index(text: str, top_k: int = 64) -> dict:
    """Small deterministic inverted-like index (top-K term frequencies)."""
    if not text:
        return {"top_terms": {}, "token_count": 0}
    tokens = [t.lower() for t in _INDEX_TOKEN_RE.findall(text)]
    freq: dict = {}
    for tok in tokens:
        freq[tok] = freq.get(tok, 0) + 1
    top = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]
    return {"top_terms": dict(top), "token_count": len(tokens)}
