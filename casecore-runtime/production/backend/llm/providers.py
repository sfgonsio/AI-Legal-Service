"""Provider abstraction — Claude primary, OpenAI secondary; lazy + resilient.

Vendor SDKs are imported lazily inside each call so the backend boots with
neither installed/configured. Each entry point raises a clear, actionable error
only when actually invoked without the needed key/SDK — never at import or boot.

This is the seam the AI capabilities build on:
  - text_complete()  -> reasoning / research / structured extraction (Claude)
  - vision_extract() -> OCR for images + scanned PDFs (Claude vision)
  - transcribe()     -> audio/video -> text (OpenAI Whisper)
  - embed()          -> RAG index vectors (OpenAI embeddings)
Swappable per task; no lock-in.
"""
from __future__ import annotations

import glob
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .config import LLMConfig, load_llm_config

# OpenAI Whisper rejects files over 25 MB; stay under with headroom.
_WHISPER_MAX_BYTES = 24 * 1024 * 1024
_AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".webm", ".mpga", ".mpeg", ".oga", ".ogg"}


class LLMNotConfigured(RuntimeError):
    """Raised when a capability is invoked but its provider/key is absent."""


def _require_anthropic(cfg: LLMConfig):
    if not cfg.anthropic_available:
        raise LLMNotConfigured(
            "ANTHROPIC_API_KEY is not set. Add it to backend/.env "
            "(copy from .env.template) to enable Claude reasoning/vision."
        )
    try:
        import anthropic  # type: ignore
    except ImportError as e:  # pragma: no cover - depends on optional dep
        raise LLMNotConfigured(
            "anthropic SDK not installed. `pip install anthropic`."
        ) from e
    return anthropic.Anthropic(api_key=cfg.anthropic_api_key)


def _require_openai(cfg: LLMConfig):
    if not cfg.openai_available:
        raise LLMNotConfigured(
            "OPENAI_API_KEY is not set. Add it to backend/.env "
            "(copy from .env.template) to enable embeddings/transcription."
        )
    try:
        import openai  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise LLMNotConfigured("openai SDK not installed. `pip install openai`.") from e
    return openai.OpenAI(api_key=cfg.openai_api_key)


def text_complete(
    prompt: str,
    *,
    system: Optional[str] = None,
    tier: str = "routine",
    max_tokens: int = 1024,
    cfg: Optional[LLMConfig] = None,
) -> str:
    """Claude text completion. tier in {reasoning, routine, bulk}."""
    cfg = cfg or load_llm_config()
    client = _require_anthropic(cfg)
    model = {
        "reasoning": cfg.reasoning_model,
        "routine": cfg.routine_model,
        "bulk": cfg.bulk_model,
    }.get(tier, cfg.routine_model)
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system or "You are a careful legal-analysis assistant. Cite sources; never invent facts.",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in msg.content if getattr(block, "type", None) == "text")


_OCR_PROMPT = (
    "You are an OCR engine. Transcribe ALL text visible in this image exactly, "
    "preserving structure (emails, receipts, documents: keep senders, dates, "
    "amounts, line items). Output only the transcribed text. If the image "
    "contains no legible text, output nothing."
)


def vision_extract(
    image_bytes: bytes,
    media_type: str,
    *,
    prompt: Optional[str] = None,
    cfg: Optional[LLMConfig] = None,
    max_tokens: int = 4096,
) -> str:
    """OCR an image (or rendered document page) with Claude vision.

    media_type e.g. 'image/png', 'image/jpeg'. Returns extracted text.
    """
    import base64

    cfg = cfg or load_llm_config()
    client = _require_anthropic(cfg)
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    msg = client.messages.create(
        model=cfg.vision_model,
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type, "data": b64,
                }},
                {"type": "text", "text": prompt or _OCR_PROMPT},
            ],
        }],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")


def _ffmpeg() -> Optional[str]:
    return shutil.which("ffmpeg")


def _ffprobe_duration(path: str) -> float:
    """Seconds of media, via ffprobe; 0.0 if unknown."""
    probe = shutil.which("ffprobe")
    if not probe:
        return 0.0
    try:
        out = subprocess.run(
            [probe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return float(out)
    except Exception:
        return 0.0


def _transcribe_file(client, model: str, path: str) -> str:
    with open(path, "rb") as fh:
        return client.audio.transcriptions.create(model=model, file=fh).text


def transcribe(media_path: str, *, cfg: Optional[LLMConfig] = None) -> str:
    """Audio/video -> text via OpenAI Whisper.

    Handles large/video files: extracts mono 16 kHz audio with ffmpeg, and
    splits into <25 MB time-chunks when needed (T1100 videos are ~700 MB).
    Small audio files are sent directly. Raises LLMNotConfigured if a large /
    video file is given but ffmpeg is unavailable.
    """
    cfg = cfg or load_llm_config()
    client = _require_openai(cfg)
    model = cfg.transcription_model
    ext = Path(media_path).suffix.lower()
    size = os.path.getsize(media_path)

    # Fast path: already-small audio.
    if ext in _AUDIO_EXTS and size <= _WHISPER_MAX_BYTES:
        return _transcribe_file(client, model, media_path)

    ff = _ffmpeg()
    if not ff:
        raise LLMNotConfigured(
            "ffmpeg not available — cannot transcode large/video media for "
            "Whisper. Install ffmpeg (or supply audio < 25 MB)."
        )

    tmpdir = tempfile.mkdtemp(prefix="cc_av_")
    try:
        audio = os.path.join(tmpdir, "audio.mp3")
        # Strip video, downmix to mono 16 kHz, ~32 kbps — tiny but ASR-adequate.
        subprocess.run(
            [ff, "-y", "-i", media_path, "-vn", "-ac", "1", "-ar", "16000",
             "-b:a", "32k", audio],
            check=True, capture_output=True,
        )
        if os.path.getsize(audio) <= _WHISPER_MAX_BYTES:
            return _transcribe_file(client, model, audio)

        # Still too big: split by time into <25 MB chunks.
        dur = _ffprobe_duration(audio)
        nchunks = max(2, math.ceil(os.path.getsize(audio) / _WHISPER_MAX_BYTES))
        chunk_secs = max(1, math.ceil((dur or nchunks * 600) / nchunks))
        subprocess.run(
            [ff, "-y", "-i", audio, "-f", "segment", "-segment_time",
             str(chunk_secs), "-c", "copy", os.path.join(tmpdir, "chunk_%03d.mp3")],
            check=True, capture_output=True,
        )
        parts = sorted(glob.glob(os.path.join(tmpdir, "chunk_*.mp3")))
        return "\n".join(_transcribe_file(client, model, p) for p in parts)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def status(cfg: Optional[LLMConfig] = None) -> dict:
    """Key-free status for health/diagnostics (safe to expose)."""
    cfg = cfg or load_llm_config()
    return cfg.status()
