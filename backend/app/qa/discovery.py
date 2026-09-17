import json
from typing import Dict, Any, List
from backend.app.llm.base import LLMProvider


class ApplicationDiscovery:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def discover(self, base_url: str, dom_snapshot: str, requirements_text: str = "") -> Dict[str, Any]:
        """
        Discovers key functional areas, navigation entry points, and forms in the application.
        """
        system_prompt = """ROLE: DISCOVERY_ROLE
You are an expert Autonomous QA Discovery Agent.
Your goal is to inspect the application snapshot and requirements to identify the core functional areas, modules, and workflows.

Respond ONLY with valid JSON in this exact structure:
{
  "areas": [
    {
      "name": "Area Name (e.g. Authentication, Form Builder, Navigation)",
      "description": "Short description of what this area does"
    }
  ],
  "summary": "Brief summary of discovered entry points"
}
"""
        user_prompt = f"""Base URL: {base_url}

Requirements / PRD:
{requirements_text if requirements_text else 'No specific PRD provided. Explore all available interactive features.'}

Initial DOM Snapshot:
{dom_snapshot}
"""
        response = await self.llm.generate(system_prompt, user_prompt, json_mode=True)
        if response.parsed_json and "areas" in response.parsed_json:
            return response.parsed_json
        
        # Fallback default areas
        return {
            "areas": [
                {"name": "Core Navigation", "description": "Navigation links and page layout"},
                {"name": "Main Interactive Area", "description": "Primary buttons, forms, and inputs"},
                {"name": "Validation & Persistence", "description": "Data entry and state persistence"}
            ],
            "summary": "Discovered primary application areas."
        }
