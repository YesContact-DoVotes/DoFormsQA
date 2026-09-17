import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.database import Base


class TestStep(Base):
    __tablename__ = "test_steps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)

    action = Column(String(50), nullable=False)  # navigate, click, fill, select, check, press_key, reload, wait, etc.
    target = Column(String(255), nullable=True)  # Selector or target element description
    value = Column(Text, nullable=True)          # Input value or payload
    result = Column(String(50), default="success")  # success, error, blocked

    url = Column(String(1024), nullable=True)
    screenshot_path = Column(String(1024), nullable=True)
    duration_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    scenario = relationship("Scenario", back_populates="steps")
