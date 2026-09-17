import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class ScenarioPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ScenarioStatus(str, Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    area = Column(String(100), nullable=False, default="General")
    priority = Column(String(50), default=ScenarioPriority.MEDIUM.value)
    status = Column(String(50), default=ScenarioStatus.PLANNED.value, index=True)
    order_index = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    session = relationship("TestSession", back_populates="scenarios")
    steps = relationship("TestStep", back_populates="scenario", cascade="all, delete-orphan", order_by="TestStep.id")
    findings = relationship("Finding", back_populates="scenario")
