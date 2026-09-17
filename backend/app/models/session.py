import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.database import Base


class SessionStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    mission = Column(Text, nullable=False)
    status = Column(String(50), default=SessionStatus.CREATED.value, index=True)

    max_actions = Column(Integer, default=100)
    actions_used = Column(Integer, default=0)

    ai_calls_count = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    report_markdown = Column(Text, nullable=True)

    project = relationship("Project", back_populates="sessions")
    scenarios = relationship("Scenario", back_populates="session", cascade="all, delete-orphan", order_by="Scenario.order_index")
    findings = relationship("Finding", back_populates="session", cascade="all, delete-orphan", order_by="desc(Finding.id)")
    regression_tests = relationship("RegressionTest", back_populates="session", cascade="all, delete-orphan")
