import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.models.finding import FindingType, FindingSeverity, FindingStatus


class EvidenceResponse(BaseModel):
    id: int
    finding_id: int
    type: str
    path: str
    details_json: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class RegressionTestResponse(BaseModel):
    id: int
    finding_id: int
    session_id: int
    name: str
    file_path: str
    test_code: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class FindingResponse(BaseModel):
    id: int
    session_id: int
    scenario_id: Optional[int] = None
    title: str
    description: str
    type: str
    severity: str
    status: str
    reproduction_attempts: int
    reproduced: bool
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    reproduction_steps: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    evidences: List[EvidenceResponse] = []
    regression_test: Optional[RegressionTestResponse] = None

    model_config = ConfigDict(from_attributes=True)
