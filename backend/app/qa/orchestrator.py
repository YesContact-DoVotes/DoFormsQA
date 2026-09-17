import asyncio
import datetime
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.config import settings
from backend.app.database import AsyncSessionLocal
from backend.app.models.session import TestSession, SessionStatus
from backend.app.models.project import Project
from backend.app.models.scenario import Scenario, ScenarioStatus
from backend.app.models.step import TestStep
from backend.app.models.finding import Finding, FindingStatus, FindingSeverity, FindingType
from backend.app.models.evidence import Evidence, EvidenceType
from backend.app.models.regression import RegressionTest

from backend.app.browser.manager import BrowserManager
from backend.app.llm.factory import get_llm_provider
from backend.app.llm.base import LLMProvider
from backend.app.qa.discovery import ApplicationDiscovery
from backend.app.qa.planner import TestPlanner
from backend.app.qa.executor import ActionExecutor
from backend.app.qa.analyzer import ActionAnalyzer
from backend.app.qa.verifier import BugVerifier
from backend.app.qa.reporter import ReportGenerator
from backend.app.qa.regression import RegressionTestGenerator


class QAOrchestrator:
    def __init__(
        self,
        session_id: int,
        event_broadcaster: Optional[Callable[[str, Dict[str, Any]], Any]] = None
    ):
        self.session_id = session_id
        self.broadcast = event_broadcaster or (lambda event, data: None)
        self.browser: Optional[BrowserManager] = None
        self.llm: Optional[LLMProvider] = None
        self._stop_requested = False
        self._paused = False

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Helper to broadcast events to connected WebSocket clients."""
        try:
            payload = {"event": event_type, "session_id": self.session_id, "data": data}
            if asyncio.iscoroutinefunction(self.broadcast):
                await self.broadcast(event_type, payload)
            else:
                res = self.broadcast(event_type, payload)
                if asyncio.iscoroutine(res):
                    await res
        except Exception as e:
            logger.warning("[Session #{}] Error broadcasting event {}: {}", self.session_id, event_type, e)

    def request_stop(self):
        self._stop_requested = True
        logger.info("[Session #{}] Stop requested by user - closing browser immediately", self.session_id)
        if self.browser:
            try:
                asyncio.create_task(self.browser.close())
            except Exception:
                pass

    async def run(self):
        """
        Master execution loop for the QA session.
        """
        start_time_total = time.time()

        async with AsyncSessionLocal() as db:
            session_obj = await db.get(TestSession, self.session_id)
            if not session_obj:
                logger.error("[Session #{}] TestSession not found in database.", self.session_id)
                return

            project_obj = await db.get(Project, session_obj.project_id)
            if not project_obj:
                logger.error("[Session #{}] Project for session not found.", self.session_id)
                return

            logger.info(
                "[Session #{}] Initializing QA run for project '{}' (Target: {}, Mission: '{}', Action budget: {})",
                self.session_id,
                project_obj.name,
                project_obj.base_url,
                session_obj.mission,
                session_obj.max_actions
            )

            # Setup session storage
            session_dir = settings.SESSIONS_PATH / f"session-{self.session_id}"
            screenshots_dir = session_dir / "screenshots"
            tests_dir = session_dir / "regression_tests"
            session_dir.mkdir(parents=True, exist_ok=True)
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            tests_dir.mkdir(parents=True, exist_ok=True)

            # Initialize LLM Provider
            if not self.llm:
                self.llm = get_llm_provider()
            logger.info("[Session #{}] Using LLM Engine: {}", self.session_id, type(self.llm).__name__)


            # Initialize Subsystems
            discovery = ApplicationDiscovery(self.llm)
            planner = TestPlanner(self.llm)
            executor = ActionExecutor(self.llm)
            analyzer = ActionAnalyzer(self.llm)
            reporter = ReportGenerator(self.llm)
            regression_gen = RegressionTestGenerator(self.llm)

            # Update status to PLANNING
            session_obj.status = SessionStatus.PLANNING.value
            session_obj.started_at = datetime.datetime.now(datetime.timezone.utc)
            await db.commit()
            await self.emit("session.started", {
                "session_id": self.session_id,
                "status": session_obj.status,
                "project_name": project_obj.name,
                "base_url": project_obj.base_url
            })

            # Stage 1: Initialize Browser
            logger.info("[Session #{}] Launching Chromium (Headless={})...", self.session_id, settings.DEFAULT_HEADLESS)
            self.browser = BrowserManager(
                headless=settings.DEFAULT_HEADLESS,
                session_storage_dir=session_dir
            )
            await self.browser.initialize()
            verifier = BugVerifier(self.llm, self.browser)
            logger.info("[Session #{}] Chromium initialized successfully", self.session_id)

            try:
                # Stage 2: Initial Navigation & Application Discovery
                logger.info("[Session #{}] Navigating to entry URL: {}", self.session_id, project_obj.base_url)
                nav_result = await self.browser.navigate(project_obj.base_url)
                logger.info("[Session #{}] Navigation result: {} (HTTP / DOM loaded in {:.1f}ms)", self.session_id, nav_result.get("status"), nav_result.get("duration_ms", 0.0))

                initial_state = await self.browser.get_state()
                logger.info("[Session #{}] Running Application Discovery Agent...", self.session_id)
                discovery_data = await discovery.discover(
                    base_url=project_obj.base_url,
                    dom_snapshot=initial_state.get("formatted_dom", ""),
                    requirements_text=project_obj.requirements_text or "",
                    mission=session_obj.mission
                )
                session_obj.ai_calls_count += 1
                await db.commit()

                discovered_areas = discovery_data.get("areas", [])
                logger.info("[Session #{}] Discovery completed: {} functional areas identified: {}", self.session_id, len(discovered_areas), [a.get("name") if isinstance(a, dict) else str(a) for a in discovered_areas])

                await self.emit("discovery.completed", {
                    "areas": discovered_areas,
                    "summary": discovery_data.get("summary", "")
                })

                # Stage 3: Build Test Plan (Generate Initial Scenarios)
                max_scenarios_to_plan = min(session_obj.max_actions // 3, 20)
                logger.info("[Session #{}] Generating test plan (up to {} scenarios)...", self.session_id, max_scenarios_to_plan)
                planned_scenarios_data = await planner.generate_plan(
                    mission=session_obj.mission,
                    requirements_text=project_obj.requirements_text or "",
                    discovered_areas=discovered_areas,
                    dom_snapshot=initial_state.get("formatted_dom", ""),
                    max_scenarios=max_scenarios_to_plan
                )
                session_obj.ai_calls_count += 1

                # Save scenarios to DB
                created_scenarios: List[Scenario] = []
                for idx, sc_item in enumerate(planned_scenarios_data):
                    sc_model = Scenario(
                        session_id=self.session_id,
                        title=sc_item.get("title", f"Scenario #{idx+1}"),
                        description=sc_item.get("description", ""),
                        area=sc_item.get("area", "General"),
                        priority=sc_item.get("priority", "MEDIUM"),
                        status=ScenarioStatus.PLANNED.value,
                        order_index=idx
                    )
                    db.add(sc_model)
                    created_scenarios.append(sc_model)
                await db.commit()

                logger.info("[Session #{}] Test plan ready with {} prioritized scenarios", self.session_id, len(created_scenarios))

                # Refresh list
                for sc in created_scenarios:
                    await db.refresh(sc)
                    logger.debug("[Session #{}] Scenario #{}: [{}] [{}] {}", self.session_id, sc.id, sc.area, sc.priority, sc.title)
                    await self.emit("scenario.created", {
                        "id": sc.id,
                        "title": sc.title,
                        "description": sc.description,
                        "area": sc.area,
                        "priority": sc.priority,
                        "status": sc.status
                    })

                # Stage 4: Execution Loop
                session_obj.status = SessionStatus.RUNNING.value
                await db.commit()
                await self.emit("session.status_change", {"status": session_obj.status})

                potential_findings: List[Finding] = []

                for idx, scenario in enumerate(created_scenarios):
                    if self._stop_requested or session_obj.actions_used >= session_obj.max_actions:
                        logger.warning("[Session #{}] Execution loop terminating (stop_requested={}, actions_used={}/{})", self.session_id, self._stop_requested, session_obj.actions_used, session_obj.max_actions)
                        break

                    # Clear analyzer loop history for new scenario
                    analyzer.clear_history()

                    scenario.status = ScenarioStatus.RUNNING.value
                    await db.commit()
                    logger.info("[Session #{}] ---> Executing Scenario #{}/{} [{}]: '{}'", self.session_id, idx + 1, len(created_scenarios), scenario.area, scenario.title)

                    await self.emit("scenario.started", {
                        "id": scenario.id,
                        "title": scenario.title,
                        "area": scenario.area
                    })

                    recent_steps: List[Dict[str, Any]] = []
                    scenario_finished = False
                    scenario_step_count = 0
                    max_steps_per_scenario = 8
                    loop_recovery_count = 0

                    while not scenario_finished and scenario_step_count < max_steps_per_scenario:
                        if self._stop_requested or session_obj.actions_used >= session_obj.max_actions:
                            break

                        # Get current browser state
                        state = await self.browser.get_state()

                        # Active findings titles
                        active_finding_titles = [f.title for f in potential_findings]
                        coverage_summary = f"{session_obj.actions_used}/{session_obj.max_actions} actions used"

                        # Choose next action
                        action_decision = await executor.choose_next_action(
                            mission=session_obj.mission,
                            current_scenario={
                                "title": scenario.title,
                                "description": scenario.description,
                                "area": scenario.area,
                                "priority": scenario.priority
                            },
                            dom_snapshot=state.get("formatted_dom", ""),
                            recent_steps=recent_steps,
                            coverage_summary=coverage_summary,
                            active_findings=active_finding_titles,
                            action_count=session_obj.actions_used + 1,
                            max_actions=session_obj.max_actions
                        )
                        session_obj.ai_calls_count += 1
                        session_obj.actions_used += 1
                        scenario_step_count += 1

                        action_name = action_decision.get("action", "wait")
                        target = action_decision.get("target")
                        value = action_decision.get("value")
                        thought = action_decision.get("thought", "")

                        # Loop prevention check
                        is_loop = analyzer.check_loop(state.get("url", ""), action_name, target)
                        if is_loop:
                            loop_recovery_count += 1
                            if loop_recovery_count > 1:
                                logger.warning("[Session #{}] Scenario #{} reached max loop recoveries ({}). Concluding scenario.", self.session_id, scenario.id, loop_recovery_count)
                                scenario_finished = True
                                scenario.status = ScenarioStatus.PASSED.value
                                break
                            logger.warning("[Session #{}] Loop detected for target '{}'. Executing recovery reload.", self.session_id, target)
                            action_name = "reload"
                            target = None
                            thought = "Loop detected (same action repeated 3 times). Reloading page to recover."

                        logger.info(
                            "[Session #{}] Action [{}/{}]: {} target='{}' val='{}' | Thought: {}",
                            self.session_id,
                            session_obj.actions_used,
                            session_obj.max_actions,
                            action_name.upper(),
                            target or "",
                            value or "",
                            thought
                        )


                        # Execute action in browser
                        exec_result = await self.browser.execute_action(action_name, target, value)

                        logger.info(
                            "[Session #{}] Result: {} in {:.1f}ms (URL: {})",
                            self.session_id,
                            exec_result.get("status"),
                            exec_result.get("duration_ms", 0.0),
                            exec_result.get("url", "")
                        )

                        # Capture screenshot for interesting steps or errors
                        screenshot_path_str = None
                        if exec_result.get("status") == "error" or scenario_step_count == 1:
                            sc_file = screenshots_dir / f"step_{scenario.id}_{scenario_step_count}.png"
                            try:
                                await self.browser.take_screenshot(sc_file)
                                screenshot_path_str = f"/storage/sessions/session-{self.session_id}/screenshots/{sc_file.name}"
                            except Exception as sc_err:
                                logger.debug("[Session #{}] Screenshot capture skipped: {}", self.session_id, sc_err)

                        # Save step to DB
                        step_record = TestStep(
                            scenario_id=scenario.id,
                            action=action_name,
                            target=target,
                            value=str(value) if value else None,
                            result=exec_result.get("status", "success"),
                            url=exec_result.get("url", state.get("url")),
                            screenshot_path=screenshot_path_str,
                            duration_ms=exec_result.get("duration_ms", 0.0),
                            error_message=exec_result.get("error")
                        )
                        db.add(step_record)
                        await db.commit()
                        await db.refresh(step_record)

                        recent_steps.append({
                            "action": action_name,
                            "target": target,
                            "value": value,
                            "result": exec_result.get("status"),
                            "url": exec_result.get("url")
                        })

                        await self.emit("action.executed", {
                            "step_id": step_record.id,
                            "scenario_id": scenario.id,
                            "action": action_name,
                            "target": target,
                            "value": value,
                            "result": exec_result.get("status"),
                            "url": exec_result.get("url"),
                            "thought": thought,
                            "actions_used": session_obj.actions_used,
                            "max_actions": session_obj.max_actions,
                            "screenshot_path": screenshot_path_str
                        })

                        # Analyze result for anomalies and bugs
                        post_state = await self.browser.get_state()
                        analysis = await analyzer.analyze_step(
                            scenario={"title": scenario.title, "area": scenario.area},
                            action_executed={"action": action_name, "target": target, "value": value},
                            action_result=exec_result,
                            console_errors=post_state.get("console_errors", []),
                            network_errors=post_state.get("network_errors", []),
                            dom_snapshot=post_state.get("formatted_dom", ""),
                            requirements_text=project_obj.requirements_text or ""
                        )
                        session_obj.ai_calls_count += 1

                        if analysis.get("is_finding"):
                            logger.warning(
                                "[Session #{}] ⚠️ Finding detected: [{}] {} - {}",
                                self.session_id,
                                analysis.get("severity", "MEDIUM"),
                                analysis.get("title", ""),
                                analysis.get("description", "")
                            )
                            # Take bug screenshot
                            bug_sc_file = screenshots_dir / f"finding_{scenario.id}_{datetime.datetime.now(datetime.timezone.utc).timestamp():.0f}.png"
                            try:
                                await self.browser.take_screenshot(bug_sc_file)
                                bug_sc_url = f"/storage/sessions/session-{self.session_id}/screenshots/{bug_sc_file.name}"
                            except Exception:
                                bug_sc_url = screenshot_path_str

                            finding_record = Finding(
                                session_id=self.session_id,
                                scenario_id=scenario.id,
                                title=analysis.get("title", "Detected UI / Runtime Anomaly"),
                                description=analysis.get("description", "An unexpected issue was detected."),
                                type=analysis.get("type", FindingType.BUG.value),
                                severity=analysis.get("severity", FindingSeverity.MEDIUM.value),
                                status=FindingStatus.POTENTIAL.value,
                                reproduction_attempts=0,
                                reproduced=False,
                                expected_behavior=analysis.get("expected_behavior"),
                                actual_behavior=analysis.get("actual_behavior"),
                                reproduction_steps=analysis.get("reproduction_steps")
                            )
                            db.add(finding_record)
                            await db.commit()
                            await db.refresh(finding_record)

                            if bug_sc_url:
                                evidence_rec = Evidence(
                                    finding_id=finding_record.id,
                                    type=EvidenceType.SCREENSHOT.value,
                                    path=bug_sc_url
                                )
                                db.add(evidence_rec)
                                await db.commit()

                            potential_findings.append(finding_record)
                            await self.emit("finding.created", {
                                "id": finding_record.id,
                                "scenario_id": scenario.id,
                                "title": finding_record.title,
                                "type": finding_record.type,
                                "severity": finding_record.severity,
                                "status": finding_record.status,
                                "description": finding_record.description,
                                "screenshot": bug_sc_url
                            })

                        if action_decision.get("is_completed"):
                            scenario_finished = True
                            scenario.status = action_decision.get("scenario_result", ScenarioStatus.PASSED.value)

                    # Finalize scenario status
                    if not scenario_finished:
                        scenario.status = ScenarioStatus.PASSED.value if not potential_findings else ScenarioStatus.FAILED.value
                    await db.commit()
                    logger.info("[Session #{}] Scenario #{} completed with status: {}", self.session_id, scenario.id, scenario.status)
                    await self.emit("scenario.completed", {
                        "id": scenario.id,
                        "status": scenario.status
                    })

                # Stage 5: Bug Verification for Potential Findings
                if not self._stop_requested and potential_findings:
                    logger.info("[Session #{}] Running Bug Verification Agent on {} potential finding(s)...", self.session_id, len(potential_findings))
                for f_item in (potential_findings if not self._stop_requested else []):
                    if self._stop_requested:
                        break
                    f_item.status = FindingStatus.VERIFYING.value
                    await db.commit()
                    logger.info("[Session #{}] Verifying finding #{}: '{}'...", self.session_id, f_item.id, f_item.title)
                    await self.emit("finding.verifying", {"id": f_item.id, "title": f_item.title})

                    # Run isolated reproduction
                    verify_result = await verifier.verify_finding(
                        finding={
                            "title": f_item.title,
                            "description": f_item.description,
                            "type": f_item.type,
                            "expected_behavior": f_item.expected_behavior,
                            "actual_behavior": f_item.actual_behavior
                        },
                        base_url=project_obj.base_url,
                        steps_history=[]
                    )
                    session_obj.ai_calls_count += 1

                    f_item.reproduction_attempts = verify_result.get("reproduction_attempts", 2)
                    f_item.reproduced = verify_result.get("reproduced", False)
                    f_item.status = verify_result.get("status", FindingStatus.CONFIRMED.value)
                    await db.commit()

                    logger.info("[Session #{}] Finding #{} verification outcome: status={}, reproduced={}", self.session_id, f_item.id, f_item.status, f_item.reproduced)

                    await self.emit("finding.confirmed" if f_item.reproduced else "finding.rejected", {
                        "id": f_item.id,
                        "title": f_item.title,
                        "status": f_item.status,
                        "reproduced": f_item.reproduced
                    })

                    # Stage 6: Generate Playwright Regression Test for Confirmed Bugs
                    if f_item.status == FindingStatus.CONFIRMED.value and f_item.type == FindingType.BUG.value:
                        logger.info("[Session #{}] Synthesizing Playwright regression test for finding #{}...", self.session_id, f_item.id)
                        reg_data = await regression_gen.generate_playwright_test(
                            finding={
                                "id": f_item.id,
                                "title": f_item.title,
                                "description": f_item.description,
                                "expected_behavior": f_item.expected_behavior,
                                "actual_behavior": f_item.actual_behavior,
                                "reproduction_steps": f_item.reproduction_steps
                            },
                            scenario={"title": "Regression verification"},
                            steps=[],
                            base_url=project_obj.base_url
                        )
                        session_obj.ai_calls_count += 1

                        test_file_path = tests_dir / reg_data["name"]
                        test_file_path.write_text(reg_data["code"])

                        reg_record = RegressionTest(
                            finding_id=f_item.id,
                            session_id=self.session_id,
                            name=reg_data["name"],
                            file_path=f"/storage/sessions/session-{self.session_id}/regression_tests/{reg_data['name']}",
                            test_code=reg_data["code"]
                        )
                        db.add(reg_record)
                        await db.commit()
                        logger.info("[Session #{}] Regression test saved: {}", self.session_id, reg_data["name"])
                        await self.emit("regression_test.created", {
                            "id": reg_record.id,
                            "finding_id": f_item.id,
                            "name": reg_record.name,
                            "file_path": reg_record.file_path
                        })

                # Stage 7: Generate Final Report
                if self._stop_requested:
                    logger.info("[Session #{}] Session was stopped by user; finishing immediately without extra LLM report call.", self.session_id)
                    final_report_md = f"# QA Session #{self.session_id} - Stopped by user\n\nSession was manually stopped."
                else:
                    logger.info("[Session #{}] Generating comprehensive Markdown QA report...", self.session_id)
                    all_scenarios_query = await db.execute(select(Scenario).where(Scenario.session_id == self.session_id))
                    all_scenarios = all_scenarios_query.scalars().all()
                    all_findings_query = await db.execute(select(Finding).where(Finding.session_id == self.session_id))
                    all_findings = all_findings_query.scalars().all()

                    final_report_md = await reporter.generate_markdown_report(
                        session_data={
                            "id": self.session_id,
                            "mission": session_obj.mission,
                            "status": "COMPLETED",
                            "actions_used": session_obj.actions_used,
                            "max_actions": session_obj.max_actions,
                            "ai_calls_count": session_obj.ai_calls_count,
                            "estimated_cost": session_obj.estimated_cost
                        },
                        scenarios=[{
                            "title": s.title,
                            "description": s.description,
                            "area": s.area,
                            "status": s.status,
                            "priority": s.priority
                        } for s in all_scenarios],
                        findings=[{
                            "id": f.id,
                            "title": f.title,
                        "description": f.description,
                        "type": f.type,
                        "severity": f.severity,
                        "status": f.status,
                        "reproduced": f.reproduced,
                        "reproduction_attempts": f.reproduction_attempts,
                        "expected_behavior": f.expected_behavior,
                        "actual_behavior": f.actual_behavior,
                        "reproduction_steps": f.reproduction_steps
                    } for f in all_findings],
                    console_logs=self.browser.console_logs,
                    network_errors=self.browser.network_errors
                )

                # Save report to storage
                report_file = session_dir / "report.md"
                report_file.write_text(final_report_md)

                session_obj.report_markdown = final_report_md
                session_obj.status = SessionStatus.COMPLETED.value
                session_obj.finished_at = datetime.datetime.now(datetime.timezone.utc)
                await db.commit()

                elapsed_total = time.time() - start_time_total
                logger.info(
                    "[Session #{}] ✅ QA Session COMPLETED in {:.1f}s (Actions: {}/{}, Scenarios: {}, Confirmed bugs: {})",
                    self.session_id,
                    elapsed_total,
                    session_obj.actions_used,
                    session_obj.max_actions,
                    len(all_scenarios),
                    len([f for f in all_findings if f.status == FindingStatus.CONFIRMED.value])
                )

                await self.emit("report.generated", {
                    "session_id": self.session_id,
                    "report_markdown": final_report_md
                })
                await self.emit("session.completed", {
                    "session_id": self.session_id,
                    "status": session_obj.status,
                    "actions_used": session_obj.actions_used,
                    "scenarios_tested": len(all_scenarios),
                    "findings_count": len(all_findings)
                })

            except Exception as e:
                logger.exception("[Session #{}] ❌ Fatal error in QA session: {}", self.session_id, e)
                session_obj.status = SessionStatus.FAILED.value
                session_obj.finished_at = datetime.datetime.now(datetime.timezone.utc)
                await db.commit()
                await self.emit("session.failed", {"session_id": self.session_id, "error": str(e)})

            finally:
                if self.browser:
                    logger.info("[Session #{}] Closing Chromium browser context...", self.session_id)
                    await self.browser.close()
