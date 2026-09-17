import pytest
import asyncio
import http.server
import socketserver
import threading
from pathlib import Path

from backend.app.database import init_db, AsyncSessionLocal
from backend.app.models import Project, TestSession, Scenario, TestStep, Finding
from backend.app.qa.orchestrator import QAOrchestrator


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="sample_app", **kwargs)

    def log_message(self, format, *args):
        pass  # suppress noisy logs


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


@pytest.mark.asyncio
async def test_full_autonomous_qa_run():
    # 1. Start test target web server on free dynamic port
    httpd = ReusableTCPServer(("127.0.0.1", 0), QuietHandler)
    port = httpd.server_address[1]

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()


    try:
        await init_db()

        # 2. Create project in DB
        async with AsyncSessionLocal() as db:
            project = Project(
                name="DoForms E2E Test App",
                base_url=f"http://127.0.0.1:{port}",
                description="Sample App for automated verification",
                requirements_text="Must create forms, add questions, validate empty title, and persist state."
            )
            db.add(project)
            await db.commit()
            await db.refresh(project)

            session = TestSession(
                project_id=project.id,
                mission="Conduct exploratory testing of form builder, validation, and persistence.",
                max_actions=12
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            session_id = session.id

        events_received = []

        def event_handler(evt, data):
            events_received.append((evt, data))

        # 3. Run QA Orchestrator
        orchestrator = QAOrchestrator(session_id=session_id, event_broadcaster=event_handler)
        from backend.app.llm.openai_provider import CodexProvider
        orchestrator.llm = CodexProvider()
        await orchestrator.run()


        # 4. Assert Results in DB
        async with AsyncSessionLocal() as db:
            session_record = await db.get(TestSession, session_id)
            assert session_record is not None
            assert session_record.status == "COMPLETED"
            assert session_record.actions_used > 0
            assert session_record.report_markdown is not None
            assert "Executive Summary" in session_record.report_markdown

            # Verify scenarios
            from sqlalchemy import select
            sc_res = await db.execute(select(Scenario).where(Scenario.session_id == session_id))
            scenarios = sc_res.scalars().all()
            assert len(scenarios) > 0

            # Verify steps
            st_res = await db.execute(select(TestStep).join(Scenario).where(Scenario.session_id == session_id))
            steps = st_res.scalars().all()
            assert len(steps) > 0

        # Assert WebSocket events were emitted
        event_names = [e[0] for e in events_received]
        assert "session.started" in event_names
        assert "discovery.completed" in event_names
        assert "scenario.created" in event_names
        assert "action.executed" in event_names
        assert "session.completed" in event_names

    finally:
        httpd.shutdown()
        httpd.server_close()
