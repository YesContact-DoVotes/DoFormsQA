import json
import httpx
from typing import Optional, Dict, Any
from backend.app.llm.base import LLMProvider, LLMResponse
from backend.app.config import settings


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    async def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False, temperature: float = 0.2) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Gemini API Key is missing. Please configure GEMINI_API_KEY.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload: Dict[str, Any] = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Gemini API Error ({response.status_code}): {response.text}")

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("No candidate response from Gemini API")

            content = candidates[0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", len(system_prompt + user_prompt) // 4)
            output_tokens = usage.get("candidatesTokenCount", len(content) // 4)

            parsed_json = None
            if json_mode:
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
