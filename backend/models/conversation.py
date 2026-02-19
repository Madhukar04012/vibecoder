"""
Conversation Model - Chat messages between user and AI agents
"""

from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
import uuid

from backend.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or agent role like "team_lead"
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
