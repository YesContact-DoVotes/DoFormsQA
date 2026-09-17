import abc
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class LLMResponse(BaseModel):
    content: str
    parsed_json: Optional[Dict[str, Any]] = None
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False, temperature: float = 0.2) -> LLMResponse:
        """Generates a completion from the LLM provider."""
        pass

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimates cost based on standard model pricing."""
        model_lower = model.lower()
        if "gpt-4o-mini" in model_lower:
            return (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
        elif "gpt-4o" in model_lower:
            return (input_tokens * 2.50 + output_tokens * 10.00) / 1_000_000
        elif "claude-3-5-sonnet" in model_lower:
            return (input_tokens * 3.00 + output_tokens * 15.00) / 1_000_000
        elif "gemini-1.5-pro" in model_lower:
            return (input_tokens * 1.25 + output_tokens * 5.00) / 1_000_000
        elif "gemini-1.5-flash" in model_lower:
            return (input_tokens * 0.075 + output_tokens * 0.30) / 1_000_000
        else:
            # Fallback estimation
            return (input_tokens * 1.0 + output_tokens * 3.0) / 1_000_000
