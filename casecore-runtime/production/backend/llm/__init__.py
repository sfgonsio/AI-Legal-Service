"""CaseCore LLM layer — provider-agnostic Claude(+OpenAI) abstraction.

Boots with no keys/SDKs; AI capabilities report unavailable until keys are set.
"""
from .config import LLMConfig, load_llm_config
from .providers import LLMNotConfigured, text_complete, vision_extract, transcribe, status

__all__ = [
    "LLMConfig",
    "load_llm_config",
    "LLMNotConfigured",
    "text_complete",
    "vision_extract",
    "transcribe",
    "status",
]
