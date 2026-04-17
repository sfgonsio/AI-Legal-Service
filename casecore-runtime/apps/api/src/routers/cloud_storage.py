"""
Cloud Storage Router
FastAPI endpoints for cloud storage integration (Dropbox, Google Drive, OneDrive, etc.)

Endpoints:
  GET  /cloud/providers                  — List available providers with connection status
  GET  /cloud/{provider}/auth            — Start OAuth authorization
  POST /cloud/{provider}/callback        — OAuth callback (exchange code for token)
  GET  /cloud/{provider}/connections    — List active connections
  GET  /cloud/{provider}/files           — Browse cloud storage files
  POST /cloud/{provider}/import          — Import a single file as evidence
  POST /cloud/{provider}/import-batch    — Import multiple files
  DELETE /cloud/{provider}/disconnect    — Revoke connection
"""

import json
import logging
import os
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.services.cloud_storage import (
    get_cloud_storage_manager,
    CloudProvider,
    CloudFileEntry,
    FileType,
)
from src.services.video_processor import get_video_processor
from src.services.evidence_vault import (
    get_evidence_vault, DerivationMethod,
)
from src.routers.intake import get_evidence_svc, get_engine
from src.utils.ids import new_id

logger = logging.getLogger(__name__)
router = APIRouter(tags=["cloud_storage"])

# ---------------------------------------------------------------------------
# Background Job Tracking
# ---------------------------------------------------------------------------
# Stages and their weight in the 0-100% progress:
#   downloading: 0-40%
#   extracting_audio: 40-55%
#   transcribing: 55-85%
#   capturing_frames: 85-95%
#   feeding_intake: 95-100%

_import_jobs: Dict[str, Dict[str, Any]] = {}


def _update_job(job_id: str, **kwargs):
    """Thread-safe job status update."""
    if job_id in _import_jobs:
        _import_jobs[job_id].update(kwargs)


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class ProviderInfo(BaseModel):
    """Cloud provider availability info."""
    provider: str
    status: str  # "configured", "not_configured"
    connected: bool
    connection_count: int


class AuthUrlResponse(BaseModel):
    """OAuth authorization URL response."""
    provider: str
    auth_url: str
    state: str


class CallbackRequest(BaseModel):
    """OAuth callback handler request."""
    code: str
    state: str


class TokenResponse(BaseModel):
    """Token exchange response."""
    provider: str
    account_id: Optional[str]
    email: Optional[str]
    token_type: str = "Bearer"
    expires_in: int


class ConnectionInfo(BaseModel):
    """Active connection info."""
    connection_id: str
    provider: str
    account_id: Optional[str]
    email: Optional[str]
    created_at: str


class FileEntryResponse(BaseModel):
    """File entry in cloud storage."""
    name: str
    path: str
    file_id: str
    size: int
    is_dir: bool
    extension: Optional[str]
    file_type: str
    modified: Optional[str]


class ListFilesResponse(BaseModel):
    """File listing response."""
    success: bool
    correlation_id: str
    provider: str
    path: str
    count: int
    files: List[FileEntryResponse]


class ImportFileRequest(BaseModel):
    """Request to import a single file."""
    file_path: str = Field(..., description="Cloud storage file path (e.g., /folder/video.mp4)")
    file_id: Optional[str] = Field(default=None, description="File ID from cloud provider")
    case_id: str = Field(..., description="Case ID for intake")
    actor: str = Field(default="attorney", description="User role (attorney, client, etc.)")


class ImportBatchRequest(BaseModel):
    """Request to import multiple files."""
    file_paths: List[str] = Field(..., description="List of file paths to import")
    case_id: str = Field(..., description="Case ID for intake")
    actor: str = Field(default="attorney", description="User role")


class ImportFileResponse(BaseModel):
    """Response from importing a file."""
    success: bool
    correlation_id: str
    file_path: str
    filename: str
    evidence_id: Optional[str] = None
    video_id: Optional[str] = None
    pipeline_summary: Optional[dict] = None
    video_processing_result: Optional[dict] = None
    error: Optional[str] = None


class ImportBatchResponse(BaseModel):
    """Response from batch import."""
    success: bool
    correlation_id: str
    case_id: str
    total: int
    imported: int
    failed: int
    results: List[ImportFileResponse]


class DisconnectResponse(BaseModel):
    """Disconnect response."""
    success: bool
    provider: str
    connection_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/cloud/providers")
def list_providers() -> dict:
    """
    List available cloud storage providers and connection status.

    Returns info about each provider:
      - status: "configured" if env vars are set, else "not_configured"
      - connected: whether there's an active connection
      - connection_count: number of active connections
    """
    manager = get_cloud_storage_manager()
    providers = manager.get_available_providers()
    return {
        "success": True,
        "correlation_id": new_id(),
        "providers": providers,
    }


@router.get("/cloud/{provider}/auth")
def start_auth(provider: str, format: Optional[str] = None):
    """
    Start OAuth authorization flow.

    By default, redirects the browser directly to the provider's consent screen.
    Pass ?format=json to get the URL as JSON instead of redirecting.

    Args:
        provider: Provider name (dropbox, google_drive, onedrive)
        format: "json" to return URL as JSON, otherwise redirects browser
    """
    from fastapi.responses import RedirectResponse

    try:
        prov_enum = CloudProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    manager = get_cloud_storage_manager()

    try:
        auth_response = manager.start_authorization(prov_enum)

        # Default: redirect browser to provider's OAuth consent screen
        if format == "json":
            return AuthUrlResponse(
                provider=provider,
                auth_url=auth_response.auth_url,
                state=auth_response.state,
            )
        return RedirectResponse(url=auth_response.auth_url)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cloud/{provider}/callback")
def oauth_callback(provider: str, code: str = Query(...), state: str = Query("")):
    """
    OAuth callback handler (GET — Dropbox redirects here with ?code=...&state=...).

    Exchanges the authorization code for an access token, then shows a
    success page so the user knows the connection worked.
    """
    from fastapi.responses import HTMLResponse

    try:
        prov_enum = CloudProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    manager = get_cloud_storage_manager()

    try:
        response = manager.exchange_code(prov_enum, code, state)
        logger.info(f"OAuth exchange successful for {provider}")

        # Return a friendly HTML page instead of raw JSON
        return HTMLResponse(content=f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>CaseCore — Connected</title>
<style>
body{{font-family:Inter,-apple-system,sans-serif;background:#f8fafc;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.card{{background:white;border-radius:16px;padding:40px;max-width:480px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.08)}}
.check{{font-size:3rem;margin-bottom:12px}}
h1{{font-size:1.3rem;color:#1a202c;margin-bottom:8px}}
p{{color:#718096;font-size:0.9rem;line-height:1.6}}
.btn{{display:inline-block;margin-top:20px;padding:12px 24px;background:#3b82f6;color:white;border-radius:8px;text-decoration:none;font-weight:500}}
.btn:hover{{background:#2563eb}}
.info{{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:12px;margin-top:16px;font-size:0.82rem;color:#166534}}
</style></head><body>
<div class="card">
  <div class="check">&#10003;</div>
  <h1>Dropbox Connected</h1>
  <p>CaseCore can now access your Dropbox files for evidence intake.</p>
  <div class="info">Account: {response.account_id or 'Connected'}</div>
  <a class="btn" href="/api/v1/cloud/dropbox/files">Browse Files</a>
</div>
</body></html>""")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


@router.get("/cloud/{provider}/connections")
def list_connections(provider: str) -> dict:
    """List active connections for a provider."""
    try:
        prov_enum = CloudProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    manager = get_cloud_storage_manager()
    connections = manager.list_connections(prov_enum)

    return {
        "success": True,
        "correlation_id": new_id(),
        "provider": provider,
        "count": len(connections),
        "connections": [
            ConnectionInfo(
                connection_id=c.connection_id,
                provider=c.provider.value,
                account_id=c.account_id,
                email=c.email,
                created_at=c.created_at.isoformat(),
            ).model_dump()
            for c in connections
        ],
    }


@router.get("/cloud/{provider}/files")
def browse_files(
    provider: str,
    path: str = Query(default="/", description="Path to browse"),
    connection_id: Optional[str] = Query(default=None, description="Connection ID (uses first if not specified)"),
) -> ListFilesResponse:
    """
    List files in cloud storage.

    Args:
        provider: Provider name
        path: Path to browse (e.g., "/", "/My Folder")
        connection_id: Connection ID (if not specified, uses the first active connection)

    Returns:
        ListFilesResponse with file entries
    """
    try:
        prov_enum = CloudProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    manager = get_cloud_storage_manager()

    # Get connection
    if connection_id:
        try:
            conn = manager.get_connection(connection_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Connection not found: {connection_id}")
    else:
        # Use first available connection
        conns = manager.list_connections(prov_enum)
        if not conns:
            raise HTTPException(status_code=404, detail=f"No active connections for {provider}")
        connection_id = conns[0].connection_id

    try:
        entries = manager.list_files_in_connection(connection_id, path)

        return ListFilesResponse(
            success=True,
            correlation_id=new_id(),
            provider=provider,
            path=path,
            count=len(entries),
            files=[
                FileEntryResponse(
                    name=e.name,
                    path=e.path,
                    file_id=e.file_id,
                    size=e.size,
                    is_dir=e.is_dir,
                    extension=e.extension,
                    file_type=e.file_type.value,
                    modified=e.modified,
                )
                for e in entries
            ],
        )

    except Exception as e:
        logger.error(f"File browse error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.post("/cloud/{provider}/import")
def import_file(provider: str, request: ImportFileRequest) -> ImportFileResponse:
    """
    Import a single file from cloud storage as evidence.

    If the file is a video (MP4, MOV, etc.):
      1. Downloads from cloud
      2. Extracts audio and transcribes
      3. Captures key frames
      4. Returns transcript + frames + metadata

    If the file is a document/image:
      1. Downloads from cloud
      2. Ingests through evidence pipeline
      3. Returns extracted content + evidence metadata

    Args:
        provider: Provider name
        request: ImportFileRequest with file_path and case_id

    Returns:
        ImportFileResponse with results
    """
    try:
        prov_enum = CloudProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    manager = get_cloud_storage_manager()
    evidence_svc = get_evidence_svc()
    engine = get_engine()
    video_proc = get_video_processor()

    correlation_id = new_id()

    try:
        # Get connection
        conns = manager.list_connections(prov_enum)
        if not conns:
            raise HTTPException(status_code=404, detail=f"No active connection for {provider}")
        connection_id = conns[0].connection_id

        # Download file
        logger.info(f"Downloading {request.file_path} from {provider}")
        dl_result = manager.download_file_from_connection(
            connection_id,
            request.file_id or request.file_path,
            request.file_path,
        )

        filename = dl_result.filename
        logger.info(f"Downloaded {filename} ({dl_result.size} bytes)")

        # Determine file type
        from src.services.cloud_storage import detect_file_type
        file_type = detect_file_type(filename)

        # Process based on file type
        if file_type == FileType.VIDEO:
            # Save to temp file and process
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", delete=False) as tmp:
                tmp.write(dl_result.data)
                tmp_path = tmp.name

            try:
                logger.info(f"Processing video {filename}")
                video_result = video_proc.process_for_intake(tmp_path, request.case_id)

                # Feed transcript into intake if available
                intake = engine.get_intake_by_case(request.case_id)
                intake_id = intake.intake_id if intake else None

                response_text = ""
                if video_result.transcript:
                    response_text = f"[Video Evidence: {filename}]\n\nTranscript:\n{video_result.transcript}"
                if video_result.frame_paths:
                    response_text += f"\n\n[{len(video_result.frame_paths)} frames captured]"

                if intake and response_text:
                    try:
                        engine.respond(
                            intake_id=intake.intake_id,
                            session_id=intake.interview_session_id,
                            message=response_text[:5000],
                            role=request.actor,
                        )
                    except Exception as e:
                        logger.warning(f"Could not feed video to intake: {e}")

                return ImportFileResponse(
                    success=True,
                    correlation_id=correlation_id,
                    file_path=request.file_path,
                    filename=filename,
                    video_id=video_result.video_id,
                    evidence_id=None,
                    video_processing_result={
                        "duration_seconds": video_result.video_metadata.duration,
                        "has_audio": video_result.has_audio,
                        "transcript_length": len(video_result.transcript) if video_result.transcript else 0,
                        "frames_captured": len(video_result.frame_paths),
                        "processing_seconds": video_result.processing_duration_seconds,
                    },
                )

            finally:
                try:
                    import os
                    os.unlink(tmp_path)
                except Exception:
                    pass

        else:
            # Document/image — use evidence pipeline
            intake = engine.get_intake_by_case(request.case_id)
            intake_id = intake.intake_id if intake else None

            evidence = evidence_svc.ingest_bytes(
                data=dl_result.data,
                filename=filename,
                case_id=request.case_id,
                intake_id=intake_id,
                actor=request.actor,
            )

            # Feed to intake if available
            if intake and evidence.extracted_content and evidence.extracted_content.full_text:
                try:
                    engine.respond(
                        intake_id=intake.intake_id,
                        session_id=intake.interview_session_id,
                        message=f"[Imported file: {filename}]\n\n{evidence.extracted_content.full_text[:5000]}",
                        role=request.actor,
                    )
                except Exception:
                    pass

            return ImportFileResponse(
                success=True,
                correlation_id=correlation_id,
                file_path=request.file_path,
                filename=filename,
                evidence_id=evidence.evidence_id,
                pipeline_summary={
                    "hash": evidence.metadata.sha256_hash,
                    "type_detected": evidence.metadata.file_type.value,
                    "text_length": len(evidence.extracted_content.full_text) if evidence.extracted_content else 0,
                    "burden_elements_mapped": len(evidence.burden_element_mappings),
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import error: {e}")
        return ImportFileResponse(
            success=False,
            correlation_id=correlation_id,
            file_path=request.file_path,
            filename=request.file_path.split("/")[-1],
            error=str(e),
        )


@router.post("/cloud/{provider}/import-async")
def import_file_async(provider: str, request: ImportFileRequest):
    """
    Start an async file import. Returns a job_id immediately.
    Poll GET /cloud/jobs/{job_id} for progress (0-100%).

    Progress stages:
      0-40%   Downloading from cloud
      40-55%  Extracting audio
      55-85%  Transcribing with Whisper
      85-95%  Capturing key frames
      95-100% Feeding into intake
    """
    try:
        prov_enum = CloudProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    job_id = new_id()
    file_name = request.file_path.split("/")[-1]

    _import_jobs[job_id] = {
        "job_id": job_id,
        "file_path": request.file_path,
        "filename": file_name,
        "case_id": request.case_id,
        "status": "queued",
        "stage": "queued",
        "progress": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    def _run_import():
        try:
            import tempfile as tf
            import time
            manager = get_cloud_storage_manager()
            video_proc = get_video_processor()
            vault = get_evidence_vault()

            # Stage: downloading (0-40%)
            _update_job(job_id, status="running", stage="downloading", progress=5)
            conns = manager.list_connections(prov_enum)
            if not conns:
                raise RuntimeError(f"No active connection for {provider}")
            connection_id = conns[0].connection_id

            _update_job(job_id, progress=10)
            dl_result = manager.download_file_from_connection(
                connection_id,
                request.file_id or request.file_path,
                request.file_path,
            )
            filename = dl_result.filename
            logger.info(f"[Job {job_id}] Downloaded {filename} ({dl_result.size} bytes)")

            # Write to temp file for hashing
            ext = f".{filename.split('.')[-1]}" if '.' in filename else ""
            with tf.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(dl_result.data)
                tmp_path = tmp.name

            # ============================================================
            # VAULT: Hash raw file BEFORE any processing
            # ============================================================
            _update_job(job_id, progress=35, stage="hashing")
            cloud_source = f"{provider}:{request.file_path}"

            try:
                from src.services.cloud_storage import detect_file_type
                file_type = detect_file_type(filename)
                import mimetypes
                mime = mimetypes.guess_type(filename)[0]

                source_record, is_new = vault.ingest_source(
                    file_path=tmp_path,
                    case_id=request.case_id,
                    original_filename=filename,
                    actor=request.actor,
                    cloud_source=cloud_source,
                    mime_type=mime,
                )
                evidence_id = source_record.evidence_id
                sha256 = source_record.sha256
                _update_job(job_id, progress=40, stage="hashed",
                            evidence_id=evidence_id, sha256=sha256[:16])

                # DEDUP: If file already exists, skip ALL processing
                if not is_new:
                    logger.info(f"[Job {job_id}] DEDUP HIT — {filename} already in vault as {evidence_id}")
                    existing_derivs = vault.list_derivations(source_evidence_id=evidence_id)
                    transcript_deriv = next(
                        (d for d in existing_derivs if d.artifact_type == "transcript"), None
                    )
                    transcript_preview = ""
                    if transcript_deriv and transcript_deriv.artifact_inline:
                        transcript_preview = transcript_deriv.artifact_inline[:200]
                    elif transcript_deriv and transcript_deriv.artifact_path:
                        art_path = vault.get_derivation_artifact_path(transcript_deriv.derivation_id)
                        if art_path and os.path.exists(art_path):
                            with open(art_path, "r") as f:
                                transcript_preview = f.read(200)

                    _update_job(job_id, progress=100, status="completed", stage="dedup",
                                completed_at=datetime.now(timezone.utc).isoformat(),
                                result={
                                    "dedup": True,
                                    "evidence_id": evidence_id,
                                    "sha256": sha256,
                                    "existing_derivations": len(existing_derivs),
                                    "transcript_preview": transcript_preview,
                                    "message": "File already processed — skipped Whisper (no charge)",
                                })
                    try: os.unlink(tmp_path)
                    except: pass
                    return

                # ============================================================
                # NEW FILE — Full processing pipeline with vault storage
                # ============================================================
                # Use the vault copy for all processing (raw file is preserved)
                vault_file_path = vault.get_source_path(evidence_id)

                if file_type == FileType.VIDEO:
                    t0 = time.time()

                    # Stage: extracting audio (40-55%)
                    _update_job(job_id, stage="extracting_audio", progress=42)
                    metadata = video_proc.probe(vault_file_path)

                    # Store metadata as a derivation
                    vault.add_derivation(
                        source_evidence_id=evidence_id,
                        method=DerivationMethod.FFPROBE_METADATA,
                        method_version=f"ffprobe-{video_proc.ffprobe_path}",
                        artifact_type="video_metadata",
                        artifact_text=json.dumps(metadata.model_dump(), default=str),
                        parameters={"probe_path": vault_file_path},
                        processing_seconds=time.time() - t0,
                    )
                    _update_job(job_id, progress=45)

                    audio_path = None
                    audio_derivation_id = None
                    if metadata.has_audio:
                        t1 = time.time()
                        audio_tmp = tf.NamedTemporaryFile(suffix=".wav", delete=False)
                        audio_path = audio_tmp.name
                        audio_tmp.close()
                        video_proc.extract_audio(vault_file_path, audio_path)

                        # Store audio extraction as derivation
                        audio_deriv = vault.add_derivation(
                            source_evidence_id=evidence_id,
                            method=DerivationMethod.FFMPEG_AUDIO_EXTRACT,
                            method_version=f"ffmpeg-{video_proc.ffmpeg_path}",
                            artifact_type="audio_wav",
                            artifact_file=audio_path,
                            parameters={
                                "sample_rate": 16000,
                                "channels": 1,
                                "codec": "pcm_s16le",
                            },
                            processing_seconds=time.time() - t1,
                        )
                        audio_derivation_id = audio_deriv.derivation_id

                    _update_job(job_id, progress=55, stage="audio_extracted")

                    # Stage: transcribing (55-85%)
                    transcript = ""
                    if audio_path and os.path.exists(audio_path):
                        t2 = time.time()
                        _update_job(job_id, stage="transcribing", progress=58)
                        transcript = video_proc.transcribe_audio(audio_path)

                        # Store transcript as derivation (chained from audio)
                        vault.add_derivation(
                            source_evidence_id=evidence_id,
                            method=DerivationMethod.WHISPER_TRANSCRIPTION,
                            method_version="whisper-1",
                            artifact_type="transcript",
                            artifact_text=transcript,
                            parent_derivation_id=audio_derivation_id,
                            parameters={
                                "model": "whisper-1",
                                "language": "en",
                                "audio_size_bytes": os.path.getsize(audio_path),
                            },
                            source_time_start=0.0,
                            source_time_end=metadata.duration,
                            confidence=0.90,
                            processing_seconds=time.time() - t2,
                        )
                        _update_job(job_id, progress=85, stage="transcribed")
                    else:
                        _update_job(job_id, progress=85, stage="no_audio")

                    # Stage: capturing frames (85-95%)
                    _update_job(job_id, stage="capturing_frames", progress=87)
                    t3 = time.time()
                    interval = max(1, metadata.duration / 10)
                    frame_paths = video_proc.capture_frames(vault_file_path,
                                                            interval_seconds=interval)

                    # Store each frame as a derivation
                    for i, fp in enumerate(frame_paths):
                        timestamp = i * interval
                        vault.add_derivation(
                            source_evidence_id=evidence_id,
                            method=DerivationMethod.FFMPEG_FRAME_CAPTURE,
                            method_version=f"ffmpeg-{video_proc.ffmpeg_path}",
                            artifact_type="frame_png",
                            artifact_file=fp,
                            parameters={
                                "interval_seconds": interval,
                                "frame_index": i,
                            },
                            source_time_start=timestamp,
                            source_time_end=timestamp,
                            processing_seconds=(time.time() - t3) / max(len(frame_paths), 1),
                        )
                    _update_job(job_id, progress=95, stage="frames_captured")

                    # Stage: feeding intake (95-100%)
                    _update_job(job_id, stage="feeding_intake", progress=96)
                    engine = get_engine()
                    intake = engine.get_intake_by_case(request.case_id) if request.case_id else None
                    if intake and transcript:
                        try:
                            engine.respond(
                                intake_id=intake.intake_id,
                                session_id=intake.interview_session_id,
                                message=f"[Video Evidence: {filename}]\n\nTranscript:\n{transcript[:5000]}",
                                role=request.actor,
                            )
                        except Exception as e:
                            logger.warning(f"Could not feed video to intake: {e}")

                    _update_job(job_id, progress=100, status="completed", stage="done",
                                completed_at=datetime.now(timezone.utc).isoformat(),
                                result={
                                    "evidence_id": evidence_id,
                                    "sha256": sha256,
                                    "duration_seconds": metadata.duration,
                                    "has_audio": metadata.has_audio,
                                    "transcript_length": len(transcript),
                                    "frames_captured": len(frame_paths),
                                    "transcript_preview": transcript[:200] if transcript else "",
                                    "vault_derivations": len(vault.list_derivations(
                                        source_evidence_id=evidence_id)),
                                })

                    # Cleanup audio temp (frames were copied into vault)
                    if audio_path:
                        try: os.unlink(audio_path)
                        except: pass
                    # Clean up temp frame files (now in vault)
                    for fp in frame_paths:
                        try: os.unlink(fp)
                        except: pass

                else:
                    # Non-video file — ingest into vault (already done above),
                    # content extraction happens through evidence_ingestion service
                    _update_job(job_id, stage="processing", progress=60)
                    _update_job(job_id, progress=100, status="completed", stage="done",
                                completed_at=datetime.now(timezone.utc).isoformat(),
                                result={
                                    "evidence_id": evidence_id,
                                    "sha256": sha256,
                                    "type": "document",
                                    "size": dl_result.size,
                                })

            finally:
                try: os.unlink(tmp_path)
                except: pass

        except Exception as e:
            logger.error(f"[Job {job_id}] Import error: {e}")
            _update_job(job_id, status="error", stage="error",
                        error=str(e),
                        completed_at=datetime.now(timezone.utc).isoformat())

    # Start background thread
    thread = threading.Thread(target=_run_import, daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "queued", "file_path": request.file_path}


@router.get("/cloud/jobs/{job_id}")
def get_job_status(job_id: str):
    """Get progress for an async import job. Returns 0-100 progress."""
    if job_id not in _import_jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return _import_jobs[job_id]


@router.get("/cloud/jobs")
def list_jobs():
    """List all import jobs."""
    return {"jobs": list(_import_jobs.values())}


@router.get("/vault/stats")
def vault_stats():
    """Get evidence vault statistics."""
    vault = get_evidence_vault()
    return vault.stats()


@router.get("/vault/sources")
def vault_sources(case_id: Optional[str] = Query(default=None)):
    """List all source evidence files in the vault."""
    vault = get_evidence_vault()
    sources = vault.list_sources(case_id)
    return {
        "count": len(sources),
        "sources": [s.model_dump() for s in sources],
    }


@router.get("/vault/provenance/{evidence_id}")
def vault_provenance(evidence_id: str):
    """
    Get full provenance chain for a source evidence file.
    Shows all derivations (transcripts, frames, metadata) linked to it.
    """
    vault = get_evidence_vault()
    source = vault._sources.get(evidence_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Evidence not found: {evidence_id}")

    derivations = vault.list_derivations(source_evidence_id=evidence_id)
    theories = [t for t in vault._theories.values()
                if evidence_id in t.source_evidence_ids]

    return {
        "source": source.model_dump(),
        "derivations": [d.model_dump() for d in derivations],
        "theories": [t.model_dump() for t in theories],
        "chain_summary": {
            "sha256": source.sha256,
            "original_file": source.original_filename,
            "derivation_count": len(derivations),
            "theory_count": len(theories),
            "methods_used": list(set(d.method for d in derivations)),
        },
    }


@router.post("/cloud/{provider}/import-batch")
def import_batch(provider: str, request: ImportBatchRequest) -> ImportBatchResponse:
    """
    Import multiple files from cloud storage.

    Processes files sequentially to avoid overwhelming the system.
    Returns results for each file.

    Args:
        provider: Provider name
        request: ImportBatchRequest with file_paths and case_id

    Returns:
        ImportBatchResponse with results for each file
    """
    correlation_id = new_id()
    results = []
    imported = 0
    failed = 0

    for file_path in request.file_paths:
        try:
            result = import_file(
                provider,
                ImportFileRequest(
                    file_path=file_path,
                    case_id=request.case_id,
                    actor=request.actor,
                ),
            )

            results.append(result)
            if result.success:
                imported += 1
            else:
                failed += 1

        except Exception as e:
            logger.error(f"Batch import error for {file_path}: {e}")
            failed += 1
            results.append(ImportFileResponse(
                success=False,
                correlation_id=correlation_id,
                file_path=file_path,
                filename=file_path.split("/")[-1],
                error=str(e),
            ))

    return ImportBatchResponse(
        success=True,
        correlation_id=correlation_id,
        case_id=request.case_id,
        total=len(request.file_paths),
        imported=imported,
        failed=failed,
        results=results,
    )


@router.delete("/cloud/{provider}/disconnect")
def disconnect(provider: str, connection_id: str = Query(...)) -> DisconnectResponse:
    """
    Disconnect a cloud storage connection and revoke the token.

    Args:
        provider: Provider name
        connection_id: Connection ID to disconnect

    Returns:
        DisconnectResponse confirming disconnection
    """
    try:
        prov_enum = CloudProvider(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    manager = get_cloud_storage_manager()

    try:
        success = manager.disconnect(connection_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Connection not found: {connection_id}")

        logger.info(f"Disconnected {provider} connection {connection_id}")

        return DisconnectResponse(
            success=True,
            provider=provider,
            connection_id=connection_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disconnect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
