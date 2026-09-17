import json
import asyncio
from typing import Dict, Any, List, Optional
from backend.app.llm.base import LLMProvider
from backend.app.browser.manager import BrowserManager
from backend.app.models.finding import FindingStatus


class BugVerifier:
    def __init__(self, llm: LLMProvider, browser: BrowserManager):
        self.llm = llm
        self.browser = browser

    async def verify_finding(
        self,
        finding: Dict[str, Any],
        base_url: str,
        steps_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes reproduction cycle from a clean state to verify potential bugs.
        """
        attempts = 2
        reproduced_count = 0

        for attempt in range(1, attempts + 1):
            try:
                # Reload / reset to base URL
                await self.browser.navigate(base_url)
                await asyncio.sleep(0.5)

                # Re-execute key recent steps
                for step in steps_history[-4:]:
                    action = step.get("action", "")
                    target = step.get("target")
                    val = step.get("value")
                    if action:
                        await self.browser.execute_action(action, target, val)
                        await asyncio.sleep(0.3)

                # Capture state after reproduction run
                state = await self.browser.get_state()
                console_errors = state.get("console_errors", [])
                network_errors = state.get("network_errors", [])
                dom_snapshot = state.get("formatted_dom", "")

                system_prompt = """ROLE: VERIFIER_ROLE
You are an expert QA Bug Verification Agent.
You are evaluating whether a potential bug was reproduced during an isolated replay.

Respond ONLY with valid JSON:
{
  "reproduced": true | false,
  "status": "CONFIRMED | REJECTED | VERIFYING",
  "notes": "Detailed verification notes"
}
"""
                user_prompt = f"""Finding to Verify:
Title: {finding.get('title')}
Description: {finding.get('description')}
Type: {finding.get('type')}
Expected: {finding.get('expected_behavior')}
Actual: {finding.get('actual_behavior')}

Reproduction Attempt #{attempt} State:
Console Errors: {json.dumps(console_errors)}
Network Errors: {json.dumps(network_errors)}
DOM Snapshot:
{dom_snapshot}
"""
                response = await self.llm.generate(system_prompt, user_prompt, json_mode=True)
                if response.parsed_json and response.parsed_json.get("reproduced"):
                    reproduced_count += 1
                elif len(console_errors) > 0 or len(network_errors) > 0:
                    reproduced_count += 1
            except Exception:
                pass

        final_reproduced = reproduced_count >= 1
        final_status = FindingStatus.CONFIRMED.value if final_reproduced else FindingStatus.REJECTED.value

        return {
            "reproduction_attempts": attempts,
            "reproduced": final_reproduced,
            "status": final_status,
            "notes": f"Verification completed ({reproduced_count}/{attempts} attempts confirmed problem)."
        }
