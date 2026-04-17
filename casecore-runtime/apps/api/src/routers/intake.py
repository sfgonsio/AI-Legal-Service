"""
INTAKE_ENGINE API Router — Phase 2 Endpoints

Endpoints:
  POST /cases/{case_id}/intake/start         — Begin intake with narrative
  POST /cases/{case_id}/intake/respond        — Client/attorney follow-up response
  POST /cases/{case_id}/intake/audio          — Submit audio for transcription + intake
  POST /cases/{case_id}/intake/evidence       — Submit file evidence (video, doc, image, etc.)
  GET  /cases/{case_id}/intake/evidence       — List all ingested evidence for case
  GET  /cases/{case_id}/intake/evidence/{id}  — Get single evidence record with chain of custody
  GET  /cases/{case_id}/intake                — Get current intake state
  GET  /cases/{case_id}/intake/gaps           — Get gap summary + suggested questions
  GET  /cases/{case_id}/intake/coa            — Get COA assessment + burden scorecard
  POST /cases/{case_id}/intake/complete       — Mark intake as complete
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional

from src.schemas.intake import (
    StartIntakeRequest,
    StartIntakeResponse,
    RespondIntakeRequest,
    RespondIntakeResponse,
    GetIntakeResponse,
    GetIntakeGapsResponse,
    CompleteIntakeRequest,
    CompleteIntakeResponse,
    IntakeGapSummary,
)
from src.schemas.common import StandardResponse
from src.services.intake_engine import IntakeEngine
from src.services.interview_agent import InterviewAgent, LLMProvider
from src.services.coa_engine import COAMatcher, BurdenTracker, QuestionGenerator
from src.services.audio_transcription import WhisperTranscriptionService
from src.services.evidence_ingestion import EvidenceIngestionService
from src.services.case_analyzer import get_case_analyzer, CaseAnalyzer
from src.utils.ids import new_id

router = APIRouter(tags=["intake"])

# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------

_engine: IntakeEngine | None = None
_coa_matcher: COAMatcher | None = None
_burden_tracker: BurdenTracker | None = None
_question_gen: QuestionGenerator | None = None
_whisper: WhisperTranscriptionService | None = None
_evidence_svc: EvidenceIngestionService | None = None
_llm: LLMProvider | None = None

# Environment-aware paths
import os
try:
    from config.environments import get_data_paths, get_environment
    _env_paths = get_data_paths()
    CANONICAL_BASE = _env_paths["canonical_store"]
    EVIDENCE_STORAGE = _env_paths["evidence_storage"]
    IS_SANDBOX = _env_paths["is_sandbox"]
except ImportError:
    CANONICAL_BASE = os.getenv(
        "CASECORE_CANONICAL_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "legal", "canonical")
    )
    EVIDENCE_STORAGE = os.getenv("CASECORE_EVIDENCE_STORAGE", "/tmp/casecore_evidence")
    IS_SANDBOX = os.getenv("CASECORE_ENV", "sandbox") == "sandbox"


def get_llm() -> LLMProvider:
    global _llm
    if _llm is None:
        _llm = LLMProvider()
    return _llm


def get_engine() -> IntakeEngine:
    global _engine
    if _engine is None:
        _engine = IntakeEngine()
    return _engine


def get_coa_matcher() -> COAMatcher:
    global _coa_matcher
    if _coa_matcher is None:
        _coa_matcher = COAMatcher(
            canonical_base_path=CANONICAL_BASE,
            llm_provider=get_llm(),
        )
    return _coa_matcher


def get_burden_tracker() -> BurdenTracker:
    global _burden_tracker
    if _burden_tracker is None:
        _burden_tracker = BurdenTracker()
    return _burden_tracker


def get_question_gen() -> QuestionGenerator:
    global _question_gen
    if _question_gen is None:
        _question_gen = QuestionGenerator(llm_provider=get_llm())
    return _question_gen


def get_whisper() -> WhisperTranscriptionService:
    global _whisper
    if _whisper is None:
        _whisper = WhisperTranscriptionService()
    return _whisper


def get_evidence_svc() -> EvidenceIngestionService:
    global _evidence_svc
    if _evidence_svc is None:
        _evidence_svc = EvidenceIngestionService(
            storage_base=EVIDENCE_STORAGE,
            whisper_service=get_whisper(),
            llm_provider=get_llm(),
            burden_tracker=get_burden_tracker(),
        )
    return _evidence_svc


# ---------------------------------------------------------------------------
# POST /cases/{case_id}/intake/start
# ---------------------------------------------------------------------------

@router.post("/cases/{case_id}/intake/start", response_model=StartIntakeResponse)
def start_intake(
    case_id: str,
    body: StartIntakeRequest,
    engine: IntakeEngine = Depends(get_engine),
    coa_matcher: COAMatcher = Depends(get_coa_matcher),
    tracker: BurdenTracker = Depends(get_burden_tracker),
    qgen: QuestionGenerator = Depends(get_question_gen),
):
    """
    Start a new intake session.

    Flow:
      1. Capture narrative (immutable)
      2. Parse narrative into structured model (parties, events, gaps)
      3. Match narrative to candidate Causes of Action
      4. Extract burden elements for each COA
      5. Generate targeted questions based on burden gaps
    """
    # Step 1-2: Standard intake start
    intake, session_id, generic_questions = engine.start_intake(
        case_id=case_id,
        narrative=body.narrative,
        client_name=body.client_name,
        incident_date=body.incident_date,
        case_type_hint=body.case_type_hint,
        jurisdiction_hint=body.jurisdiction_hint,
    )

    # Step 3-4: COA matching and burden tracking
    targeted_questions = generic_questions  # fallback
    try:
        case_context = None
        if intake.case_context:
            case_context = intake.case_context.model_dump()

        matched_coas = coa_matcher.match_narrative(body.narrative, case_context)
        assessment = tracker.create_assessment(case_id, matched_coas)

        # Step 5: Generate legally-targeted questions from burden gaps
        gap_elements = tracker.get_gap_elements(case_id)
        if gap_elements and assessment.causes_of_action:
            targeted = qgen.generate_targeted_questions(
                gap_elements=gap_elements,
                coa_context=assessment.causes_of_action,
                conversation_history=[{"role": "client", "content": body.narrative}],
                max_questions=5,
            )
            if targeted:
                targeted_questions = [q["question"] for q in targeted]

    except Exception:
        # COA matching failed — fall back to generic questions
        pass

    return StartIntakeResponse(
        correlation_id=new_id(),
        intake=intake,
        interview_session_id=session_id,
        initial_questions=targeted_questions,
    )


# ---------------------------------------------------------------------------
# POST /cases/{case_id}/intake/respond
# ---------------------------------------------------------------------------

@router.post("/cases/{case_id}/intake/respond", response_model=RespondIntakeResponse)
def respond_intake(
    case_id: str,
    body: RespondIntakeRequest,
    engine: IntakeEngine = Depends(get_engine),
    tracker: BurdenTracker = Depends(get_burden_tracker),
    qgen: QuestionGenerator = Depends(get_question_gen),
):
    """
    Submit a follow-up response from the client or attorney.

    The response is:
      1. Refined into the structured model
      2. Mapped against burden elements (evidence strength assessment)
      3. Used to generate next round of targeted questions
    """
    intake = engine.get_intake_by_case(case_id)
    if not intake:
        raise HTTPException(status_code=404, detail=f"No intake found for case {case_id}")

    # Standard refinement
    updated, follow_up, new_gaps, resolved = engine.respond(
        intake_id=intake.intake_id,
        session_id=body.session_id,
        message=body.message,
        role=body.role,
    )

    # Map response to burden elements
    try:
        tracker.map_response_to_elements(case_id, body.message, get_llm())

        # Generate targeted questions from remaining gaps
        gap_elements = tracker.get_gap_elements(case_id)
        assessment = tracker.get_assessment(case_id)
        if gap_elements and assessment and assessment.causes_of_action:
            targeted = qgen.generate_targeted_questions(
                gap_elements=gap_elements,
                coa_context=assessment.causes_of_action,
                conversation_history=[
                    {"role": body.role, "content": body.message},
                ],
                max_questions=3,
            )
            if targeted:
                follow_up = [q["question"] for q in targeted]
    except Exception:
        pass

    return RespondIntakeResponse(
        correlation_id=new_id(),
        intake=updated,
        follow_up_questions=follow_up,
        new_gaps_detected=new_gaps,
        gaps_resolved=resolved,
    )


# ---------------------------------------------------------------------------
# POST /cases/{case_id}/intake/audio
# ---------------------------------------------------------------------------

@router.post("/cases/{case_id}/intake/audio")
async def submit_audio(
    case_id: str,
    audio: UploadFile = File(...),
    speaker: str = Form(default="client"),
    engine: IntakeEngine = Depends(get_engine),
    whisper: WhisperTranscriptionService = Depends(get_whisper),
    coa_matcher: COAMatcher = Depends(get_coa_matcher),
    tracker: BurdenTracker = Depends(get_burden_tracker),
    qgen: QuestionGenerator = Depends(get_question_gen),
):
    """
    Submit an audio file for transcription and intake processing.

    Flow:
      1. Transcribe audio via Whisper API
      2. If no active intake: start new intake with transcript as narrative
      3. If active intake: treat transcript as a response (refine model)
      4. Map to COA burden elements
      5. Return transcript + follow-up questions

    Supports: wav, mp3, m4a, webm, mp4, ogg, flac
    """
    # Read audio data
    audio_data = await audio.read()

    # Determine format from filename
    fmt = "webm"
    if audio.filename:
        ext = audio.filename.rsplit(".", 1)[-1].lower()
        if ext in WhisperTranscriptionService.SUPPORTED_FORMATS:
            fmt = ext

    # Check for existing intake
    existing = engine.get_intake_by_case(case_id)

    # Transcribe
    session_id = existing.interview_session_id if existing else new_id()
    transcript = whisper.transcribe_bytes(
        audio_data=audio_data,
        case_id=case_id,
        session_id=session_id,
        format=fmt,
        speaker=speaker,
    )

    if not existing:
        # New intake — use transcript as initial narrative
        intake, session_id, questions = engine.start_intake(
            case_id=case_id,
            narrative=transcript.full_text,
        )

        # COA matching
        try:
            matched = coa_matcher.match_narrative(transcript.full_text)
            tracker.create_assessment(case_id, matched)
            gap_elements = tracker.get_gap_elements(case_id)
            assessment = tracker.get_assessment(case_id)
            if gap_elements and assessment and assessment.causes_of_action:
                targeted = qgen.generate_targeted_questions(
                    gap_elements=gap_elements,
                    coa_context=assessment.causes_of_action,
                    conversation_history=[{"role": "client", "content": transcript.full_text}],
                )
                if targeted:
                    questions = [q["question"] for q in targeted]
        except Exception:
            pass

        return {
            "success": True,
            "correlation_id": new_id(),
            "action": "intake_started",
            "transcript": transcript.model_dump(),
            "intake": intake.model_dump(),
            "interview_session_id": session_id,
            "follow_up_questions": questions,
        }

    else:
        # Existing intake — treat as response
        updated, follow_up, new_gaps, resolved = engine.respond(
            intake_id=existing.intake_id,
            session_id=existing.interview_session_id,
            message=transcript.full_text,
            role=speaker,
        )

        try:
            tracker.map_response_to_elements(case_id, transcript.full_text, get_llm())
            gap_elements = tracker.get_gap_elements(case_id)
            assessment = tracker.get_assessment(case_id)
            if gap_elements and assessment and assessment.causes_of_action:
                targeted = qgen.generate_targeted_questions(
                    gap_elements=gap_elements,
                    coa_context=assessment.causes_of_action,
                    conversation_history=[{"role": speaker, "content": transcript.full_text}],
                )
                if targeted:
                    follow_up = [q["question"] for q in targeted]
        except Exception:
            pass

        return {
            "success": True,
            "correlation_id": new_id(),
            "action": "intake_refined",
            "transcript": transcript.model_dump(),
            "intake": updated.model_dump(),
            "follow_up_questions": follow_up,
            "new_gaps_detected": new_gaps,
            "gaps_resolved": resolved,
        }


# ---------------------------------------------------------------------------
# POST /cases/{case_id}/intake/evidence — File evidence ingestion
# ---------------------------------------------------------------------------

@router.post("/cases/{case_id}/intake/evidence")
async def submit_evidence_file(
    case_id: str,
    file: UploadFile = File(...),
    actor: str = Form(default="client"),
    evidence_svc: EvidenceIngestionService = Depends(get_evidence_svc),
    engine: IntakeEngine = Depends(get_engine),
    tracker: BurdenTracker = Depends(get_burden_tracker),
):
    """
    Submit a file as evidence for intake processing.

    Full pipeline:
      1. HASH — SHA-256 fingerprint in the evidence vault (dedup check)
      2. CLASSIFY — Determine file type (video, audio, document, image, etc.)
      3. EXTRACT — Pull content (transcript, text, OCR, structured data)
      4. TIMELINE — Tag dates, durations, temporal references
      5. MAP — Map extracted content to COA burden elements
      6. REGISTER — Create evidence record with provenance chain

    Supports: video (mp4, mov, avi, mkv, webm), audio (mp3, wav, m4a),
              documents (pdf, docx, txt), images (jpg, png, tiff),
              spreadsheets (xlsx, csv), email (eml, msg)
    """
    import tempfile
    from src.services.evidence_vault import get_evidence_vault, DerivationMethod

    file_data = await file.read()
    filename = file.filename or "unknown_file"

    # ---- VAULT REGISTRATION (P3: Evidence Registration) ----
    # Write to temp file so we can hash and store in vault
    vault = get_evidence_vault()
    vault_record = None
    is_new = True
    tmp_path = None

    try:
        ext = os.path.splitext(filename)[1].lower()
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        vault_record, is_new = vault.ingest_source(
            file_path=tmp_path,
            case_id=case_id,
            original_filename=filename,
            actor=actor,
            mime_type=file.content_type,
        )
    except Exception as vault_err:
        import logging
        logging.getLogger(__name__).warning(f"Vault registration failed (continuing): {vault_err}")

    # ---- FULL INGESTION PIPELINE ----
    # Find or reference intake
    intake = engine.get_intake_by_case(case_id)
    intake_id = intake.intake_id if intake else None

    # Run full ingestion pipeline (classification, extraction, timeline, burden mapping)
    evidence = evidence_svc.ingest_bytes(
        data=file_data,
        filename=filename,
        case_id=case_id,
        intake_id=intake_id,
        actor=actor,
    )

    # ---- VAULT DERIVATION: store extracted text as a derivation linked to source ----
    if vault_record and is_new and evidence.extracted_content and evidence.extracted_content.full_text:
        try:
            content_text = evidence.extracted_content.full_text
            # Determine derivation method from file type
            type_method_map = {
                'video': DerivationMethod.WHISPER_TRANSCRIPTION,
                'audio': DerivationMethod.WHISPER_TRANSCRIPTION,
                'document': DerivationMethod.TEXT_EXTRACTION,
                'spreadsheet': DerivationMethod.TEXT_EXTRACTION,
                'image': DerivationMethod.OCR_EXTRACTION,
                'email': DerivationMethod.TEXT_EXTRACTION,
            }
            file_type_str = evidence.metadata.file_type.value if hasattr(evidence.metadata, 'file_type') else 'document'
            method = type_method_map.get(file_type_str, DerivationMethod.TEXT_EXTRACTION)

            vault.add_derivation(
                source_evidence_id=vault_record.evidence_id,
                method=method,
                method_version="evidence_ingestion_v1",
                artifact_type="transcript" if method == DerivationMethod.WHISPER_TRANSCRIPTION else "extracted_text",
                artifact_text=content_text[:50000],  # Cap at 50KB for inline storage
                parameters={
                    "file_type": file_type_str,
                    "text_length": len(content_text),
                    "extraction_method": "evidence_ingestion_service",
                },
            )
        except Exception as deriv_err:
            import logging
            logging.getLogger(__name__).warning(f"Vault derivation failed (continuing): {deriv_err}")

    # Clean up temp file
    if tmp_path:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    # If content was extracted and an intake exists, also feed it as a response
    if intake and evidence.extracted_content and evidence.extracted_content.full_text:
        try:
            engine.respond(
                intake_id=intake.intake_id,
                session_id=intake.interview_session_id,
                message=f"[Evidence file: {filename}]\n\n{evidence.extracted_content.full_text[:5000]}",
                role=actor,
            )
        except Exception:
            pass

    # Build response with scorecard
    scorecard = tracker.get_scorecard(case_id) if tracker else {}

    return {
        "success": True,
        "correlation_id": new_id(),
        "evidence": evidence.model_dump(),
        "vault_registered": vault_record is not None,
        "vault_is_new": is_new,
        "vault_evidence_id": vault_record.evidence_id if vault_record else None,
        "pipeline_summary": {
            "hash": evidence.metadata.sha256_hash,
            "type_detected": evidence.metadata.file_type.value,
            "content_extracted": evidence.extracted_content is not None,
            "text_length": len(evidence.extracted_content.full_text) if evidence.extracted_content else 0,
            "timeline_tags": len(evidence.timeline_tags),
            "burden_elements_mapped": len(evidence.burden_element_mappings),
            "chain_of_custody_entries": len(evidence.chain_of_custody),
        },
        "coa_scorecard": scorecard,
    }


# ---------------------------------------------------------------------------
# GET /cases/{case_id}/intake/evidence — List all evidence
# ---------------------------------------------------------------------------

@router.get("/cases/{case_id}/intake/evidence")
def list_evidence(
    case_id: str,
    evidence_svc: EvidenceIngestionService = Depends(get_evidence_svc),
):
    """List all ingested evidence for a case with summary metadata."""
    items = evidence_svc.list_evidence(case_id)
    return {
        "success": True,
        "correlation_id": new_id(),
        "count": len(items),
        "evidence": [
            {
                "evidence_id": e.evidence_id,
                "filename": e.original_filename,
                "type": e.metadata.file_type.value,
                "size_bytes": e.metadata.file_size_bytes,
                "hash": e.metadata.sha256_hash,
                "status": e.status,
                "timeline_tags": len(e.timeline_tags),
                "burden_mappings": len(e.burden_element_mappings),
                "ingested_at": e.ingested_at.isoformat(),
            }
            for e in items
        ],
    }


# ---------------------------------------------------------------------------
# GET /cases/{case_id}/intake/evidence/{evidence_id}
# ---------------------------------------------------------------------------

@router.get("/cases/{case_id}/intake/evidence/{evidence_id}")
def get_evidence_detail(
    case_id: str,
    evidence_id: str,
    evidence_svc: EvidenceIngestionService = Depends(get_evidence_svc),
):
    """Get full evidence record including chain of custody and burden mappings."""
    evidence = evidence_svc.get_evidence(evidence_id)
    if not evidence or evidence.case_id != case_id:
        raise HTTPException(status_code=404, detail=f"Evidence {evidence_id} not found")

    return {
        "success": True,
        "correlation_id": new_id(),
        "evidence": evidence.model_dump(),
    }


# ---------------------------------------------------------------------------
# GET /cases/{case_id}/intake
# ---------------------------------------------------------------------------

@router.get("/cases/{case_id}/intake", response_model=GetIntakeResponse)
def get_intake(case_id: str, engine: IntakeEngine = Depends(get_engine)):
    """Get the current intake record for a case."""
    intake = engine.get_intake_by_case(case_id)
    if not intake:
        raise HTTPException(status_code=404, detail=f"No intake found for case {case_id}")

    return GetIntakeResponse(correlation_id=new_id(), intake=intake)


# ---------------------------------------------------------------------------
# GET /cases/{case_id}/intake/gaps
# ---------------------------------------------------------------------------

@router.get("/cases/{case_id}/intake/gaps", response_model=GetIntakeGapsResponse)
def get_intake_gaps(case_id: str, engine: IntakeEngine = Depends(get_engine)):
    """Get the gap summary and suggested follow-up questions."""
    intake = engine.get_intake_by_case(case_id)
    if not intake:
        raise HTTPException(status_code=404, detail=f"No intake found for case {case_id}")

    gap_summary, questions = engine.get_gaps(intake.intake_id)
    if not gap_summary:
        gap_summary = IntakeGapSummary(
            gap_summary_id=new_id(),
            case_id=case_id,
            intake_model_id="none",
            assessed_at=datetime.now(timezone.utc),
        )

    return GetIntakeGapsResponse(
        correlation_id=new_id(),
        gap_summary=gap_summary,
        suggested_questions=questions,
    )


# ---------------------------------------------------------------------------
# GET /cases/{case_id}/intake/coa
# ---------------------------------------------------------------------------

@router.get("/cases/{case_id}/intake/coa")
def get_coa_assessment(
    case_id: str,
    tracker: BurdenTracker = Depends(get_burden_tracker),
):
    """
    Get the COA assessment and burden element scorecard.

    Returns all candidate Causes of Action with:
    - Burden elements and evidence strength per element
    - Viability scores
    - Remedies available
    - Coverage percentage
    - Critical gaps remaining
    """
    assessment = tracker.get_assessment(case_id)
    if not assessment:
        raise HTTPException(status_code=404, detail=f"No COA assessment for case {case_id}")

    scorecard = tracker.get_scorecard(case_id)

    return {
        "success": True,
        "correlation_id": new_id(),
        "assessment": assessment.model_dump(),
        "scorecard": scorecard,
    }


# ---------------------------------------------------------------------------
# POST /cases/{case_id}/intake/complete
# ---------------------------------------------------------------------------

@router.post("/cases/{case_id}/intake/complete", response_model=CompleteIntakeResponse)
def complete_intake(
    case_id: str,
    body: CompleteIntakeRequest,
    engine: IntakeEngine = Depends(get_engine),
    tracker: BurdenTracker = Depends(get_burden_tracker),
):
    """
    Mark the intake as complete.

    If critical gaps remain and force_complete is False, the intake
    is escalated instead. Returns final COA scorecard with warnings.
    """
    intake = engine.get_intake_by_case(case_id)
    if not intake:
        raise HTTPException(status_code=404, detail=f"No intake found for case {case_id}")

    completed, unresolved, warnings = engine.complete_intake(
        intake_id=intake.intake_id,
        attorney_notes=body.attorney_notes,
        force_complete=body.force_complete,
    )

    return CompleteIntakeResponse(
        correlation_id=new_id(),
        intake=completed,
        unresolved_gaps=unresolved,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Case Analysis Endpoints (P4 → P5 Pipeline)
# ---------------------------------------------------------------------------

def _get_analyzer() -> CaseAnalyzer:
    return get_case_analyzer(
        canonical_base=CANONICAL_BASE,
        llm_provider=get_llm(),
    )


@router.post("/cases/{case_id}/analyze")
def run_case_analysis(case_id: str):
    """
    Run the full P4 → P5 analysis pipeline on a case.

    Takes all evidence in the vault for this case and:
      P4: Derives candidate facts from transcripts, text, metadata
      P5: Identifies COAs, maps burden elements, scores coverage

    Returns the ELEMENT_COVERAGE_MATRIX and gap analysis.

    IMPORTANT: All outputs are PROPOSAL-layer — attorney review required.
    """
    import traceback
    try:
        analyzer = _get_analyzer()
        result = analyzer.run_full_analysis(case_id)
        return {
            "success": True,
            "correlation_id": new_id(),
            **result,
        }
    except Exception as e:
        # Return structured error so the dashboard can display it
        return {
            "success": False,
            "correlation_id": new_id(),
            "case_id": case_id,
            "status": "analysis_failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "hint": _get_error_hint(e),
        }


def _get_error_hint(e: Exception) -> str:
    """Provide actionable hints for common errors."""
    msg = str(e).lower()
    if "anthropic" in msg and "install" in msg:
        return "Install the Anthropic SDK: pip install anthropic"
    if "api_key" in msg or "authentication" in msg or "unauthorized" in msg:
        return "Check ANTHROPIC_API_KEY in your .env file"
    if "rate_limit" in msg or "429" in msg:
        return "API rate limit hit. Wait a moment and retry."
    if "not found" in msg and "vault" in msg.lower():
        return "No evidence in vault for this case. Import files first via Cloud Import."
    if "module" in msg or "import" in msg:
        return f"Missing dependency: {e}. Check pip install requirements."
    return "Check server logs for details. The pipeline will return partial results where possible."


@router.get("/cases/{case_id}/analysis/facts")
def get_case_facts(case_id: str):
    """Get all derived fact candidates for a case."""
    analyzer = _get_analyzer()
    facts = analyzer.get_facts(case_id)
    events = analyzer.get_events(case_id)
    return {
        "success": True,
        "correlation_id": new_id(),
        "case_id": case_id,
        "facts": [f.model_dump() for f in facts],
        "events": [e.model_dump() for e in events],
    }


@router.get("/cases/{case_id}/analysis/matrix")
def get_coverage_matrix(case_id: str):
    """Get the element coverage matrix for a case."""
    analyzer = _get_analyzer()
    matrix = analyzer.get_matrix(case_id)
    if not matrix:
        raise HTTPException(
            status_code=404,
            detail=f"No coverage matrix for case {case_id}. Run POST /cases/{case_id}/analyze first."
        )
    return {
        "success": True,
        "correlation_id": new_id(),
        "matrix": matrix.model_dump(),
    }


# ---------------------------------------------------------------------------
# P7 — Attorney Review: COA Approve / Dismiss
# ---------------------------------------------------------------------------

# In-memory store for COA decisions (will be replaced by DB)
_coa_decisions: dict[str, dict[str, dict]] = {}  # case_id → { coa_id → decision }


@router.post("/cases/{case_id}/coa/{coa_id}/approve")
def approve_coa(case_id: str, coa_id: str):
    """
    Attorney approves a Cause of Action — promotes from PROPOSAL to APPROVED.
    This is the P7 gate. Only approved COAs move forward to complaint drafting.
    """
    if case_id not in _coa_decisions:
        _coa_decisions[case_id] = {}

    _coa_decisions[case_id][coa_id] = {
        "status": "approved",
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "decided_by": "attorney",
    }

    # Also update the burden tracker assessment if it exists
    tracker = get_burden_tracker()
    assessment = tracker.get_assessment(case_id)
    if assessment:
        for coa in assessment.causes_of_action:
            if coa.coa_id == coa_id:
                coa.status = "approved"
                break

    return {
        "success": True,
        "correlation_id": new_id(),
        "case_id": case_id,
        "coa_id": coa_id,
        "status": "approved",
    }


@router.post("/cases/{case_id}/coa/{coa_id}/dismiss")
def dismiss_coa(case_id: str, coa_id: str):
    """
    Attorney dismisses a Cause of Action — will not be included in complaint.
    """
    if case_id not in _coa_decisions:
        _coa_decisions[case_id] = {}

    _coa_decisions[case_id][coa_id] = {
        "status": "dismissed",
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "decided_by": "attorney",
    }

    tracker = get_burden_tracker()
    assessment = tracker.get_assessment(case_id)
    if assessment:
        for coa in assessment.causes_of_action:
            if coa.coa_id == coa_id:
                coa.status = "dismissed"
                break

    return {
        "success": True,
        "correlation_id": new_id(),
        "case_id": case_id,
        "coa_id": coa_id,
        "status": "dismissed",
    }


@router.post("/cases/{case_id}/coa/approve-all")
def approve_all_coas(case_id: str):
    """
    DEV MODE / Batch: Approve all COAs for a case at once.
    Moves all candidate COAs to approved status.
    """
    if case_id not in _coa_decisions:
        _coa_decisions[case_id] = {}

    tracker = get_burden_tracker()
    assessment = tracker.get_assessment(case_id)
    approved_ids = []

    if assessment:
        now = datetime.now(timezone.utc).isoformat()
        for coa in assessment.causes_of_action:
            if coa.status != "dismissed":
                coa.status = "approved"
                _coa_decisions[case_id][coa.coa_id] = {
                    "status": "approved",
                    "decided_at": now,
                    "decided_by": "attorney",
                }
                approved_ids.append(coa.coa_id)

    return {
        "success": True,
        "correlation_id": new_id(),
        "case_id": case_id,
        "approved_count": len(approved_ids),
        "approved_coa_ids": approved_ids,
    }


@router.get("/cases/{case_id}/coa/decisions")
def get_coa_decisions(case_id: str):
    """Get all attorney decisions on COAs for this case."""
    decisions = _coa_decisions.get(case_id, {})
    return {
        "success": True,
        "correlation_id": new_id(),
        "case_id": case_id,
        "decisions": decisions,
        "approved_count": sum(1 for d in decisions.values() if d["status"] == "approved"),
        "dismissed_count": sum(1 for d in decisions.values() if d["status"] == "dismissed"),
    }
