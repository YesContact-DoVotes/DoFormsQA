import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from backend.app.models.scenario import ScenarioPriority, ScenarioStatus


class ScenarioBase(BaseModel):
    title: str
    description: Optional[str] = ""
    area: str = "General"
    priority: str = ScenarioPriority.MEDIUM.value
    status: str = ScenarioStatus.PLANNED.value
    order_index: int = 0


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioResponse(ScenarioBase):
    id: int
    session_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    steps_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
