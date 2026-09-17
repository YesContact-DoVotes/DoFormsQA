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
        max_scenarios: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Creates prioritized test scenarios strictly focused on the user's mission directive.
        """
        system_prompt = f"""ROLE: PLANNER_ROLE
You are a Principal QA Automation and Exploratory Testing Architect.
Your task is to create a focused, actionable test plan containing 3 to {max_scenarios} prioritized test scenarios.

CRITICAL DIRECTIVES:
1. THE USER MISSION IS YOUR SUPREME GOAL. 
   - If the user asked to test a specific page, tab, or feature (e.g. 'templates', 'login', 'create form'), ALL scenarios MUST directly focus on that specific target!
   - Do NOT generate unrelated scenarios for other pages if the user gave a specific mission.
2. Structure the scenarios logically to accomplish the mission:
   - Scenario 1: Navigate to the target area/page specified in the mission and verify initial render.
   - Scenario 2: Test primary functionality, buttons, inputs, and happy paths within the target area.
   - Scenario 3: Test negative cases, validation, edge cases, or error handling within the target area.
   - Scenario 4+: Test persistence, state changes, and interactions relevant to the mission.
3. Assign priorities (HIGH, MEDIUM, LOW).

Respond ONLY with valid JSON in this exact structure:
{{
  "scenarios": [
    {{
      "title": "Clear concise scenario title",
      "description": "What to do and what to verify (step-by-step)",
      "area": "Target area name",
      "priority": "HIGH" // or "MEDIUM" or "LOW"
    }}
  ]
}}
"""
        areas_str = json.dumps(discovered_areas, indent=2)
        user_prompt = f"""PRIMARY USER MISSION DIRECTIVE:
{mission}

Requirements / PRD:
{requirements_text if requirements_text else 'Standard web application testing'}

Discovered Application Areas:
{areas_str}

Current DOM Snapshot:
{dom_snapshot}
"""
        response = await self.llm.generate(system_prompt, user_prompt, json_mode=True)
        if response.parsed_json and "scenarios" in response.parsed_json:
            scenarios = response.parsed_json["scenarios"]
            if isinstance(scenarios, list) and len(scenarios) > 0:
                return scenarios[:max_scenarios]

        # Fallback plan tailored to mission
        return [
            {
                "title": f"Navigate and Verify {mission[:40]}",
                "description": f"Open target section and verify UI elements for: {mission}",
                "area": "Target Module",
                "priority": "HIGH"
            },
            {
                "title": f"Interactive Functionality Testing for {mission[:40]}",
                "description": "Test primary user actions, buttons, and state updates.",
                "area": "Target Module",
                "priority": "HIGH"
            }
        ]
