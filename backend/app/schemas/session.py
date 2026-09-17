import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.models.session import SessionStatus


class SessionCreate(BaseModel):
    mission: str = "Conduct full exploratory testing of the application. Test main user flows, negative cases, input validation, navigation, API errors, and UI persistence. Do not stop after the first successful flow."
    max_actions: int = 100
    headless: Optional[bool] = False
    llm_provider: Optional[str] = "codex"  # codex, openai, gemini, anthropic
    llm_model: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    project_id: int
    mission: str
    status: str
    max_actions: int
    actions_used: int
    ai_calls_count: int
    estimated_cost: float
    started_at: Optional[datetime.datetime] = None
    finished_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    report_markdown: Optional[str] = None

    scenarios_total: Optional[int] = 0
    scenarios_passed: Optional[int] = 0
    scenarios_failed: Optional[int] = 0
    scenarios_blocked: Optional[int] = 0
    findings_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
