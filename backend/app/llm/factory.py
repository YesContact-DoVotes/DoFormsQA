from typing import Optional
from loguru import logger
from backend.app.config import settings
from backend.app.llm.base import LLMProvider
from backend.app.llm.openai_provider import CodexProvider, OpenAIProvider
from backend.app.llm.gemini_provider import GeminiProvider


def get_llm_provider(provider_name: Optional[str] = None, model: Optional[str] = None) -> LLMProvider:
    """
    Returns the configured LLM Provider.
    Default: Codex Sandbox provider (openai_codex).
    """
    provider = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()

    if provider in ["codex", "openai", "openai-codex", "openai_codex"]:
        return CodexProvider(model=model or settings.OPENAI_MODEL)
    elif provider == "gemini":
        return GeminiProvider(model=model or settings.GEMINI_MODEL)
    else:
        # Default to CodexProvider
        return CodexProvider(model=model or settings.OPENAI_MODEL)
