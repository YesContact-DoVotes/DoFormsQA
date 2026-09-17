import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.session import TestSession, SessionStatus
from backend.app.models.scenario import Scenario, ScenarioStatus
from backend.app.models.step import TestStep
from backend.app.models.finding import Finding
from backend.app.models.evidence import Evidence
from backend.app.models.regression import RegressionTest
from backend.app.schemas.session import SessionCreate, SessionResponse
from backend.app.schemas.scenario import ScenarioResponse
from backend.app.schemas.step import StepResponse
from backend.app.schemas.finding import FindingResponse, RegressionTestResponse
from backend.app.schemas.report import FullReportResponse, ReportSummary, ReportAreaCoverage
from backend.app.api.websocket import ws_manager
from backend.app.qa.orchestrator import QAOrchestrator

router = APIRouter(tags=["sessions"])

# In-memory registry of active orchestrators
active_orchestrators: Dict[int, QAOrchestrator] = {}


async def broadcast_session_event(event_type: str, payload: Dict[str, Any]):
    session_id = payload.get("session_id")
    if session_id:
        await ws_manager.broadcast_to_session(session_id, payload)


@router.post("/projects/{project_id}/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(project_id: int, payload: SessionCreate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    session = TestSession(
        project_id=project_id,
        mission=payload.mission,
        max_actions=payload.max_actions,
        status=SessionStatus.CREATED.value
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    resp = SessionResponse.model_validate(session)
    return resp


@router.get("/projects/{project_id}/sessions", response_model=List[SessionResponse])
async def list_project_sessions(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    res = await db.execute(
        select(TestSession).where(TestSession.project_id == project_id).order_by(TestSession.created_at.desc())
    )
    sessions = res.scalars().all()

    response_list = []
    for s in sessions:
        # Load scenario counts
        scenarios_res = await db.execute(select(Scenario).where(Scenario.session_id == s.id))
        all_sc = scenarios_res.scalars().all()
        
        findings_res = await db.execute(select(func.count(Finding.id)).where(Finding.session_id == s.id))
        findings_count = findings_res.scalar() or 0

        resp = SessionResponse.model_validate(s)
        resp.scenarios_total = len(all_sc)
        resp.scenarios_passed = len([x for x in all_sc if x.status == ScenarioStatus.PASSED.value])
        resp.scenarios_failed = len([x for x in all_sc if x.status == ScenarioStatus.FAILED.value])
        resp.scenarios_blocked = len([x for x in all_sc if x.status == ScenarioStatus.BLOCKED.value])
        resp.findings_count = findings_count
        response_list.append(resp)

    return response_list


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await db.get(TestSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    scenarios_res = await db.execute(select(Scenario).where(Scenario.session_id == session.id))
    all_sc = scenarios_res.scalars().all()

    findings_res = await db.execute(select(func.count(Finding.id)).where(Finding.session_id == session.id))
    findings_count = findings_res.scalar() or 0

    resp = SessionResponse.model_validate(session)
    resp.scenarios_total = len(all_sc)
    resp.scenarios_passed = len([x for x in all_sc if x.status == ScenarioStatus.PASSED.value])
    resp.scenarios_failed = len([x for x in all_sc if x.status == ScenarioStatus.FAILED.value])
    resp.scenarios_blocked = len([x for x in all_sc if x.status == ScenarioStatus.BLOCKED.value])
    resp.findings_count = findings_count
    return resp


@router.post("/sessions/{session_id}/start")
async def start_session(session_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    session = await db.get(TestSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status in [SessionStatus.RUNNING.value, SessionStatus.PLANNING.value]:
        return {"message": "Session is already active", "status": session.status}

    orchestrator = QAOrchestrator(
        session_id=session_id,
        event_broadcaster=broadcast_session_event
    )
    active_orchestrators[session_id] = orchestrator

    # Launch in background
    background_tasks.add_task(orchestrator.run)

    return {"message": "QA Session started successfully", "session_id": session_id}


@router.post("/sessions/{session_id}/stop")
async def stop_session(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await db.get(TestSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_id in active_orchestrators:
        orch = active_orchestrators.pop(session_id)
        orch.request_stop()
        if orch.browser:
            try:
                await orch.browser.close()
            except Exception:
                pass

    session.status = SessionStatus.COMPLETED.value
    session.finished_at = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()

    await broadcast_session_event("session.stopped", {"session_id": session_id})
    return {"message": "Session stopped and browser closed", "session_id": session_id}


@router.get("/sessions/{session_id}/scenarios", response_model=List[ScenarioResponse])
async def list_session_scenarios(session_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Scenario).where(Scenario.session_id == session_id).order_by(Scenario.order_index)
    )
    scenarios = res.scalars().all()
    
    response_list = []
    for sc in scenarios:
        steps_count_res = await db.execute(select(func.count(TestStep.id)).where(TestStep.scenario_id == sc.id))
        steps_count = steps_count_res.scalar() or 0

        resp = ScenarioResponse.model_validate(sc)
        resp.steps_count = steps_count
        response_list.append(resp)

    return response_list


@router.get("/sessions/{session_id}/steps", response_model=List[StepResponse])
async def list_session_steps(session_id: int, scenario_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    if scenario_id:
        query = select(TestStep).where(TestStep.scenario_id == scenario_id).order_by(TestStep.id)
    else:
        query = (
            select(TestStep)
            .join(Scenario, TestStep.scenario_id == Scenario.id)
            .where(Scenario.session_id == session_id)
            .order_by(TestStep.id)
        )
    res = await db.execute(query)
    steps = res.scalars().all()
    return [StepResponse.model_validate(s) for s in steps]


@router.get("/sessions/{session_id}/findings", response_model=List[FindingResponse])
async def list_session_findings(session_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Finding)
        .options(selectinload(Finding.evidences), selectinload(Finding.regression_test))
        .where(Finding.session_id == session_id)
        .order_by(Finding.id.desc())
    )
    findings = res.scalars().all()
    return [FindingResponse.model_validate(f) for f in findings]


@router.get("/findings/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Finding)
        .options(selectinload(Finding.evidences), selectinload(Finding.regression_test))
        .where(Finding.id == finding_id)
    )
    finding = res.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse.model_validate(finding)


@router.get("/sessions/{session_id}/report", response_model=FullReportResponse)
async def get_session_report(session_id: int, db: AsyncSession = Depends(get_db)):
    session = await db.get(TestSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    scenarios_res = await db.execute(select(Scenario).where(Scenario.session_id == session.id))
    all_sc = scenarios_res.scalars().all()

    findings_res = await db.execute(select(Finding).where(Finding.session_id == session.id))
    all_findings = findings_res.scalars().all()

    duration = 0.0
    if session.started_at and session.finished_at:
        duration = (session.finished_at - session.started_at).total_seconds()

    # Areas coverage
    areas: Dict[str, Dict[str, int]] = {}
    for sc in all_sc:
        area_name = sc.area or "General"
        if area_name not in areas:
            areas[area_name] = {"tested": 0, "total": 0}
        areas[area_name]["total"] += 1
        if sc.status in [ScenarioStatus.PASSED.value, ScenarioStatus.FAILED.value, ScenarioStatus.BLOCKED.value]:
            areas[area_name]["tested"] += 1

    coverage_list = [
        ReportAreaCoverage(
            area=area,
            scenarios_tested=data["tested"],
            scenarios_total=data["total"],
            coverage_percent=(data["tested"] / data["total"] * 100) if data["total"] > 0 else 0
        )
        for area, data in areas.items()
    ]

    summary = ReportSummary(
        session_id=session.id,
        duration_seconds=duration,
        actions_used=session.actions_used,
        max_actions=session.max_actions,
        scenarios_total=len(all_sc),
        scenarios_passed=len([x for x in all_sc if x.status == ScenarioStatus.PASSED.value]),
        scenarios_failed=len([x for x in all_sc if x.status == ScenarioStatus.FAILED.value]),
        scenarios_blocked=len([x for x in all_sc if x.status == ScenarioStatus.BLOCKED.value]),
        scenarios_skipped=len([x for x in all_sc if x.status == ScenarioStatus.PLANNED.value or x.status == ScenarioStatus.SKIPPED.value]),
        confirmed_bugs=len([f for f in all_findings if f.status == "CONFIRMED"]),
        potential_issues=len([f for f in all_findings if f.status in ["POTENTIAL", "VERIFYING"]]),
        ai_calls_count=session.ai_calls_count,
        estimated_cost=session.estimated_cost
    )

    return FullReportResponse(
        session_id=session.id,
        markdown=session.report_markdown or "# QA Report\n\nNo report generated yet.",
        summary=summary,
        coverage=coverage_list
    )


@router.get("/sessions/{session_id}/regression-tests", response_model=List[RegressionTestResponse])
async def list_session_regression_tests(session_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(RegressionTest).where(RegressionTest.session_id == session_id).order_by(RegressionTest.id)
    )
    tests = res.scalars().all()
    return [RegressionTestResponse.model_validate(t) for t in tests]
