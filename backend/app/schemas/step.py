import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class StepResponse(BaseModel):
    id: int
    scenario_id: int
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    result: str = "success"
    url: Optional[str] = None
    screenshot_path: Optional[str] = None
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
