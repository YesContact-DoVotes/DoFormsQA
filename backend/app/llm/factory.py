from typing import Optional
from backend.app.config import settings
from backend.app.llm.base import LLMProvider
from backend.app.llm.openai_provider import OpenAIProvider
from backend.app.llm.gemini_provider import GeminiProvider
from backend.app.llm.mock_provider import MockProvider


def get_llm_provider(provider_name: Optional[str] = None, model: Optional[str] = None) -> LLMProvider:
    provider = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()

    if provider == "openai":
        return OpenAIProvider(model=model)
    elif provider == "gemini":
        return GeminiProvider(model=model)
    elif provider == "mock":
        return MockProvider(model=model or "mock-qa-engine")
    else:
        # If unknown or fallback, check if OPENAI_API_KEY is present, otherwise use mock
        if settings.OPENAI_API_KEY:
            return OpenAIProvider(model=model)
        elif settings.GEMINI_API_KEY:
            return GeminiProvider(model=model)
        return MockProvider(model=model or "mock-qa-engine")
