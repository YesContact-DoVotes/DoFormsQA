import json
from typing import Dict, Any, List, Optional
from backend.app.llm.base import LLMProvider


class ApplicationDiscovery:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def discover(self, base_url: str, dom_snapshot: str, requirements_text: str = "", mission: str = "") -> Dict[str, Any]:
        """
        Discovers key functional areas, navigation entry points, and forms in the application,
        giving strict priority to the user's explicit mission directive.
        """
        system_prompt = """ROLE: DISCOVERY_ROLE
You are an expert Autonomous QA Discovery Agent.
Your goal is to inspect the application snapshot and requirements to identify the core functional areas and navigation entry points needed to accomplish the user's mission.

CRITICAL INSTRUCTION:
- If the user's Mission specifies a specific page, feature, or workflow (e.g., 'templates', 'form builder', 'auth'), you MUST prioritize and highlight that area as the primary discovery target.

Respond ONLY with valid JSON in this exact structure:
{
  "areas": [
    {
      "name": "Area Name (e.g. Templates, Form Builder, Navigation)",
      "description": "Short description of what this area does and its relevance to the mission"
    }
  ],
  "summary": "Brief summary of discovered entry points for the mission"
}
"""
        user_prompt = f"""Base URL: {base_url}

User Mission Directive:
{mission if mission else 'Conduct full exploratory testing of the application.'}

Requirements / PRD:
{requirements_text if requirements_text else 'Standard web application testing'}

Initial DOM Snapshot:
{dom_snapshot}
"""
        response = await self.llm.generate(system_prompt, user_prompt, json_mode=True)
        if response.parsed_json and response.parsed_json.get("areas") and len(response.parsed_json["areas"]) > 0:
            return response.parsed_json
        
        # Fallback default areas
        return {
            "areas": [
                {"name": "Target Area", "description": f"Target area for mission: {mission or 'Main workflow'}"},
                {"name": "Core Navigation", "description": "Navigation links and page layout"},
                {"name": "Validation & Persistence", "description": "Data entry and state persistence"}
            ],
            "summary": "Discovered primary application areas."
        }
