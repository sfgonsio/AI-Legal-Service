"""
Audio Transcription Service — Whisper API Integration

Handles real-time audio intake:
  1. Accepts audio chunks (streaming) or complete audio files
  2. Transcribes via OpenAI Whisper API
  3. Applies legal vocabulary boosting
  4. Returns timestamped transcript segments
  5. Feeds transcript into INTERVIEW_AGENT pipeline

Supports:
  - File upload (wav, mp3, m4a, webm, mp4)
  - Streaming chunks via WebSocket
  - Real-time partial transcription
"""

import io
import os
import tempfile
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from pydantic import BaseModel, Field
from src.utils.ids import new_id


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TranscriptSegment(BaseModel):
    """A single transcribed segment with timing."""
    segment_id: str
    start_time: float  # seconds
    end_time: float  # seconds
    text: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    speaker: Optional[str] = None  # "client", "attorney", "unknown"


class TranscriptionResult(BaseModel):
    """Complete transcription result."""
    transcription_id: str
    case_id: str
    session_id: str
    full_text: str
    segments: list[TranscriptSegment] = Field(default_factory=list)
    duration_seconds: float = 0.0
    language: str = "en"
    model_used: str = "whisper-1"
    transcribed_at: datetime
    audio_source: str = "upload"  # "upload", "stream", "microphone"


class StreamingChunk(BaseModel):
    """A chunk of streaming audio data."""
    chunk_id: str
    sequence: int
    audio_data: bytes
    format: str = "webm"  # audio format
    is_final: bool = False


# ---------------------------------------------------------------------------
# Whisper Transcription Service
# ---------------------------------------------------------------------------

class WhisperTranscriptionService:
    """
    Transcription service using OpenAI's Whisper API.

    Configuration via environment variables:
      OPENAI_API_KEY — Required for Whisper API access
      WHISPER_MODEL — Model to use (default: "whisper-1")
      WHISPER_LANGUAGE — Language hint (default: "en")
    """

    SUPPORTED_FORMATS = {"wav", "mp3", "m4a", "webm", "mp4", "ogg", "flac"}

    # Legal terminology prompt to improve accuracy
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
        self._client = None

        # Streaming state per session
        self._stream_buffers: dict[str, list[bytes]] = {}

    @property
    def client(self):
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

    # ------------------------------------------------------------------
    # File-based transcription
    # ------------------------------------------------------------------

    def transcribe_file(
        self,
        file_path: str,
        case_id: str,
        session_id: str,
        speaker: str = "client",
    ) -> TranscriptionResult:
        """
        Transcribe an audio file via Whisper API.

        Supports: wav, mp3, m4a, webm, mp4, ogg, flac
        """
        path = Path(file_path)
        if path.suffix.lstrip(".").lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        with open(file_path, "rb") as audio_file:
            # Verbose JSON gives us timestamps per segment
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=self.language,
                prompt=self.LEGAL_PROMPT,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = []
        for seg in getattr(response, "segments", []):
            # Handle both dict (older SDK) and Pydantic object (newer SDK)
            if isinstance(seg, dict):
                s_start = seg.get("start", 0.0)
                s_end = seg.get("end", 0.0)
                s_text = seg.get("text", "").strip()
                s_conf = 1.0 - seg.get("no_speech_prob", 0.0)
            else:
                s_start = getattr(seg, "start", 0.0)
                s_end = getattr(seg, "end", 0.0)
                s_text = getattr(seg, "text", "").strip()
                s_conf = 1.0 - getattr(seg, "no_speech_prob", 0.0)
            segments.append(TranscriptSegment(
                segment_id=new_id(),
                start_time=s_start,
                end_time=s_end,
                text=s_text,
                confidence=s_conf,
                speaker=speaker,
            ))

        full_text = getattr(response, "text", "")
        duration = getattr(response, "duration", 0.0)

        return TranscriptionResult(
            transcription_id=new_id(),
            case_id=case_id,
            session_id=session_id,
            full_text=full_text,
            segments=segments,
            duration_seconds=duration or 0.0,
            language=self.language,
            model_used=self.model,
            transcribed_at=datetime.now(timezone.utc),
            audio_source="upload",
        )

    def transcribe_bytes(
        self,
        audio_data: bytes,
        case_id: str,
        session_id: str,
        format: str = "webm",
        speaker: str = "client",
    ) -> TranscriptionResult:
        """
        Transcribe raw audio bytes via Whisper API.

        Useful for browser-recorded audio or API-submitted audio.
        """
        # Write to temp file (Whisper API requires file-like object)
        suffix = f".{format}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            return self.transcribe_file(tmp_path, case_id, session_id, speaker)
        finally:
            os.unlink(tmp_path)

    # ------------------------------------------------------------------
    # Streaming transcription
    # ------------------------------------------------------------------

    def start_stream(self, session_id: str) -> str:
        """Initialize a streaming transcription session."""
        stream_id = new_id()
        self._stream_buffers[stream_id] = []
        return stream_id

    def add_chunk(self, stream_id: str, audio_chunk: bytes) -> Optional[str]:
        """
        Add an audio chunk to the stream buffer.

        Returns partial transcription if enough audio has accumulated,
        otherwise None.
        """
        if stream_id not in self._stream_buffers:
            raise ValueError(f"Stream {stream_id} not found")

        self._stream_buffers[stream_id].append(audio_chunk)

        # Transcribe every ~5 seconds of audio (rough estimate)
        # 16kHz mono 16-bit = ~32KB/sec, so ~160KB per 5 sec
        total_size = sum(len(c) for c in self._stream_buffers[stream_id])
        if total_size >= 160_000:
            combined = b"".join(self._stream_buffers[stream_id])
            self._stream_buffers[stream_id] = []

            try:
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                    tmp.write(combined)
                    tmp_path = tmp.name

                with open(tmp_path, "rb") as f:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=f,
                        language=self.language,
                        prompt=self.LEGAL_PROMPT,
                    )
                os.unlink(tmp_path)
                return response.text
            except Exception:
                return None

        return None

    def end_stream(
        self,
        stream_id: str,
        case_id: str,
        session_id: str,
        speaker: str = "client",
    ) -> Optional[TranscriptionResult]:
        """
        Finalize a streaming session and transcribe remaining audio.
        """
        if stream_id not in self._stream_buffers:
            return None

        remaining = self._stream_buffers.pop(stream_id, [])
        if not remaining:
            return None

        combined = b"".join(remaining)
        return self.transcribe_bytes(combined, case_id, session_id, "webm", speaker)
