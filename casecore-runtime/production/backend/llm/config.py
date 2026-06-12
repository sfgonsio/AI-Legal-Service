"""LLM configuration — provider-agnostic, resilient.

Reads keys + model routing from the environment. NEVER hard-codes secrets.
The app must import and boot with NO keys present (the AI capabilities simply
report unavailable until keys are provided), so nothing here imports a vendor
SDK at module load.

Architecture (see memory: architecture-and-llm-decisions):
  - Anthropic Claude = primary reasoning + citations engine (Opus/Sonnet/Haiku).
  - OpenAI = embeddings (RAG index) + Whisper transcription + fallback.
  - RAG grounds answers in OUR canonical sources for auditable traceability.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v else default


@dataclass(frozen=True)
class LLMConfig:
    anthropic_api_key: str | None
    openai_api_key: str | None
    # Claude tiers
    reasoning_model: str
    routine_model: str
    bulk_model: str
    vision_model: str
    # OpenAI utility models
    embedding_model: str
    transcription_model: str

    @property
    def anthropic_available(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def openai_available(self) -> bool:
        return bool(self.openai_api_key)

    def status(self) -> dict:
        """Safe, key-free summary for a health/status endpoint."""
        return {
            "anthropic_configured": self.anthropic_available,
            "openai_configured": self.openai_available,
            "reasoning_model": self.reasoning_model,
            "routine_model": self.routine_model,
            "bulk_model": self.bulk_model,
            "vision_model": self.vision_model,
            "embedding_model": self.embedding_model,
            "transcription_model": self.transcription_model,
        }


def load_llm_config() -> LLMConfig:
    return LLMConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        reasoning_model=_env("CASECORE_REASONING_MODEL", "claude-opus-4-8"),
        routine_model=_env("CASECORE_ROUTINE_MODEL", "claude-sonnet-4-6"),
        bulk_model=_env("CASECORE_BULK_MODEL", "claude-haiku-4-5-20251001"),
        vision_model=_env("CASECORE_VISION_MODEL", "claude-sonnet-4-6"),
        embedding_model=_env("CASECORE_EMBEDDING_MODEL", "text-embedding-3-large"),
        transcription_model=_env("CASECORE_TRANSCRIPTION_MODEL", "whisper-1"),
    )
