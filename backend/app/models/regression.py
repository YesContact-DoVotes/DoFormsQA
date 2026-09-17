import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class RegressionTest(Base):
    __tablename__ = "regression_tests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, unique=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    test_code = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    finding = relationship("Finding", back_populates="regression_test")
    session = relationship("TestSession", back_populates="regression_tests")
