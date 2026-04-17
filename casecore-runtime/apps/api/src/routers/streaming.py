"""
Real-Time Streaming Intake Router

WebSocket endpoint for real-time conversational intake:
  ws://localhost:8000/api/v1/ws/intake/{case_id}

Features:
  - Real-time audio transcription (Whisper)
  - Live COA matching (Claude)
  - Auto-generated follow-up questions
  - Streaming partial transcripts
  - Connection lifecycle management

Message Format:
  Client -> Server (incoming):
    {"type": "audio_chunk", "data": "<base64 audio>"}
    {"type": "text_input", "data": "typed narrative"}
    {"type": "control", "action": "pause|resume|end"}

  Server -> Client (outgoing):
    {"type": "transcript_partial", "text": "...", "is_final": false}
    {"type": "transcript_final", "text": "...", "is_final": true}
    {"type": "coa_update", "matches": [...]}
    {"type": "suggested_question", "question": "..."}
    {"type": "status", "state": "listening|processing|ready"}
    {"type": "error", "message": "..."}

Requires: pip install websockets
"""

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from src.services.streaming_transcription import StreamingTranscriber, StreamingSession
from src.services.realtime_coa_matcher import RealtimeCOAMatcher
from src.utils.ids import new_id

router = APIRouter(tags=["streaming"])
logger = logging.getLogger(__name__)

# Global state management
_transcriber: Optional[StreamingTranscriber] = None
_active_sessions: dict[str, dict] = {}  # session_id -> {websocket, transcriber_session, coa_matcher}


def _get_transcriber() -> StreamingTranscriber:
    """Get or create the global transcriber instance."""
    global _transcriber
    if _transcriber is None:
        _transcriber = StreamingTranscriber()
    return _transcriber


# ---------------------------------------------------------------------------
# WebSocket Message Handlers
# ---------------------------------------------------------------------------

async def _on_transcription_chunk(chunk):
    """Callback when transcriber emits a partial transcription."""
    # This is invoked from StreamingTranscriber
    # We'll use the session context to send it to the WebSocket
    pass  # Handled in the WebSocket handler loop


async def _on_coa_update(update):
    """Callback when COA matcher identifies new matches."""
    # This is invoked from RealtimeCOAMatcher
    # We'll use the session context to send it to the WebSocket
    pass  # Handled in the WebSocket handler loop


# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/intake/{case_id}")
async def websocket_intake(websocket: WebSocket, case_id: str):
    """
    Real-time streaming intake WebSocket endpoint.

    Path: /api/v1/ws/intake/{case_id}

    Accepts:
      - Audio chunks (base64 encoded)
      - Text input (typed narrative)
      - Control messages (pause/resume/end)

    Emits:
      - Partial & final transcripts
      - COA matches as they emerge
      - Suggested follow-up questions
      - Status updates
    """
    session_id = new_id()
    logger.info(f"[{session_id}] WebSocket connection attempt for case {case_id}")

    try:
        await websocket.accept()
        logger.info(f"[{session_id}] WebSocket accepted")

        # Initialize transcriber and COA matcher
        transcriber = _get_transcriber()
        coa_matcher = RealtimeCOAMatcher(case_id=case_id)

        # Create transcriber session with callback
        async def on_partial_chunk(chunk):
            await websocket.send_json({
                "type": "transcript_partial",
                "chunk_id": chunk.chunk_id,
                "sequence": chunk.sequence,
                "text": chunk.text,
                "confidence": chunk.confidence,
                "is_final": chunk.is_final,
                "duration_offset": chunk.end_offset_seconds,
            })

        # Create COA matcher with callback
        async def on_coa_update(update):
            questions = await coa_matcher.get_suggested_questions()
            await websocket.send_json({
                "type": "coa_update",
                "update_id": update.update_id,
                "timestamp": update.timestamp.isoformat(),
                "new_matches": [m.dict() for m in update.new_matches],
                "updated_matches": [m.dict() for m in update.updated_matches],
                "removed_matches": update.removed_matches,
                "suggested_questions": [q.dict() for q in questions],
            })

        transcriber_session = await transcriber.start_session(
            case_id=case_id,
            on_partial=on_partial_chunk,
        )
        coa_matcher._on_update = on_coa_update

        # Register session
        _active_sessions[session_id] = {
            "case_id": case_id,
            "websocket": websocket,
            "transcriber_session": transcriber_session,
            "coa_matcher": coa_matcher,
            "full_transcript": "",
            "connected_at": datetime.now(timezone.utc),
        }

        # Send initial status
        await websocket.send_json({
            "type": "status",
            "state": "listening",
            "session_id": session_id,
            "case_id": case_id,
            "message": "Intake streaming session started. Send audio chunks or type narrative.",
        })

        logger.info(f"[{session_id}] Session initialized, waiting for messages")

        # Message loop
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "unknown")
            logger.debug(f"[{session_id}] Received {message_type} message")

            try:
                if message_type == "audio_chunk":
                    await _handle_audio_chunk(
                        session_id,
                        websocket,
                        transcriber,
                        transcriber_session,
                        coa_matcher,
                        data,
                    )

                elif message_type == "text_input":
                    await _handle_text_input(
                        session_id,
                        websocket,
                        coa_matcher,
                        data,
                    )

                elif message_type == "control":
                    await _handle_control(
                        session_id,
                        websocket,
                        transcriber,
                        transcriber_session,
                        data,
                    )

                else:
                    logger.warning(f"[{session_id}] Unknown message type: {message_type}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    })

            except Exception as e:
                logger.error(f"[{session_id}] Message handler error: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}",
                })

    except WebSocketDisconnect:
        logger.info(f"[{session_id}] WebSocket disconnected")

    except Exception as e:
        logger.error(f"[{session_id}] WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {str(e)}",
            })
        except Exception:
            pass

    finally:
        # Clean up session
        if session_id in _active_sessions:
            session_data = _active_sessions[session_id]
            transcriber_session = session_data.get("transcriber_session")
            transcriber = _get_transcriber()

            # Finalize transcription if active
            if transcriber_session and transcriber_session.is_active:
                try:
                    result = await transcriber.end_session(transcriber_session)
                    logger.info(
                        f"[{session_id}] Transcription finalized: "
                        f"{result.chunks_count} chunks, {result.duration_seconds:.1f}s"
                    )
                except Exception as e:
                    logger.error(f"[{session_id}] Error finalizing transcription: {e}")

            del _active_sessions[session_id]
            logger.info(f"[{session_id}] Session cleaned up")


# ---------------------------------------------------------------------------
# Message Handlers
# ---------------------------------------------------------------------------

async def _handle_audio_chunk(
    session_id: str,
    websocket: WebSocket,
    transcriber: StreamingTranscriber,
    transcriber_session: StreamingSession,
    coa_matcher: RealtimeCOAMatcher,
    data: dict,
):
    """Handle incoming audio chunk."""
    try:
        # Decode base64 audio
        audio_data = base64.b64decode(data.get("data", ""))
        if not audio_data:
            raise ValueError("Empty audio data")

        # Send processing status
        await websocket.send_json({
            "type": "status",
            "state": "processing",
            "message": "Transcribing audio chunk...",
        })

        # Feed to transcriber
        chunk = await transcriber.feed_audio(transcriber_session, audio_data)

        # Get updated transcript
        full_transcript = await transcriber.get_full_transcript(transcriber_session)
        _active_sessions[session_id]["full_transcript"] = full_transcript

        # Send final transcript update if chunk was completed
        if chunk and chunk.is_final:
            await websocket.send_json({
                "type": "transcript_final",
                "text": full_transcript,
                "chunk_id": chunk.chunk_id,
                "sequence": chunk.sequence,
            })

        # Update COA matcher with accumulated transcript
        update = await coa_matcher.on_transcript_update(full_transcript)

        # Send ready status
        await websocket.send_json({
            "type": "status",
            "state": "listening",
            "message": "Ready for next input",
        })

    except Exception as e:
        logger.error(f"[{session_id}] Audio chunk handler error: {e}", exc_info=True)
        raise


async def _handle_text_input(
    session_id: str,
    websocket: WebSocket,
    coa_matcher: RealtimeCOAMatcher,
    data: dict,
):
    """Handle typed narrative input."""
    try:
        text = data.get("data", "").strip()
        if not text:
            raise ValueError("Empty text input")

        # Update COA matcher
        update = await coa_matcher.on_transcript_update(text)

        # Store in session
        _active_sessions[session_id]["full_transcript"] = text

        # Send transcript confirmation
        await websocket.send_json({
            "type": "transcript_final",
            "text": text,
            "is_typed": True,
        })

        # Send ready status
        await websocket.send_json({
            "type": "status",
            "state": "listening",
            "message": "Narrative received. Ready for next input.",
        })

    except Exception as e:
        logger.error(f"[{session_id}] Text input handler error: {e}", exc_info=True)
        raise


async def _handle_control(
    session_id: str,
    websocket: WebSocket,
    transcriber: StreamingTranscriber,
    transcriber_session: StreamingSession,
    data: dict,
):
    """Handle control messages (pause/resume/end)."""
    try:
        action = data.get("action", "").lower()

        if action == "pause":
            await websocket.send_json({
                "type": "status",
                "state": "paused",
                "message": "Recording paused",
            })
            logger.info(f"[{session_id}] Recording paused")

        elif action == "resume":
            await websocket.send_json({
                "type": "status",
                "state": "listening",
                "message": "Recording resumed",
            })
            logger.info(f"[{session_id}] Recording resumed")

        elif action == "end":
            # Finalize transcription
            if transcriber_session.is_active:
                result = await transcriber.end_session(transcriber_session)
                logger.info(
                    f"[{session_id}] Intake ended: "
                    f"{result.chunks_count} chunks, {result.duration_seconds:.1f}s, "
                    f"full transcript length: {len(result.full_transcript)} chars"
                )

                # Send final summary
                await websocket.send_json({
                    "type": "transcript_final",
                    "text": result.full_transcript,
                    "is_complete": True,
                    "summary": {
                        "chunks_processed": result.chunks_count,
                        "duration_seconds": result.duration_seconds,
                        "character_count": len(result.full_transcript),
                    },
                })

            # Send completion status
            await websocket.send_json({
                "type": "status",
                "state": "complete",
                "message": "Intake session complete",
            })

            # Close connection
            await websocket.close(code=1000, reason="Intake complete")

        else:
            raise ValueError(f"Unknown control action: {action}")

    except Exception as e:
        logger.error(f"[{session_id}] Control handler error: {e}", exc_info=True)
        raise


# ---------------------------------------------------------------------------
# Management Endpoints (HTTP)
# ---------------------------------------------------------------------------

@router.get("/ws/intake/status")
async def get_intake_sessions():
    """
    Get status of all active streaming intake sessions.

    Returns:
      {
        "active_sessions": [
          {
            "session_id": "...",
            "case_id": "...",
            "connected_at": "...",
            "transcript_length": 1234,
            "coas_identified": 3
          }
        ]
      }
    """
    sessions_info = []
    for sid, session_data in _active_sessions.items():
        coa_matcher = session_data.get("coa_matcher")
        sessions_info.append({
            "session_id": sid,
            "case_id": session_data.get("case_id"),
            "connected_at": session_data.get("connected_at").isoformat(),
            "transcript_length": len(session_data.get("full_transcript", "")),
            "coas_identified": len(coa_matcher.get_current_matches()) if coa_matcher else 0,
        })

    return {
        "active_sessions": sessions_info,
        "total_active": len(sessions_info),
    }


@router.get("/ws/intake/{case_id}/status")
async def get_intake_session_status(case_id: str):
    """
    Get status of a specific case's intake session.

    Returns:
      {
        "case_id": "...",
        "session_id": "...",
        "connected_at": "...",
        "transcript": "full transcript text",
        "transcript_length": 1234,
        "coas": [ { ... } ],
        "suggested_questions": [ { ... } ]
      }
    """
    # Find session for this case
    session_data = None
    session_id = None
    for sid, data in _active_sessions.items():
        if data.get("case_id") == case_id:
            session_data = data
            session_id = sid
            break

    if not session_data:
        raise HTTPException(status_code=404, detail=f"No active session for case {case_id}")

    coa_matcher = session_data.get("coa_matcher")
    transcript = session_data.get("full_transcript", "")

    coas = coa_matcher.get_current_matches() if coa_matcher else []
    questions = await coa_matcher.get_suggested_questions() if coa_matcher else []

    return {
        "case_id": case_id,
        "session_id": session_id,
        "connected_at": session_data.get("connected_at").isoformat(),
        "transcript": transcript,
        "transcript_length": len(transcript),
        "coas": [c.dict() for c in coas],
        "suggested_questions": [q.dict() for q in questions],
    }
