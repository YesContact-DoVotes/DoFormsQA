import os
import json
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from backend.app.llm.base import LLMProvider, LLMResponse
from backend.app.config import settings


class OpenAIProvider(LLMProvider):
    """
    OpenAI Provider using official openai Python SDK (supports OpenAI, Codex sandbox, Azure, Ollama, OpenRouter).
    Works with or without explicit API key (defaults to environment or proxy sandbox).
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        # Fallback to env or dummy if in sandbox environment
        key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY") or "sandbox"
        base = base_url or settings.OPENAI_BASE_URL or os.getenv("OPENAI_BASE_URL")

        client_kwargs: Dict[str, Any] = {"api_key": key}
        if base and base != "https://api.openai.com/v1":
            client_kwargs["base_url"] = base

        self.client = AsyncOpenAI(**client_kwargs)
        self.model = model or settings.OPENAI_MODEL or "gpt-4o"

    async def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False, temperature: float = 0.2) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        content = choice.message.content or ""
        
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else len(system_prompt + user_prompt) // 4
        output_tokens = usage.completion_tokens if usage else len(content) // 4

        parsed_json = None
        if json_mode and content:
            try:
                parsed_json = json.loads(content)
            except Exception:
                cleaned = content.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                try:
                    parsed_json = json.loads(cleaned.strip())
                except Exception:
                    parsed_json = {"raw": content}

        cost = self.calculate_cost(self.model, input_tokens, output_tokens)

        return LLMResponse(
            content=content,
            parsed_json=parsed_json,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost
        )
