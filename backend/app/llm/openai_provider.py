import json
import httpx
from typing import Optional, Dict, Any
from backend.app.llm.base import LLMProvider, LLMResponse
from backend.app.config import settings


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.model = model or settings.OPENAI_MODEL

    async def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False, temperature: float = 0.2) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OpenAI API Key is missing. Please configure OPENAI_API_KEY.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                raise RuntimeError(f"OpenAI API Error ({response.status_code}): {response.text}")
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            parsed_json = None
            if json_mode:
                try:
                    parsed_json = json.loads(content)
                except Exception:
                    # Clean markdown code blocks if any
                    cleaned = content.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    if cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    parsed_json = json.loads(cleaned.strip())

            cost = self.calculate_cost(self.model, input_tokens, output_tokens)

            return LLMResponse(
                content=content,
                parsed_json=parsed_json,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=cost
            )
