import json
from typing import Dict, Any, List
from backend.app.llm.base import LLMProvider


class TestPlanner:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def generate_plan(
        self,
        mission: str,
        requirements_text: str,
        discovered_areas: List[Dict[str, Any]],
        dom_snapshot: str,
        target_routes: List[Dict[str, Any]] = None,
        base_url: str = "",
        max_scenarios: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Creates prioritized test scenarios strictly focused on the user's mission directive
        with explicit route path schemes.
        """
        system_prompt = f"""ROLE: PLANNER_ROLE
You are a Principal QA Automation and Exploratory Testing Architect.
Your task is to create a focused, actionable test plan containing 3 to {max_scenarios} prioritized test scenarios.

CRITICAL DIRECTIVES:
1. ROUTE SCHEME & TARGET PATH FIRST:
   - Identify the exact target URL path corresponding to the User Mission (e.g. mission mentions 'templates' -> target path is '/templates', direct URL is '{base_url.rstrip("/")}/templates').
   - Scenario 1 MUST BE: Navigate to target page (via header link/button or direct URL navigation) and verify complete page render.
2. SCENARIO PROGRESSION ON TARGET PAGE:
   - Scenario 2: Test primary interactions, template cards, forms, buttons, and filters on the target page.
   - Scenario 3: Test edge cases, modal dialogs, search queries, or negative states on the target page.
   - Scenario 4: Test state persistence and responsiveness on the target page.
3. STRICT MISSION FOCUS:
   - Do NOT wander off to unrelated pages (e.g. do not test pricing or feed if the user asked for templates).

Respond ONLY with valid JSON in this exact structure:
{{
  "scenarios": [
    {{
      "title": "Clear concise scenario title",
      "description": "What to do and what to verify. Include specific target URL/path and elements to inspect.",
      "area": "Target area name (e.g. Templates)",
      "priority": "HIGH" // or "MEDIUM" or "LOW"
    }}
  ]
}}
"""
        areas_str = json.dumps(discovered_areas, indent=2)
        routes_str = json.dumps(target_routes or [], indent=2)

        user_prompt = f"""PRIMARY USER MISSION DIRECTIVE:
{mission}

Base URL: {base_url}

Identified Target Routes & Paths:
{routes_str}

Discovered Application Areas:
{areas_str}

Requirements / PRD:
{requirements_text if requirements_text else 'Standard web application testing'}

Current DOM Snapshot:
{dom_snapshot}
"""
        response = await self.llm.generate(system_prompt, user_prompt, json_mode=True)
        if response.parsed_json and "scenarios" in response.parsed_json:
            scenarios = response.parsed_json["scenarios"]
            if isinstance(scenarios, list) and len(scenarios) > 0:
                return scenarios[:max_scenarios]

        # Inferred route fallback
        clean_base = base_url.rstrip("/")
        target_path = "/templates" if "template" in (mission or "").lower() else "/"
        return [
            {
                "title": f"Navigate to {target_path} and Verify Page Render",
                "description": f"Open {clean_base}{target_path} (via nav link or direct URL) and verify all main page components render.",
                "area": "Templates" if "template" in target_path else "Main Navigation",
                "priority": "HIGH"
            },
            {
                "title": f"Test Core Functionality on {target_path}",
                "description": "Interact with available cards, buttons, search inputs, and filters.",
                "area": "Templates" if "template" in target_path else "Interactive",
                "priority": "HIGH"
            },
            {
                "title": f"Verify State Persistence and Actions on {target_path}",
                "description": "Test clicking actions, dialogs, and verify that no error states appear.",
                "area": "Templates" if "template" in target_path else "Validation",
                "priority": "MEDIUM"
            }
        ]
