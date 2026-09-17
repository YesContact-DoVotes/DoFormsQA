import pytest
import asyncio
from backend.app.database import init_db, AsyncSessionLocal
from backend.app.models import Project, TestSession, Scenario, TestStep, Finding, Evidence, RegressionTest
from backend.app.browser.dom_snapshot import DOMSnapshot
from backend.app.llm.openai_provider import CodexProvider
from backend.app.qa.discovery import ApplicationDiscovery
from backend.app.qa.planner import TestPlanner
from backend.app.qa.executor import ActionExecutor
from backend.app.qa.analyzer import ActionAnalyzer
from backend.app.qa.verifier import BugVerifier
from backend.app.qa.reporter import ReportGenerator
from backend.app.qa.regression import RegressionTestGenerator


@pytest.mark.asyncio
async def test_database_and_models():
    await init_db()
    async with AsyncSessionLocal() as db:
        # Create Project
        project = Project(
            name="Test DoForms",
            base_url="http://localhost:3000",
            requirements_text="Test requirements text"
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        assert project.id is not None
        assert project.name == "Test DoForms"

        # Create Session
        session = TestSession(
            project_id=project.id,
            mission="Full exploratory test",
            max_actions=50
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        assert session.id is not None
        assert session.status == "CREATED"

        # Create Scenario
        scenario = Scenario(
            session_id=session.id,
            title="Create form flow",
            area="Form Builder",
            priority="HIGH"
        )
        db.add(scenario)
        await db.commit()
        await db.refresh(scenario)
        assert scenario.id is not None

        # Create Step
        step = TestStep(
            scenario_id=scenario.id,
            action="click",
            target="button#save",
            result="success"
        )
        db.add(step)
        await db.commit()
        await db.refresh(step)
        assert step.id is not None

        # Create Finding & Evidence
        finding = Finding(
            session_id=session.id,
            scenario_id=scenario.id,
            title="Empty title bug",
            description="Allows saving empty title",
            type="BUG",
            severity="HIGH",
            status="CONFIRMED"
        )
        db.add(finding)
        await db.commit()
        await db.refresh(finding)
        assert finding.id is not None

        evidence = Evidence(
            finding_id=finding.id,
            type="SCREENSHOT",
            path="/storage/test.png"
        )
        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)
        assert evidence.id is not None


@pytest.mark.asyncio
async def test_llm_and_qa_components():
    llm = CodexProvider()

    # 1. Discovery
    discovery = ApplicationDiscovery(llm)
    disc_res = await discovery.discover("http://localhost:3000", "Sample DOM", "PRD")
    assert "areas" in disc_res
    assert len(disc_res["areas"]) > 0

    # 2. Planner
    planner = TestPlanner(llm)
    plan = await planner.generate_plan("Mission", "PRD", disc_res["areas"], "DOM", 10)
    assert len(plan) > 0
    assert "title" in plan[0]

    # 3. Executor
    executor = ActionExecutor(llm)
    action = await executor.choose_next_action(
        mission="Mission",
        current_scenario={"title": "Test scenario", "area": "Form Builder", "priority": "HIGH"},
        dom_snapshot="selector='#btn-save' label='Save'",
        recent_steps=[],
        coverage_summary="1/50",
        active_findings=[],
        action_count=1,
        max_actions=50
    )
    assert "action" in action
    assert "thought" in action

    # 4. Analyzer
    analyzer = ActionAnalyzer(llm)
    analysis = await analyzer.analyze_step(
        scenario={"title": "Save", "area": "Form Builder"},
        action_executed={"action": "click", "target": "#save"},
        action_result={"status": "success", "url": "http://localhost:3000"},
        console_errors=[],
        network_errors=[],
        dom_snapshot="DOM"
    )
    assert "is_finding" in analysis

    # 5. Reporter
    reporter = ReportGenerator(llm)
    report_md = await reporter.generate_markdown_report(
        session_data={"id": 1, "mission": "Explore", "status": "COMPLETED", "actions_used": 10, "max_actions": 50},
        scenarios=[{"title": "Test 1", "area": "Builder", "status": "PASSED"}],
        findings=[],
        console_logs=[],
        network_errors=[]
    )
    assert "# QA Autonomous Test Report" in report_md
    assert "## 1. Executive Summary" in report_md

    # 6. Regression Test Generator
    reg_gen = RegressionTestGenerator(llm)
    reg_res = await reg_gen.generate_playwright_test(
        finding={"title": "Form bug", "description": "Desc", "expected_behavior": "Exp", "actual_behavior": "Act", "reproduction_steps": "Steps"},
        scenario={"title": "Form"},
        steps=[],
        base_url="http://localhost:3000"
    )
    assert "test_code" in reg_res or "code" in reg_res
