"""
Bulk Evidence Import Router

Endpoints for importing pre-processed evidence in bulk:
  POST /bulk/import-spreadsheet     — Import email evidence from a parsed spreadsheet
  POST /bulk/import-folder          — Import raw files from a local folder
  GET  /bulk/import-status          — Check status of a bulk import job
"""

import hashlib
import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from src.services.evidence_vault import (
    get_evidence_vault, EvidenceVault,
    DerivationMethod, SourceRecord,
)
from src.utils.ids import new_id

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bulk-import"])

# ---------------------------------------------------------------------------
# Job tracking
# ---------------------------------------------------------------------------

_import_jobs: dict[str, dict] = {}


class BulkImportRequest(BaseModel):
    case_id: str
    source_description: str = "Spreadsheet bulk import"


# ---------------------------------------------------------------------------
# POST /bulk/import-spreadsheet
# ---------------------------------------------------------------------------

@router.post("/bulk/import-spreadsheet")
async def import_spreadsheet(
    file: UploadFile = File(...),
    case_id: str = Form(default="CASE-INTAKE-001"),
):
    """
    Import email evidence from a parsed spreadsheet (.xlsx).

    Expects two sheets:
      - Master_File_Log: file_name, file_id, file_extension, file_size, hash, full_path
      - Tagged_Documents: Filename, File_ID, Extracted Text, Tags, Actors

    For each row with Extracted Text:
      1. Register source in vault using the provided hash
      2. Store extracted text as a derivation
      3. Skip rows with no text or duplicate hashes

    Returns import summary with counts and any errors.
    """
    import tempfile
    import pandas as pd

    # Save uploaded file to temp
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        # Read both sheets
        mfl = pd.read_excel(tmp_path, sheet_name="Master_File_Log")
        td = pd.read_excel(tmp_path, sheet_name="Tagged_Documents")

        # Merge on file_id / File_ID
        mfl_lookup = {}
        for _, row in mfl.iterrows():
            fid = str(row.get("file_id", ""))
            if fid:
                mfl_lookup[fid] = {
                    "file_name": str(row.get("file_name", "")),
                    "file_size": int(row.get("file_size", 0)) if pd.notna(row.get("file_size")) else 0,
                    "hash": str(row.get("hash", "")) if pd.notna(row.get("hash")) else "",
                    "full_path": str(row.get("full_path", "")) if pd.notna(row.get("full_path")) else "",
                    "page_count": int(row.get("page_count", 0)) if pd.notna(row.get("page_count")) else 0,
                    "extension": str(row.get("file_extension", "")) if pd.notna(row.get("file_extension")) else "",
                }

        vault = get_evidence_vault()
        results = {
            "total_rows": len(td),
            "imported": 0,
            "skipped_no_text": 0,
            "skipped_dedup": 0,
            "errors": 0,
            "error_details": [],
            "imported_evidence_ids": [],
        }

        for idx, row in td.iterrows():
            text = row.get("Extracted Text")
            if pd.isna(text) or not str(text).strip() or len(str(text).strip()) < 20:
                results["skipped_no_text"] += 1
                continue

            text = str(text).strip()
            file_id = str(row.get("File_ID", ""))
            filename = str(row.get("Filename", f"email_{idx}.pdf"))

            # Get metadata from Master File Log
            meta = mfl_lookup.get(file_id, {})
            original_hash = meta.get("hash", "")

            # Check dedup by original hash
            if original_hash and vault.has_evidence(original_hash):
                results["skipped_dedup"] += 1
                # Still add the text as derivation if not already there
                existing = vault.get_evidence_by_hash(original_hash)
                if existing:
                    existing_derivs = vault.list_derivations(
                        source_evidence_id=existing.evidence_id
                    )
                    has_text = any(
                        d.artifact_type == "extracted_text" for d in existing_derivs
                    )
                    if not has_text:
                        try:
                            vault.add_derivation(
                                source_evidence_id=existing.evidence_id,
                                method=DerivationMethod.TEXT_EXTRACTION,
                                method_version="spreadsheet_import_v1",
                                artifact_type="extracted_text",
                                artifact_text=text[:50000],
                                parameters={
                                    "source": "deposition_prep.xlsx",
                                    "sheet": "Tagged_Documents",
                                    "row": idx,
                                },
                            )
                        except Exception:
                            pass
                continue

            try:
                # Create a virtual source record
                # We don't have the actual file, so we use the hash from the spreadsheet
                # and create a placeholder source entry
                evidence_id = new_id()
                file_size = meta.get("file_size", len(text.encode("utf-8")))

                # Compute hash from text if no original hash
                if not original_hash:
                    original_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

                source_record = SourceRecord(
                    evidence_id=evidence_id,
                    case_id=case_id,
                    sha256=original_hash,
                    original_filename=filename,
                    file_size_bytes=file_size,
                    mime_type="application/pdf",
                    vault_path=f"virtual/{original_hash[:8]}/{filename}",
                    ingested_at=datetime.now(timezone.utc).isoformat(),
                    ingested_by="bulk_import",
                    cloud_source=meta.get("full_path", ""),
                    file_metadata={
                        "page_count": meta.get("page_count", 0),
                        "import_source": "deposition_prep.xlsx",
                        "original_file_id": file_id,
                        "category": _categorize_email(filename, text),
                    },
                )

                # Register in vault's internal index
                vault._sources[evidence_id] = source_record
                vault._by_hash[original_hash] = evidence_id

                # Add the extracted text as a derivation
                vault.add_derivation(
                    source_evidence_id=evidence_id,
                    method=DerivationMethod.TEXT_EXTRACTION,
                    method_version="spreadsheet_import_v1",
                    artifact_type="extracted_text",
                    artifact_text=text[:50000],
                    parameters={
                        "source": "deposition_prep.xlsx",
                        "sheet": "Tagged_Documents",
                        "row": idx,
                        "text_length": len(text),
                    },
                )

                results["imported"] += 1
                results["imported_evidence_ids"].append(evidence_id)

            except Exception as e:
                results["errors"] += 1
                results["error_details"].append({
                    "row": idx,
                    "filename": filename,
                    "error": str(e),
                })

        # Save vault manifest
        vault._save_manifest()

        # Trim evidence IDs list for response (just show count)
        total_imported = len(results["imported_evidence_ids"])
        results["imported_evidence_ids"] = results["imported_evidence_ids"][:10]
        if total_imported > 10:
            results["imported_evidence_ids"].append(f"... and {total_imported - 10} more")

        return {
            "success": True,
            "correlation_id": new_id(),
            "case_id": case_id,
            **results,
        }

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# POST /bulk/import-folder
# ---------------------------------------------------------------------------

@router.post("/bulk/import-folder")
def import_folder(
    folder_path: str = Form(...),
    case_id: str = Form(default="CASE-INTAKE-001"),
    file_pattern: str = Form(default="*.pdf"),
    max_files: int = Form(default=100),
):
    """
    Import raw files from a local folder into the evidence vault.

    Each file is:
      1. SHA-256 hashed
      2. Stored in vault (dedup check)
      3. Text extracted if supported file type

    Runs as a background job. Returns job_id for status polling.
    """
    if not os.path.isdir(folder_path):
        raise HTTPException(404, f"Folder not found: {folder_path}")

    job_id = new_id()
    _import_jobs[job_id] = {
        "job_id": job_id,
        "status": "running",
        "folder": folder_path,
        "case_id": case_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "processed": 0,
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "total": 0,
    }

    def _run_import():
        vault = get_evidence_vault()
        job = _import_jobs[job_id]

        files = sorted(Path(folder_path).glob(file_pattern))[:max_files]
        job["total"] = len(files)

        for f in files:
            job["processed"] += 1
            try:
                record, is_new = vault.ingest_source(
                    file_path=str(f),
                    case_id=case_id,
                    original_filename=f.name,
                    actor="bulk_import",
                )
                if is_new:
                    job["imported"] += 1
                else:
                    job["skipped"] += 1
            except Exception as e:
                job["errors"] += 1
                logger.error(f"Folder import error for {f.name}: {e}")

        job["status"] = "complete"
        job["completed_at"] = datetime.now(timezone.utc).isoformat()

    thread = threading.Thread(target=_run_import, daemon=True)
    thread.start()

    return {
        "success": True,
        "correlation_id": new_id(),
        "job_id": job_id,
        "status": "running",
        "total_files": _import_jobs[job_id]["total"],
        "message": f"Import started for {folder_path}. Poll GET /bulk/import-status?job_id={job_id}",
    }


# ---------------------------------------------------------------------------
# GET /bulk/import-status
# ---------------------------------------------------------------------------

@router.get("/bulk/import-status")
def import_status(job_id: str):
    """Check status of a bulk import job."""
    job = _import_jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    return {"success": True, **job}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _categorize_email(filename: str, text: str) -> str:
    """Categorize an email based on filename and content keywords."""
    fn_lower = filename.lower()
    text_lower = text[:2000].lower()

    if "helios" in fn_lower or "helios" in text_lower:
        return "Helios Distribution"
    if "preferred" in fn_lower or "preferred gardens" in text_lower:
        return "Preferred Gardens"
    if "yolo" in fn_lower or "yolo" in text_lower:
        return "YOLO Farms"
    if "fiori" in fn_lower or "fiori" in text_lower:
        return "Fiori"
    if "distinguished" in fn_lower or "distinguished" in text_lower:
        return "Distinguished Gardens"
    if "highlands" in fn_lower or "highlands" in text_lower:
        return "Highlands"
    if "packaging" in fn_lower:
        return "Packaging"
    if "contract" in fn_lower or "agreement" in text_lower:
        return "Contracts"
    if "invoice" in text_lower or "payment" in text_lower:
        return "Financial"
    if "license" in text_lower or "permit" in text_lower or "cup" in text_lower:
        return "Licensing/Permits"
    if "text message" in fn_lower or "imessage" in text_lower:
        return "Text Messages"
    return "General Correspondence"
