import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class EvidenceType(str, Enum):
    SCREENSHOT = "SCREENSHOT"
    TRACE = "TRACE"
    CONSOLE_LOG = "CONSOLE_LOG"
    NETWORK_LOG = "NETWORK_LOG"


class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)

    type = Column(String(50), default=EvidenceType.SCREENSHOT.value)
    path = Column(String(1024), nullable=False)
    details_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    finding = relationship("Finding", back_populates="evidences")
