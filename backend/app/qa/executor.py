import json
from typing import Dict, Any, List, Optional
from backend.app.llm.base import LLMProvider


class ActionExecutor:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def choose_next_action(
        self,
        mission: str,
        current_scenario: Dict[str, Any],
        dom_snapshot: str,
        recent_steps: List[Dict[str, Any]],
        coverage_summary: str,
        active_findings: List[str],
        action_count: int,
        max_actions: int
    ) -> Dict[str, Any]:
        """
        Determines the next atomic browser action or concludes the scenario.
        """
        system_prompt = """ROLE: EXECUTOR_ROLE
You are an expert Autonomous Browser Testing Agent.
Your job is to execute actions to test the given Scenario.

SAFETY GUIDELINES:
- Never perform destructive production operations (e.g. permanently deleting system account, real credit card transactions). If encountered, set is_completed=true and scenario_result="BLOCKED".

SUPPORTED ACTIONS:
- "click": target=selector or button/link text
- "fill": target=selector, value=text to enter
- "select": target=selector, value=option value or text
- "check": target=selector
- "uncheck": target=selector
- "press_key": value=key name (e.g. "Enter", "Tab", "Escape")
- "scroll": value="down" or "up"
- "back": go back in browser history
- "forward": go forward in browser history
- "reload": reload current page
- "wait": value=seconds (e.g. "1")
- "navigate": target=full url

WHEN SCENARIO IS FINISHED:
Set "is_completed": true, and "scenario_result": "PASSED" (if expected behavior was confirmed), "FAILED" (if unexpected behavior/bug found), or "BLOCKED".

Respond ONLY with valid JSON in this exact structure:
{
  "thought": "Reasoning for this action in context of the scenario",
  "action": "click | fill | select | check | uncheck | press_key | scroll | reload | wait | navigate",
  "target": "selector or element description (or null)",
  "value": "input string or parameter (or null)",
  "is_completed": false,
  "scenario_result": "PASSED | FAILED | BLOCKED"
}
"""

        recent_actions_str = ""
        if recent_steps:
            recent_actions_str = "\n".join([
                f"- Action: {s.get('action')}, Target: {s.get('target')}, Result: {s.get('result')}, URL: {s.get('url')}"
                for s in recent_steps[-7:]
            ])
        else:
            recent_actions_str = "No previous actions in this scenario."

        findings_str = "\n".join([f"- {f}" for f in active_findings]) if active_findings else "None"

        user_prompt = f"""Testing Mission:
{mission}

Current Active Scenario:
Title: {current_scenario.get('title')}
Description: {current_scenario.get('description')}
Area: {current_scenario.get('area')}
Priority: {current_scenario.get('priority')}

Budget Status: Action {action_count} of {max_actions}
Coverage Progress: {coverage_summary}

Recent Actions in Current Scenario:
{recent_actions_str}

Active Findings:
{findings_str}

Current Browser DOM Snapshot:
{dom_snapshot}
"""

        response = await self.llm.generate(system_prompt, user_prompt, json_mode=True)
        if response.parsed_json and "action" in response.parsed_json:
            return response.parsed_json

        # Fallback default action
        return {
            "thought": "Continuing exploratory interaction.",
            "action": "wait",
            "target": None,
            "value": "1",
            "is_completed": False,
            "scenario_result": "PASSED"
        }
