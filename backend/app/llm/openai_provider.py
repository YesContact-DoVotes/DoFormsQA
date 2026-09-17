import json
import asyncio
from typing import Optional, Dict, Any
from loguru import logger
from openai_codex import Codex
from backend.app.llm.base import LLMProvider, LLMResponse
from backend.app.config import settings


class CodexProvider(LLMProvider):
    """
    OpenAI & Codex Sandbox Provider using `openai_codex`.
    Executes prompt interactions via `from openai_codex import Codex` with `with Codex() as codex:`.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None, effort: Optional[str] = None):
        self.model = model or settings.OPENAI_MODEL or "gpt-5.6-luna"
        self.effort = effort or getattr(settings, "CODEX_REASONING_EFFORT", "low") or "low"

    def _sync_generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False, temperature: float = 0.2) -> LLMResponse:
        system_instr = system_prompt
        if json_mode:
            system_instr += "\nCRITICAL: Respond ONLY with a valid JSON object. No Markdown fences, no explanation text outside the JSON."

        logger.info(f"Invoking Codex Sandbox LLM (model={self.model}, effort={self.effort}, json_mode={json_mode})")
        with Codex() as codex:
            thread = codex.thread_start(model=self.model, developer_instructions=system_instr)
            turn_result = thread.run(user_prompt, effort=self.effort)

            content = turn_result.final_response or ""
            
            # Extract token usage
            input_tokens = 0
            output_tokens = 0
            if turn_result.usage and hasattr(turn_result.usage, "last") and turn_result.usage.last:
                input_tokens = getattr(turn_result.usage.last, "input_tokens", 0) or 0
                output_tokens = getattr(turn_result.usage.last, "output_tokens", 0) or 0

            if not input_tokens:
                input_tokens = len(system_prompt + user_prompt) // 4
            if not output_tokens:
                output_tokens = len(content) // 4

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
            logger.info(f"Codex Sandbox response received (tokens: in={input_tokens}, out={output_tokens})")

            return LLMResponse(
                content=content,
                parsed_json=parsed_json,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=cost
            )

    async def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False, temperature: float = 0.2) -> LLMResponse:
        return await asyncio.to_thread(self._sync_generate, system_prompt, user_prompt, json_mode, temperature)


# Backward-compatible alias for factory & legacy imports
OpenAIProvider = CodexProvider
