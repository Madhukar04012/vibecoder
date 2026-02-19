"""
Agent Model - First-class persistent agent entities.
MetaGPT-style: Agents are tracked, not just roles.
"""

from sqlalchemy import Column, Integer, String, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from backend.database import Base
from backend.models.enums import AgentRole


class AgentStatus(str, Enum):
    """Agent execution states"""
    IDLE = "idle"
    THINKING = "thinking"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class Agent(Base):
    """
    Persistent agent entity for a project.
    Each project has multiple agents (Team Lead, Backend, Frontend, etc.)
    """
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)  # "Team Lead", "Backend Engineer"
    role = Column(SQLEnum(AgentRole), nullable=False, index=True)
    status = Column(String(20), default=AgentStatus.IDLE, nullable=False)
    
    # Agent metadata
    description = Column(String(500), nullable=True)
    avatar_url = Column(String(255), nullable=True)  # For UI display
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="agents_v2")
    messages = relationship("AgentMessage", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Agent id={self.id} name='{self.name}' role={self.role} status={self.status}>"

    def set_status(self, status: str):
        """Update agent status and last_active timestamp"""
        self.status = status
        if status in [AgentStatus.RUNNING, AgentStatus.THINKING]:
            self.last_active_at = func.now()
