"""
File Browser & Import Router

Enables the intake UI to browse local/synced folders (e.g., Dropbox)
and import files directly into the evidence pipeline.

Endpoints:
  GET  /files/browse        — List files in a local directory
  POST /files/import        — Import a local file as case evidence
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional

from src.services.evidence_ingestion import EvidenceIngestionService
from src.utils.ids import new_id

router = APIRouter(tags=["files"])


# ---------------------------------------------------------------------------
# Allowed base paths — prevent arbitrary filesystem traversal
# ---------------------------------------------------------------------------

# These are the root directories users are allowed to browse.
# Add Dropbox, OneDrive, or other sync folder paths as needed.
ALLOWED_ROOTS = []

def _get_allowed_roots():
    """Build allowed roots from env or defaults."""
    if ALLOWED_ROOTS:
        return ALLOWED_ROOTS

    # Auto-detect common sync folders
    home = Path.home()
    candidates = [
        home / "Dropbox",
        home / "OneDrive",
        home / "Documents",
        home / "Desktop",
        # Windows paths
        Path("C:/Users") / os.getenv("USERNAME", "") / "Dropbox" if os.name == "nt" else None,
        Path("C:/Users") / os.getenv("USERNAME", "") / "OneDrive" if os.name == "nt" else None,
    ]

    # Add from environment
    extra = os.getenv("CASECORE_BROWSE_PATHS", "")
    if extra:
        for p in extra.split(";"):
            p = p.strip()
            if p:
                candidates.append(Path(p))

    return [str(p) for p in candidates if p and p.exists()]


def _is_path_allowed(path: str) -> bool:
    """Check that path is under an allowed root (prevents directory traversal)."""
    resolved = os.path.realpath(path)
    allowed = _get_allowed_roots()

    # If no allowed roots configured, allow any existing path
    # (sandbox mode — trust the local user)
    if not allowed:
        return os.path.exists(resolved)

    return any(resolved.startswith(os.path.realpath(root)) for root in allowed)


# ---------------------------------------------------------------------------
# GET /files/browse
# ---------------------------------------------------------------------------

class FileEntry(BaseModel):
    name: str
    path: str
    size: int = 0
    is_dir: bool = False
    modified: Optional[str] = None
    extension: Optional[str] = None


@router.get("/files/browse")
def browse_directory(path: str = Query(..., description="Directory path to list")):
    """
    List files in a local directory.

    Used by the intake UI to browse synced folders (Dropbox, OneDrive, etc.)
    for importing evidence files.
    """
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"Not a directory: {path}")

    if not _is_path_allowed(path):
        raise HTTPException(status_code=403, detail="Access to this path is not allowed")

    try:
        entries = []
        for entry in sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())):
            try:
                stat = entry.stat()
                ext = os.path.splitext(entry.name)[1].lower() if not entry.is_dir() else None
                entries.append(FileEntry(
                    name=entry.name,
                    path=entry.path,
                    size=stat.st_size if not entry.is_dir() else 0,
                    is_dir=entry.is_dir(),
                    modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    extension=ext,
                ))
            except (PermissionError, OSError):
                continue  # Skip inaccessible files

        return {
            "success": True,
            "correlation_id": new_id(),
            "path": path,
            "count": len(entries),
            "files": [e.model_dump() for e in entries],
        }

    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")


# ---------------------------------------------------------------------------
# POST /files/import — Import a local file as evidence
# ---------------------------------------------------------------------------

class ImportFileRequest(BaseModel):
    path: str
    case_id: str
    actor: str = "attorney"


@router.post("/files/import")
def import_local_file(body: ImportFileRequest):
    """
    Import a local file into the evidence pipeline.

    Reads the file from the local filesystem and runs it through
    the full HASH → CLASSIFY → EXTRACT → TIMELINE → MAP pipeline.
    """
    if not os.path.exists(body.path):
        raise HTTPException(status_code=404, detail=f"File not found: {body.path}")

    if not os.path.isfile(body.path):
        raise HTTPException(status_code=400, detail=f"Not a file: {body.path}")

    if not _is_path_allowed(body.path):
        raise HTTPException(status_code=403, detail="Access to this file is not allowed")

    # Lazy import to match the DI pattern in intake router
    from src.routers.intake import get_evidence_svc, get_engine

    evidence_svc = get_evidence_svc()
    engine = get_engine()

    filename = os.path.basename(body.path)

    try:
        # Read file
        with open(body.path, "rb") as f:
            data = f.read()

        # Find intake if exists
        intake = engine.get_intake_by_case(body.case_id)
        intake_id = intake.intake_id if intake else None

        # Run full ingestion pipeline
        evidence = evidence_svc.ingest_bytes(
            data=data,
            filename=filename,
            case_id=body.case_id,
            intake_id=intake_id,
            actor=body.actor,
        )

        # If content extracted and intake exists, feed as response
        if intake and evidence.extracted_content and evidence.extracted_content.full_text:
            try:
                engine.respond(
                    intake_id=intake.intake_id,
                    session_id=intake.interview_session_id,
                    message=f"[Imported file: {filename}]\n\n{evidence.extracted_content.full_text[:5000]}",
                    role=body.actor,
                )
            except Exception:
                pass

        return {
            "success": True,
            "correlation_id": new_id(),
            "evidence_id": evidence.evidence_id,
            "filename": filename,
            "pipeline_summary": {
                "hash": evidence.metadata.sha256_hash,
                "type_detected": evidence.metadata.file_type.value,
                "text_length": len(evidence.extracted_content.full_text) if evidence.extracted_content else 0,
                "burden_elements_mapped": len(evidence.burden_element_mappings),
            },
        }

    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Cannot read file: {body.path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
