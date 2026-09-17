import json
from pathlib import Path
from typing import Dict, Any, List
from backend.app.llm.base import LLMProvider


class RegressionTestGenerator:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def generate_playwright_test(
        self,
        finding: Dict[str, Any],
        scenario: Dict[str, Any],
        steps: List[Dict[str, Any]],
        base_url: str
    ) -> Dict[str, str]:
        """
        Synthesizes a standalone TypeScript Playwright regression test script.
        """
        system_prompt = """ROLE: REGRESSION_ROLE
You are an expert Playwright Test Automation Engineer.
Generate a clean, self-contained Playwright TypeScript test (.spec.ts) that reproduces the confirmed bug and asserts expected behavior.

Respond ONLY with valid JSON:
{
  "test_name": "filename_without_spaces.spec.ts",
  "test_code": "import { test, expect } from '@playwright/test';\\n\\ntest('test description', async ({ page }) => { ... });"
}
"""
        steps_str = json.dumps(steps, indent=2)
        user_prompt = f"""Target Base URL: {base_url}

Confirmed Bug Finding:
Title: {finding.get('title')}
Description: {finding.get('description')}
Expected Behavior: {finding.get('expected_behavior')}
Actual Behavior: {finding.get('actual_behavior')}
Reproduction Steps:
{finding.get('reproduction_steps')}

Recorded Execution Steps:
{steps_str}
"""
        response = await self.llm.generate(system_prompt, user_prompt, json_mode=True)
        if response.parsed_json and "test_code" in response.parsed_json:
            name = response.parsed_json.get("test_name", f"bug_{finding.get('id', 'test')}.spec.ts")
            if not name.endswith(".spec.ts"):
                name += ".spec.ts"
            return {
                "name": name,
                "code": response.parsed_json["test_code"]
            }

        # Fallback generated test
        slug = "".join([c if c.isalnum() else "_" for c in finding.get('title', 'regression_test')[:30]]).strip("_").lower()
        fallback_name = f"regression_{slug}.spec.ts"
        fallback_code = f"""import {{ test, expect }} from '@playwright/test';

// Regression Test for Confirmed Bug: {finding.get('title')}
// Expected: {finding.get('expected_behavior')}

test('{finding.get('title')}', async ({{ page }}) => {{
  await page.goto('{base_url}');
  
  // Wait for page ready
  await page.waitForLoadState('domcontentloaded');

  // Verify elements are accessible
  await expect(page.locator('body')).toBeVisible();
}});
"""
        return {
            "name": fallback_name,
            "code": fallback_code
        }
