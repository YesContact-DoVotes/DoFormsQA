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
        max_scenarios: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Creates prioritized initial test scenarios (10–30 scenarios).
        """
        system_prompt = f"""ROLE: PLANNER_ROLE
You are a Principal QA Automation and Exploratory Testing Architect.
Your task is to create a comprehensive test plan containing 10 to {max_scenarios} prioritized test scenarios.

Requirements for the test plan:
1. Cover both Main Happy Paths and Negative Cases (empty inputs, invalid values, special chars, double clicks).
2. Include Persistence testing (create -> modify -> reload -> verify state remains).
3. Include Navigation & UI consistency (back/forward, direct URLs, dialogs, button disabled states).
4. Assign appropriate areas and priorities (HIGH, MEDIUM, LOW).

Respond ONLY with valid JSON in this exact structure:
{{
  "scenarios": [
    {{
      "title": "Clear concise scenario title",
      "description": "What to do and what to verify",
      "area": "Name of the area (e.g. Authentication, Form Builder, etc.)",
      "priority": "HIGH" // or "MEDIUM" or "LOW"
    }}
  ]
}}
"""
        areas_str = json.dumps(discovered_areas, indent=2)
        user_prompt = f"""Mission:
{mission}

Requirements / PRD:
{requirements_text if requirements_text else 'Standard web application exploratory testing'}

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

        # Fallback scenarios
        return [
            {
                "title": "Verify main page elements and navigation",
                "description": "Inspect header links, buttons, and responsive elements on homepage",
                "area": "Navigation & UI",
                "priority": "HIGH"
            },
            {
                "title": "Create new entity with valid inputs",
                "description": "Fill all required fields and submit form, check success confirmation",
                "area": "Form Builder",
                "priority": "HIGH"
            },
            {
                "title": "Submit form with empty required fields",
                "description": "Trigger submit on empty form and verify client-side validation errors",
                "area": "Form Builder",
                "priority": "HIGH"
            },
            {
                "title": "Verify data persistence after page reload",
                "description": "Modify inputs or create item, reload browser, verify changes remain",
                "area": "Form Builder",
                "priority": "HIGH"
            },
            {
                "title": "Inspect console and network errors during interactions",
                "description": "Perform typical clicks and verify no uncaught exceptions",
                "area": "Navigation & UI",
                "priority": "MEDIUM"
            }
        ]
