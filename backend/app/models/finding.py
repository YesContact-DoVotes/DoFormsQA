import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.app.database import Base


class FindingType(str, Enum):
    BUG = "BUG"
    MISSING_FUNCTIONALITY = "MISSING_FUNCTIONALITY"
    UX_ISSUE = "UX_ISSUE"
    CONSOLE_ERROR = "CONSOLE_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    UNKNOWN = "UNKNOWN"


class FindingSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingStatus(str, Enum):
    POTENTIAL = "POTENTIAL"
    VERIFYING = "VERIFYING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    type = Column(String(50), default=FindingType.BUG.value)
    severity = Column(String(50), default=FindingSeverity.MEDIUM.value)
    status = Column(String(50), default=FindingStatus.POTENTIAL.value, index=True)

    reproduction_attempts = Column(Integer, default=0)
    reproduced = Column(Boolean, default=False)

    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)
    reproduction_steps = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    session = relationship("TestSession", back_populates="findings")
    scenario = relationship("Scenario", back_populates="findings")
    evidences = relationship("Evidence", back_populates="finding", cascade="all, delete-orphan")
    regression_test = relationship("RegressionTest", back_populates="finding", uselist=False, cascade="all, delete-orphan")
