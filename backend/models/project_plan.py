"""
Project Plan Model - Architecture plan created by Team Lead
"""

from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.sql import func
import uuid

from backend.database import Base


class ProjectPlan(Base):
    __tablename__ = "project_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, unique=True)
    architecture_json = Column(Text, nullable=False)  # Full architecture plan
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
