"""
Video Evidence Processor
Extracts audio, transcribes, captures key frames, and feeds into intake pipeline.
Handles: MP4, MOV, AVI, WebM

This module provides:
  1. VideoMetadata — probed video information
  2. VideoProcessor — ffmpeg-based processing pipeline
  3. VideoIntakeResult — structured transcription + frames + metadata
"""

import os
import subprocess
import tempfile
import json
import urllib.request
import urllib.parse
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Callable
from dataclasses import dataclass

from pydantic import BaseModel, Field
from src.utils.ids import new_id

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class VideoMetadata(BaseModel):
    """Video file metadata from ffprobe."""
    duration: float  # seconds
    width: int
    height: int
    fps: float
    codec_video: Optional[str] = None
    codec_audio: Optional[str] = None
    has_audio: bool = False
    has_video: bool = True
    bit_rate: Optional[int] = None
    format: str = "unknown"


class AudioSegment(BaseModel):
    """Audio segment extracted from video."""
    segment_id: str
    start_time: float  # seconds
    duration: float
    file_path: str  # path to audio chunk (WAV/MP3)


class TranscriptSegment(BaseModel):
    """Transcribed text segment from Whisper."""
    segment_id: str
    start_time: float  # seconds
    end_time: float
    text: str
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class VideoIntakeResult(BaseModel):
    """Complete video processing result."""
    video_id: str
    case_id: str
    filename: str
    video_metadata: VideoMetadata
    transcript: Optional[str] = None  # full concatenated text
    segments: List[TranscriptSegment] = Field(default_factory=list)
    frame_paths: List[str] = Field(default_factory=list)  # paths to extracted frames
    has_audio: bool
    processed_at: datetime
    processing_duration_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Video Processor
# ---------------------------------------------------------------------------

class VideoProcessor:
    """
    Video processing pipeline using ffmpeg and OpenAI Whisper.

    Configuration via environment variables:
      OPENAI_API_KEY — Required for Whisper transcription
      FFMPEG_PATH — Path to ffmpeg binary (default: /usr/bin/ffmpeg)
      FFPROBE_PATH — Path to ffprobe binary (default: /usr/bin/ffprobe)
    """

    SUPPORTED_FORMATS = {".mp4", ".mov", ".avi", ".webm", ".mkv", ".flv", ".m4v", ".mpg", ".mpeg", ".3gp"}
    WHISPER_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB limit from OpenAI
    WHISPER_CHUNK_SIZE = 20 * 1024 * 1024  # Use 20MB chunks to be safe

    def __init__(self):
        self.ffmpeg_path = os.getenv("FFMPEG_PATH", self._find_binary("ffmpeg"))
        self.ffprobe_path = os.getenv("FFPROBE_PATH", self._find_binary("ffprobe"))
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

        if not self._binary_exists(self.ffmpeg_path):
            logger.warning(f"ffmpeg not found at {self.ffmpeg_path}")
        else:
            logger.info(f"ffmpeg found at {self.ffmpeg_path}")
        if not self._binary_exists(self.ffprobe_path):
            logger.warning(f"ffprobe not found at {self.ffprobe_path}")
        else:
            logger.info(f"ffprobe found at {self.ffprobe_path}")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set. Whisper transcription will be unavailable.")

    @staticmethod
    def _find_binary(name: str) -> str:
        """Auto-detect ffmpeg/ffprobe on Windows or Linux."""
        import shutil
        # Try PATH first
        found = shutil.which(name)
        if found:
            return found
        # Common Windows winget install location
        local_app = os.environ.get("LOCALAPPDATA", "")
        if local_app:
            import glob
            pattern = os.path.join(local_app, "Microsoft", "WinGet", "Packages",
                                   "Gyan.FFmpeg*", "ffmpeg-*", "bin", f"{name}.exe")
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
        # Other common Windows locations
        for p in [rf"C:\ffmpeg\bin\{name}.exe",
                  rf"C:\Program Files\FFmpeg\bin\{name}.exe"]:
            if os.path.exists(p):
                return p
        # Linux default
        if os.path.exists(f"/usr/bin/{name}"):
            return f"/usr/bin/{name}"
        return name  # Bare name, hope it's in PATH

    @staticmethod
    def _binary_exists(path: str) -> bool:
        """Check if a binary exists (handles bare names via shutil.which)."""
        import shutil
        return os.path.exists(path) or shutil.which(path) is not None

    # -----------------------------------------------------------------------
    # Video Probing
    # -----------------------------------------------------------------------

    def probe(self, video_path: str) -> VideoMetadata:
        """
        Probe video file to get metadata.

        Args:
            video_path: Path to video file

        Returns:
            VideoMetadata object

        Uses ffprobe to extract duration, resolution, codecs, etc.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-show_format",
            "-show_streams",
            "-print_format", "json",
            video_path,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )

            data = json.loads(result.stdout)
            format_data = data.get("format", {})
            streams = data.get("streams", [])

            # Find video and audio streams
            video_stream = None
            audio_stream = None

            for stream in streams:
                codec_type = stream.get("codec_type")
                if codec_type == "video" and video_stream is None:
                    video_stream = stream
                elif codec_type == "audio" and audio_stream is None:
                    audio_stream = stream

            # Extract metadata
            duration = float(format_data.get("duration", 0))
            width = video_stream.get("width", 0) if video_stream else 0
            height = video_stream.get("height", 0) if video_stream else 0
            fps = 0.0
            if video_stream:
                r_frame_rate = video_stream.get("r_frame_rate", "0/1")
                try:
                    numerator, denominator = map(float, r_frame_rate.split("/"))
                    fps = numerator / denominator if denominator else 0
                except (ValueError, ZeroDivisionError):
                    fps = 0.0

            codec_video = video_stream.get("codec_name") if video_stream else None
            codec_audio = audio_stream.get("codec_name") if audio_stream else None
            bit_rate = int(format_data.get("bit_rate", 0)) if format_data.get("bit_rate") else None

            metadata = VideoMetadata(
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                codec_video=codec_video,
                codec_audio=codec_audio,
                has_audio=audio_stream is not None,
                has_video=video_stream is not None,
                bit_rate=bit_rate,
                format=Path(video_path).suffix.lstrip(".").lower(),
            )

            logger.info(
                f"Probed {video_path}: {width}x{height} @ {fps:.1f}fps, "
                f"duration {duration:.1f}s, audio={metadata.has_audio}"
            )

            return metadata

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"ffprobe timeout on {video_path}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"ffprobe output parse error: {e}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffprobe error: {e.stderr}")
        except Exception as e:
            logger.error(f"Probe error: {e}")
            raise

    # -----------------------------------------------------------------------
    # Audio Extraction
    # -----------------------------------------------------------------------

    def extract_audio(self, video_path: str, output_path: str, format: str = "wav") -> str:
        """
        Extract audio track from video.

        Args:
            video_path: Path to video file
            output_path: Path where audio will be saved
            format: Output format (wav, mp3, aac)

        Returns:
            Path to extracted audio file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le" if format == "wav" else ("libmp3lame" if format == "mp3" else "aac"),
            "-ar", "16000",  # 16kHz sample rate for Whisper
            "-ac", "1",  # Mono
            "-y",  # Overwrite output
            output_path,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10min timeout for long videos
                check=True,
            )

            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                logger.info(f"Extracted audio: {output_path} ({size} bytes)")
                return output_path
            else:
                raise RuntimeError("Audio extraction produced no file")

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Audio extraction timeout on {video_path}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Audio extraction failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            raise

    # -----------------------------------------------------------------------
    # Frame Capture
    # -----------------------------------------------------------------------

    def capture_frames(
        self,
        video_path: str,
        interval_seconds: float = 30,
        output_dir: Optional[str] = None,
    ) -> List[str]:
        """
        Capture video frames at regular intervals.

        Args:
            video_path: Path to video file
            interval_seconds: Seconds between frames
            output_dir: Directory for frame images

        Returns:
            List of frame file paths
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Create temp directory if not specified
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="video_frames_")
        else:
            os.makedirs(output_dir, exist_ok=True)

        # Get video duration to calculate frame count
        metadata = self.probe(video_path)
        num_frames = int(metadata.duration / interval_seconds) + 1
        num_frames = min(num_frames, 100)  # Cap at 100 frames

        frame_pattern = os.path.join(output_dir, "frame_%03d.png")

        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-vf", f"fps=1/{interval_seconds}",
            "-y",
            frame_pattern,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=True,
            )

            # Collect generated frames
            frame_files = sorted([
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.startswith("frame_") and f.endswith(".png")
            ])

            logger.info(f"Captured {len(frame_files)} frames from {video_path}")
            return frame_files

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Frame capture timeout on {video_path}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Frame capture failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            raise

    # -----------------------------------------------------------------------
    # Whisper Transcription
    # -----------------------------------------------------------------------

    def _split_audio_file(self, audio_path: str) -> List[str]:
        """
        Split large audio file into Whisper-compatible chunks (max 25MB each).

        Args:
            audio_path: Path to audio file

        Returns:
            List of chunk file paths
        """
        file_size = os.path.getsize(audio_path)

        if file_size <= self.WHISPER_MAX_FILE_SIZE:
            return [audio_path]

        # Need to split
        logger.info(f"Audio file {file_size} bytes exceeds Whisper limit. Splitting into chunks.")

        # Use ffmpeg to split by duration
        metadata = self.probe(audio_path)
        duration = metadata.duration
        num_chunks = math.ceil(file_size / self.WHISPER_CHUNK_SIZE)
        chunk_duration = duration / num_chunks

        output_dir = tempfile.mkdtemp(prefix="audio_chunks_")
        chunk_pattern = os.path.join(output_dir, "chunk_%03d.wav")

        cmd = [
            self.ffmpeg_path,
            "-i", audio_path,
            "-f", "segment",
            "-segment_time", str(chunk_duration),
            "-c", "copy",
            "-y",
            chunk_pattern,
        ]

        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=True,
            )

            chunks = sorted([
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.startswith("chunk_") and f.endswith(".wav")
            ])

            logger.info(f"Split audio into {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Audio split error: {e}")
            raise

    def _transcribe_audio_chunk(self, audio_path: str) -> str:
        """
        Transcribe a single audio chunk via Whisper API.

        Args:
            audio_path: Path to audio file (< 25MB)

        Returns:
            Transcribed text
        """
        if not self.openai_api_key:
            logger.warning("OpenAI API key not set. Skipping transcription.")
            return ""

        # Read audio file
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        # Prepare multipart form data
        boundary = "----FormBoundary7MA4YWxkTrZu0gW"
        body = []

        # Add model field
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="model"')
        body.append(b"")
        body.append(b"whisper-1")

        # Add language field
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="language"')
        body.append(b"")
        body.append(b"en")

        # Add audio file
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="file"; filename="audio.wav"')
        body.append(b"Content-Type: audio/wav")
        body.append(b"")
        body.append(audio_data)

        body.append(f"--{boundary}--".encode())
        body.append(b"")

        body_bytes = b"\r\n".join(body)

        # Make request
        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/transcriptions",
            data=body_bytes,
            headers={
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                resp_data = json.loads(response.read().decode('utf-8'))
                transcript = resp_data.get("text", "").strip()
                logger.info(f"Transcribed {len(transcript)} characters")
                return transcript

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f"Whisper API error: {error_body}")
            raise RuntimeError(f"Whisper transcription failed: {error_body}")
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file, handling large files with chunking.

        Args:
            audio_path: Path to audio file

        Returns:
            Full transcribed text (concatenated from chunks if needed)
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Split if needed
        chunks = self._split_audio_file(audio_path)

        # Transcribe each chunk
        transcripts = []
        for i, chunk_path in enumerate(chunks):
            logger.info(f"Transcribing chunk {i+1}/{len(chunks)}")
            transcript = self._transcribe_audio_chunk(chunk_path)
            transcripts.append(transcript)

        # Concatenate
        full_text = " ".join(transcripts)
        return full_text

    # -----------------------------------------------------------------------
    # Full Intake Pipeline
    # -----------------------------------------------------------------------

    def process_for_intake(
        self,
        video_path: str,
        case_id: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> VideoIntakeResult:
        """
        Full video processing pipeline for intake:
          1. Probe video metadata
          2. Extract audio if present
          3. Transcribe audio
          4. Capture key frames
          5. Return structured result

        Args:
            video_path: Path to video file
            case_id: Case ID for intake
            progress_callback: Optional callback for progress updates

        Returns:
            VideoIntakeResult with transcript, frames, metadata
        """
        start_time = datetime.now(timezone.utc)

        def report(msg: str):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        try:
            # Validate video
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video not found: {video_path}")

            ext = Path(video_path).suffix.lower()
            if ext not in self.SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported format: {ext}. "
                    f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
                )

            filename = os.path.basename(video_path)
            report(f"Starting intake processing for {filename}")

            # Step 1: Probe
            report("Probing video metadata...")
            metadata = self.probe(video_path)

            # Step 2: Extract audio & transcribe
            transcript = ""
            segments: List[TranscriptSegment] = []

            if metadata.has_audio:
                report("Extracting audio...")
                audio_dir = tempfile.mkdtemp(prefix="video_audio_")
                audio_path = os.path.join(audio_dir, "extracted.wav")
                self.extract_audio(video_path, audio_path)

                report("Transcribing audio (this may take a while for long videos)...")
                transcript = self.transcribe_audio(audio_path)

                # Simple segment placeholder (Whisper API doesn't return segment timing in basic mode)
                if transcript:
                    segments.append(TranscriptSegment(
                        segment_id=new_id(),
                        start_time=0.0,
                        end_time=metadata.duration,
                        text=transcript,
                        confidence=0.90,
                    ))

                # Clean up
                try:
                    os.remove(audio_path)
                    os.rmdir(audio_dir)
                except Exception:
                    pass
            else:
                report("No audio track found in video")

            # Step 3: Capture frames
            report("Capturing key frames...")
            frame_paths = []
            try:
                # Determine frame interval (max 10 frames per minute)
                interval = max(1, metadata.duration / 10)
                frame_paths = self.capture_frames(video_path, interval_seconds=interval)
                report(f"Captured {len(frame_paths)} frames")
            except Exception as e:
                logger.warning(f"Frame capture failed (continuing): {e}")

            # Assemble result
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            result = VideoIntakeResult(
                video_id=new_id(),
                case_id=case_id,
                filename=filename,
                video_metadata=metadata,
                transcript=transcript or None,
                segments=segments,
                frame_paths=frame_paths,
                has_audio=metadata.has_audio,
                processed_at=datetime.now(timezone.utc),
                processing_duration_seconds=duration,
            )

            report(f"Intake processing complete ({duration:.1f}s)")
            return result

        except Exception as e:
            logger.error(f"Intake processing error: {e}")
            raise


# Global processor instance
_video_processor: Optional[VideoProcessor] = None


def get_video_processor() -> VideoProcessor:
    """Get or create the global video processor."""
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor()
    return _video_processor
