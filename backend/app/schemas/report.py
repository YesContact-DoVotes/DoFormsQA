from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ReportSummary(BaseModel):
    session_id: int
    duration_seconds: float
    actions_used: int
    max_actions: int
    scenarios_total: int
    scenarios_passed: int
    scenarios_failed: int
    scenarios_blocked: int
    scenarios_skipped: int
    confirmed_bugs: int
    potential_issues: int
    ai_calls_count: int
    estimated_cost: float


class ReportAreaCoverage(BaseModel):
    area: str
    scenarios_tested: int
    scenarios_total: int
    coverage_percent: float


class FullReportResponse(BaseModel):
    session_id: int
    markdown: str
    summary: ReportSummary
    coverage: List[ReportAreaCoverage]
