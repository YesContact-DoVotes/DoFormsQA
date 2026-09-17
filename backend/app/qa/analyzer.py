import json
from typing import Dict, Any, List, Optional
from backend.app.llm.base import LLMProvider


class ActionAnalyzer:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.action_history: List[str] = []

    def check_loop(self, url: str, action: str, target: Optional[str]) -> bool:
        """
        Calculates action fingerprint and detects if the same action was repeated 3+ times in a row.
        """
        fingerprint = f"{url}|{action}|{target or ''}"
        self.action_history.append(fingerprint)
        if len(self.action_history) >= 3:
            last_three = self.action_history[-3:]
            if len(set(last_three)) == 1:
                return True
        return False

    async def analyze_step(
        self,
        scenario: Dict[str, Any],
        action_executed: Dict[str, Any],
        action_result: Dict[str, Any],
        console_errors: List[Dict[str, Any]],
        network_errors: List[Dict[str, Any]],
        dom_snapshot: str,
        requirements_text: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluates step outcome and detects if a POTENTIAL finding has occurred.
        """
        # Quick rule check for severe network/console crashes
        has_500 = any(n.get("status", 0) >= 500 for n in network_errors)
        has_pageerror = any(c.get("type") == "pageerror" for c in console_errors)

        system_prompt = """ROLE: ANALYZER_ROLE
You are a Senior QA Bug Analyzer.
Analyze the executed action, result, browser console logs, network errors, and new DOM state.

Detect if there is an anomaly or issue:
- BUG: Unexpected behavior, broken form, broken state persistence, crashes.
- CONSOLE_ERROR: Relevant JavaScript errors or uncaught exceptions.
- NETWORK_ERROR: 500 Internal Server Error or critical 4xx API failures.
- MISSING_FUNCTIONALITY: Documented requirement that is missing from UI.
- UX_ISSUE: Confusing state, button enabled when invalid, layout breakage.

Respond ONLY with valid JSON in this exact structure:
{
  "is_finding": true | false,
  "title": "Short descriptive title of the issue",
  "description": "Clear explanation of what went wrong",
  "type": "BUG | CONSOLE_ERROR | NETWORK_ERROR | MISSING_FUNCTIONALITY | UX_ISSUE",
  "severity": "CRITICAL | HIGH | MEDIUM | LOW",
  "expected_behavior": "What was expected according to requirements/good UX",
  "actual_behavior": "What actually occurred",
  "reproduction_steps": "1. Step one\\n2. Step two\\n3. Step three",
  "comment": "Analysis notes"
}
"""

        user_prompt = f"""Scenario: {scenario.get('title')} ({scenario.get('area')})
Action: {json.dumps(action_executed)}
Result: {json.dumps(action_result)}

Console Errors ({len(console_errors)}):
{json.dumps(console_errors, indent=2)}

Network Errors ({len(network_errors)}):
{json.dumps(network_errors, indent=2)}

Requirements / Expectations:
{requirements_text if requirements_text else 'Standard web application stability'}

Current DOM Snapshot:
{dom_snapshot}
"""

        response = await self.llm.generate(system_prompt, user_prompt, json_mode=True)
        if response.parsed_json and "is_finding" in response.parsed_json:
            finding_data = response.parsed_json
            if finding_data["is_finding"]:
                return finding_data

        # Explicit fallback if severe network or pageerror was detected
        if has_500:
            return {
                "is_finding": True,
                "title": "Server Error (HTTP 500) during action",
                "description": f"Encountered internal server error on {action_result.get('url')}",
                "type": "NETWORK_ERROR",
                "severity": "HIGH",
                "expected_behavior": "API requests should succeed (2xx)",
                "actual_behavior": f"Received HTTP 500 error: {json.dumps(network_errors)}",
                "reproduction_steps": f"1. Navigate to {action_result.get('url')}\n2. Perform {action_executed.get('action')}",
                "comment": "Auto-flagged from network monitor"
            }
        elif has_pageerror:
            return {
                "is_finding": True,
                "title": "Uncaught Page Error in JavaScript runtime",
                "description": "An uncaught runtime exception crashed script execution on the page.",
                "type": "CONSOLE_ERROR",
                "severity": "HIGH",
                "expected_behavior": "Application scripts should run without uncaught page errors",
                "actual_behavior": f"Page error: {json.dumps(console_errors)}",
                "reproduction_steps": f"1. Open {action_result.get('url')}\n2. Execute {action_executed.get('action')}",
                "comment": "Auto-flagged from console monitor"
            }

        return {"is_finding": False, "comment": "No anomaly detected."}
