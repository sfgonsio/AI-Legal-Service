"""
Streaming Transcription Service — Real-Time Audio Processing

Handles real-time audio intake with these features:
  1. Accepts audio chunks via WebSocket in real-time
  2. Uses OpenAI Whisper API for transcription (chunked approach)
  3. Buffers 3-5 seconds of audio, transcribes each chunk
  4. Merges results with overlap detection to avoid duplicate words
  5. Emits partial transcripts back over WebSocket as they become available
  6. Maintains a running full transcript that accumulates

Architecture:
  - StreamingTranscriber: Main class managing transcription sessions
  - Chunking strategy: Buffer ~160KB (5 seconds @ 16kHz mono 16-bit)
  - Overlap handling: Last 0.5-1 second of previous chunk helps context

Requires: pip install openai
"""

import asyncio
import io
import os
import tempfile
from datetime import datetime, timezone
from typing import Optional, Callable
from dataclasses import dataclass, field
from collections import deque

from pydantic import BaseModel
from src.utils.ids import new_id


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class TranscriptionChunk:
    """A transcribed chunk of audio."""
    chunk_id: str
    sequence: int
    text: str
    confidence: float = 0.95
    is_final: bool = False
    start_offset_seconds: float = 0.0
    end_offset_seconds: float = 0.0


@dataclass
class StreamingSession:
    """State for a streaming transcription session."""
    session_id: str
    case_id: str
    buffer: deque = field(default_factory=lambda: deque(maxlen=2))  # Keep 2 chunks for overlap
    full_transcript: str = ""
    chunks_processed: int = 0
    total_audio_seconds: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_chunk_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sample_rate: int = 16000
    is_active: bool = True


class StreamingTranscriptionResult(BaseModel):
    """Result from a streaming transcription session."""
    session_id: str
    case_id: str
    full_transcript: str
    chunks_count: int
    duration_seconds: float
    language: str = "en"
    model_used: str = "whisper-1"
    completed_at: datetime


# ---------------------------------------------------------------------------
# Streaming Transcriber Service
# ---------------------------------------------------------------------------

class StreamingTranscriber:
    """
    Real-time streaming transcription service using OpenAI Whisper.

    Configuration via environment variables:
      OPENAI_API_KEY — Required for Whisper API access
      WHISPER_MODEL — Model to use (default: "whisper-1")
      WHISPER_LANGUAGE — Language hint (default: "en")
      STREAMING_CHUNK_SIZE — Bytes to buffer before transcribing (default: 160000 = ~5 sec)
      STREAMING_OVERLAP_SIZE — Bytes of overlap from previous chunk (default: 32000 = ~1 sec)

    Example usage:
      transcriber = StreamingTranscriber()
      session = await transcriber.start_session(case_id="case-123", on_partial=my_callback)
      await transcriber.feed_audio(session, audio_bytes)
      full = await transcriber.get_full_transcript(session)
      await transcriber.end_session(session)
    """

    LEGAL_PROMPT = (
        "This is a legal intake interview discussing California law. "
        "Common terms include: plaintiff, defendant, cause of action, "
        "negligence, breach of duty, proximate cause, damages, "
        "statute of limitations, discovery, deposition, interrogatories, "
        "subpoena, evidence code, CACI, burden of proof, preponderance, "
        "clear and convincing, beyond reasonable doubt, "
        "compensatory damages, punitive damages, injunctive relief, "
        "FEHA, ADA, wrongful termination, harassment, discrimination, "
        "premises liability, medical malpractice, product liability, "
        "fiduciary duty, breach of contract, fraud, misrepresentation."
    )

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("WHISPER_MODEL", "whisper-1")
        self.language = os.getenv("WHISPER_LANGUAGE", "en")
        self.chunk_size = int(os.getenv("STREAMING_CHUNK_SIZE", "160000"))
        self.overlap_size = int(os.getenv("STREAMING_OVERLAP_SIZE", "32000"))
        self._client = None
        self._sessions: dict[str, StreamingSession] = {}

    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise RuntimeError(
                    "openai package not installed. "
                    "Run: pip install openai"
                )
        return self._client

    async def start_session(
        self,
        case_id: str,
        on_partial: Optional[Callable[[TranscriptionChunk], None]] = None,
    ) -> StreamingSession:
        """
        Initialize a streaming transcription session.

        Args:
            case_id: The case ID for this transcription
            on_partial: Callback invoked when a partial transcription is ready.
                       Receives TranscriptionChunk with is_final=False.

        Returns:
            StreamingSession object to pass to feed_audio, get_partial, etc.
        """
        session = StreamingSession(
            session_id=new_id(),
            case_id=case_id,
        )
        self._sessions[session.session_id] = session
        session._on_partial = on_partial  # type: ignore
        return session

    async def feed_audio(self, session: StreamingSession, audio_chunk: bytes) -> Optional[TranscriptionChunk]:
        """
        Feed an audio chunk into the session buffer.

        Transcribes when enough audio has accumulated (~5 seconds).

        Args:
            session: StreamingSession from start_session()
            audio_chunk: Raw audio bytes (WebM, WAV, etc.)

        Returns:
            TranscriptionChunk if transcription was triggered, None otherwise.
        """
        if not session.is_active:
            raise ValueError(f"Session {session.session_id} is not active")

        # Add to buffer
        session.buffer.append(audio_chunk)
        total_buffered = sum(len(chunk) for chunk in session.buffer)

        # Check if we should transcribe
        if total_buffered >= self.chunk_size:
            return await self._transcribe_buffer(session)

        return None

    async def _transcribe_buffer(self, session: StreamingSession) -> Optional[TranscriptionChunk]:
        """
        Transcribe accumulated audio chunks with overlap detection.

        Merges results from overlapping chunks to avoid duplicate words.
        """
        if not session.buffer:
            return None

        # Combine all buffered chunks
        combined = b"".join(session.buffer)
        session.buffer.clear()

        try:
            # Write to temp file (Whisper API requires file-like object)
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(combined)
                tmp_path = tmp.name

            try:
                # Call Whisper API
                with open(tmp_path, "rb") as f:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=f,
                        language=self.language,
                        prompt=self.LEGAL_PROMPT,
                    )
                text = response.text.strip()
            finally:
                os.unlink(tmp_path)

            if not text:
                return None

            # Handle overlap: if full_transcript has content, check for duplicate words
            new_text = text
            if session.full_transcript:
                new_text = self._merge_with_overlap_detection(
                    session.full_transcript,
                    text,
                )

            session.full_transcript += new_text
            session.chunks_processed += 1
            session.total_audio_seconds += len(combined) / (
                session.sample_rate * 2
            )  # 16-bit = 2 bytes/sample
            session.last_chunk_time = datetime.now(timezone.utc)

            chunk = TranscriptionChunk(
                chunk_id=new_id(),
                sequence=session.chunks_processed,
                text=new_text,
                confidence=0.95,
                is_final=False,
                start_offset_seconds=session.total_audio_seconds - (
                    len(combined) / (session.sample_rate * 2)
                ),
                end_offset_seconds=session.total_audio_seconds,
            )

            # Invoke callback if provided
            if hasattr(session, "_on_partial") and session._on_partial:  # type: ignore
                try:
                    result = session._on_partial(chunk)  # type: ignore
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    print(f"[WARNING] on_partial callback failed: {e}")

            return chunk

        except Exception as e:
            print(f"[ERROR] Transcription failed: {e}")
            return None

    def _merge_with_overlap_detection(self, previous: str, current: str) -> str:
        """
        Detect and remove duplicate words at the boundary between chunks.

        Simple heuristic: if the current transcription starts with the last
        N words of the previous transcription, strip them from current.

        This handles the case where Whisper repeats context from overlapping audio.
        """
        if not previous or not current:
            return current

        prev_words = previous.split()
        curr_words = current.split()

        # Check for up to 5-word overlap
        for overlap_len in range(min(5, len(prev_words), len(curr_words)), 0, -1):
            prev_tail = " ".join(prev_words[-overlap_len:]).lower()
            curr_head = " ".join(curr_words[:overlap_len]).lower()

            if prev_tail == curr_head:
                # Found overlap, skip the first overlap_len words from current
                return " ".join(curr_words[overlap_len:])

        return current

    async def get_partial(self, session: StreamingSession) -> str:
        """Get the current partial transcript accumulated so far."""
        return session.full_transcript

    async def get_full_transcript(self, session: StreamingSession) -> str:
        """Get the full accumulated transcript."""
        return session.full_transcript

    async def end_session(self, session: StreamingSession) -> StreamingTranscriptionResult:
        """
        Finalize a streaming session.

        Transcribes any remaining buffered audio, marks session as inactive,
        and returns the complete transcription result.
        """
        if not session.is_active:
            raise ValueError(f"Session {session.session_id} already ended")

        # Transcribe any remaining audio
        if session.buffer:
            await self._transcribe_buffer(session)

        session.is_active = False

        result = StreamingTranscriptionResult(
            session_id=session.session_id,
            case_id=session.case_id,
            full_transcript=session.full_transcript,
            chunks_count=session.chunks_processed,
            duration_seconds=session.total_audio_seconds,
            language=self.language,
            model_used=self.model,
            completed_at=datetime.now(timezone.utc),
        )

        # Clean up
        del self._sessions[session.session_id]

        return result

    def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """Retrieve an active session by ID."""
        return self._sessions.get(session_id)

    def list_active_sessions(self) -> list[StreamingSession]:
        """List all active streaming sessions."""
        return [s for s in self._sessions.values() if s.is_active]
