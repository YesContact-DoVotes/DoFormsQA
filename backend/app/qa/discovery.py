import json
from typing import Dict, Any, List, Optional
from backend.app.llm.base import LLMProvider


class ApplicationDiscovery:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def discover(self, base_url: str, dom_snapshot: str, requirements_text: str = "", mission: str = "") -> Dict[str, Any]:
        """
        Discovers key functional areas, navigation entry points, route paths, and forms in the application,
        giving strict priority to the user's explicit mission directive.
        """
        system_prompt = """ROLE: DISCOVERY_ROLE
You are an expert Autonomous QA Discovery Agent.
Your goal is to inspect the application snapshot, extract route paths (e.g., /templates, /dashboard, /forms, /feed, /settings), and identify the functional areas required to accomplish the user's mission.

CRITICAL INSTRUCTIONS:
1. ROUTE & PATH EXTRACTION:
   - Identify candidate URL paths and navigation links (e.g. if the user wants 'templates', map it to '/templates' and the corresponding nav buttons/links).
2. MISSION ALIGNMENT:
   - If the user's Mission specifies a specific page, feature, or workflow (e.g., 'templates', 'form builder', 'auth'), prioritize and highlight that route and area as the primary discovery target.

Respond ONLY with valid JSON in this exact structure:
{
  "target_routes": [
    {
      "name": "Route Name (e.g. Templates Page)",
      "path": "/templates",
      "full_url": "full url if known",
      "nav_selector": "selector or link text in DOM if present"
    }
  ],
  "areas": [
    {
      "name": "Area Name (e.g. Templates, Form Builder, Navigation)",
      "description": "Short description of what this area does and its relevance to the mission"
    }
  ],
  "summary": "Brief summary of discovered routes and entry points for the mission"
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
        
        # Fallback default areas and inferred path
        inferred_path = "/templates" if "template" in (mission or "").lower() else "/"
        return {
            "target_routes": [
                {"name": "Target Page", "path": inferred_path, "full_url": f"{base_url.rstrip('/')}{inferred_path}", "nav_selector": "a, button"}
            ],
            "areas": [
                {"name": "Target Area", "description": f"Target area for mission: {mission or 'Main workflow'}"},
                {"name": "Core Navigation", "description": "Navigation links and page layout"},
                {"name": "Validation & Persistence", "description": "Data entry and state persistence"}
            ],
            "summary": "Discovered primary application routes and areas."
        }
