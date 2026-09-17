import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    name: str
    base_url: str
    description: Optional[str] = ""
    requirements_text: Optional[str] = ""


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    description: Optional[str] = None
    requirements_text: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    sessions_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
