import json
import re
from typing import Dict, Any, Optional
from backend.app.llm.base import LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    """
    Intelligent heuristic mock LLM provider for testing and offline runs.
    Inspects system/user prompts to determine the AI role and returns realistic responses.
    """
    def __init__(self, model: str = "mock-qa-engine"):
        self.model = model

    async def generate(self, system_prompt: str, user_prompt: str, json_mode: bool = False, temperature: float = 0.2) -> LLMResponse:
        input_tokens = len(system_prompt + user_prompt) // 4
        
        parsed_json: Optional[Dict[str, Any]] = None
        content = ""

        # Check which role is requesting
        if "DISCOVERY_ROLE" in system_prompt or "discover application" in system_prompt.lower():
            parsed_json = {
                "areas": [
                    {"name": "Authentication", "description": "User login, signup, session control"},
                    {"name": "Form Builder", "description": "Form creation, editing questions, fields, settings"},
                    {"name": "Form Responses", "description": "Viewing submissions, export data"},
                    {"name": "Navigation & UI", "description": "Header navigation, responsive layout, dark mode"},
                    {"name": "Form Publishing", "description": "Publish form, public link, form validation"}
                ],
                "summary": "Discovered 5 key functional areas in the application."
            }
            content = json.dumps(parsed_json)

        elif "PLANNER_ROLE" in system_prompt or "generate test plan" in system_prompt.lower() or "scenarios" in system_prompt.lower():
            parsed_json = {
                "scenarios": [
                    {
                        "title": "Login with valid credentials",
                        "description": "Authenticate using registered account credentials",
                        "area": "Authentication",
                        "priority": "HIGH"
                    },
                    {
                        "title": "Login with invalid password",
                        "description": "Verify error message when entering wrong password",
                        "area": "Authentication",
                        "priority": "MEDIUM"
                    },
                    {
                        "title": "Create new form",
                        "description": "Create a new form with custom title and initial question",
                        "area": "Form Builder",
                        "priority": "HIGH"
                    },
                    {
                        "title": "Empty field validation on submit",
                        "description": "Verify form cannot be saved without required title",
                        "area": "Form Builder",
                        "priority": "HIGH"
                    },
                    {
                        "title": "Form persistence after page reload",
                        "description": "Verify created form and added questions persist across browser reload",
                        "area": "Form Builder",
                        "priority": "HIGH"
                    },
                    {
                        "title": "Add and delete form questions",
                        "description": "Add multiple questions of different types and delete one",
                        "area": "Form Builder",
                        "priority": "MEDIUM"
                    },
                    {
                        "title": "Publish form and verify public URL",
                        "description": "Publish form and open the public response view",
                        "area": "Form Publishing",
                        "priority": "HIGH"
                    },
                    {
                        "title": "Submit response with invalid email",
                        "description": "Ensure email field validates format on public form submit",
                        "area": "Form Responses",
                        "priority": "MEDIUM"
                    },
                    {
                        "title": "Inspect console errors on main pages",
                        "description": "Navigate through main tabs and assert no uncaught JavaScript exceptions",
                        "area": "Navigation & UI",
                        "priority": "LOW"
                    }
                ]
            }
            content = json.dumps(parsed_json)

        elif "EXECUTOR_ROLE" in system_prompt or "choose next browser action" in system_prompt.lower():
            # Heuristic action selection based on interactive elements in the prompt
            action = "click"
            target = "button"
            value = None
            is_completed = False
            scenario_result = "PASSED"
            thought = "Exploring UI element according to active scenario."

            # Check if elements are listed
            if "selector=" in user_prompt:
                # Find first suitable interactive element
                matches = re.findall(r"selector='([^']+)'", user_prompt)
                labels = re.findall(r"label='([^']+)'", user_prompt)
                
                # Check recent actions count
                if "Recent Actions (5" in user_prompt or "Recent Actions (4" in user_prompt or "Recent Actions (3" in user_prompt:
                    is_completed = True
                    thought = "Completed the required scenario steps successfully."
                elif matches:
                    target = matches[0]
                    if "input" in target or "textarea" in target or "search" in target:
                        action = "fill"
                        value = "Test Form Title " + str(input_tokens % 100)
                    elif "reload" in user_prompt.lower() and "persistence" in user_prompt.lower():
                        action = "reload"
                        target = None
                    else:
                        action = "click"
                        if labels:
                            thought = f"Clicking {labels[0]} to proceed."
            else:
                action = "wait"
                value = "1"

            parsed_json = {
                "thought": thought,
                "action": action,
                "target": target,
                "value": value,
                "is_completed": is_completed,
                "scenario_result": scenario_result
            }
            content = json.dumps(parsed_json)

        elif "ANALYZER_ROLE" in system_prompt or "analyze result" in system_prompt.lower():
            # Check if console error or 404/500 occurred in user_prompt
            has_error = "console_errors" in user_prompt and "error" in user_prompt.lower()
            
            if has_error:
                parsed_json = {
                    "is_finding": True,
                    "title": "Uncaught JavaScript error during form interaction",
                    "description": "A console error was triggered while executing user action.",
                    "type": "CONSOLE_ERROR",
                    "severity": "HIGH",
                    "expected_behavior": "Action should complete without uncaught JavaScript exceptions",
                    "actual_behavior": "Console error detected in browser runtime",
                    "reproduction_steps": "1. Navigate to page\n2. Perform action\n3. Check console logs"
                }
            else:
                parsed_json = {
                    "is_finding": False,
                    "comment": "Action completed as expected with no critical UI or runtime errors."
                }
            content = json.dumps(parsed_json)

        elif "VERIFIER_ROLE" in system_prompt or "verify finding" in system_prompt.lower():
            parsed_json = {
                "reproduced": True,
                "status": "CONFIRMED",
                "notes": "Problem consistently reproduced across independent verification cycles."
            }
            content = json.dumps(parsed_json)

        elif "REPORTER_ROLE" in system_prompt or "generate report" in system_prompt.lower():
            content = """# QA Autonomous Test Session Report

## Summary
- **Session Status**: Completed
- **Testing Approach**: Autonomous Exploratory & E2E Validation
- **Quality Score**: 92 / 100

## Coverage Analysis
- **Authentication**: 2 / 2 scenarios tested (100%)
- **Form Builder**: 4 / 4 scenarios tested (100%)
- **Form Publishing**: 1 / 1 scenarios tested (100%)
- **Form Responses**: 1 / 1 scenarios tested (100%)
- **Navigation & UI**: 1 / 1 scenarios tested (100%)

## Key Findings & Verification
- Validated core happy paths and negative validation handling.
- Monitored network traffic and console errors throughout all exploratory steps.

## Regression Test Suite
Generated Playwright regression specifications for key flows and confirmed bugs.
"""
            parsed_json = {"report_markdown": content}

        elif "REGRESSION_ROLE" in system_prompt or "generate playwright test" in system_prompt.lower():
            content = """import { test, expect } from '@playwright/test';

test('verify form creation and persistence', async ({ page }) => {
  await page.goto('/');
  
  // Locate create form trigger
  const createBtn = page.getByRole('button', { name: /create|new/i });
  if (await createBtn.isVisible()) {
    await createBtn.click();
  }

  // Check form inputs
  const titleInput = page.locator('input[placeholder*="title" i], input[type="text"]').first();
  if (await titleInput.isVisible()) {
    await titleInput.fill('Automated Regression Form');
  }

  // Reload and verify persistence
  await page.reload();
  await expect(page.locator('body')).not.toBeEmpty();
});
"""
            parsed_json = {"test_name": "form_persistence.spec.ts", "test_code": content}

        else:
            content = "Mock response completed."
            parsed_json = {"status": "ok", "message": content}

        output_tokens = len(content) // 4
        return LLMResponse(
            content=content,
            parsed_json=parsed_json if json_mode else None,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=0.0
        )
