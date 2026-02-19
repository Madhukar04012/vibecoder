"""
Project Agent Model - AI team members for each project
"""

from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from backend.database import Base


class ProjectAgent(Base):
    __tablename__ = "project_agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    role = Column(String, nullable=False)  # team_lead, backend, frontend, qa, docs
    state_json = Column(Text, default="{}")  # Stores agent memory/state
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    project = relationship("Project", back_populates="agents")
