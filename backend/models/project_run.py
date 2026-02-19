"""
ProjectRun Model - Tracks build/execution sessions.
MetaGPT-style: Runs are first-class, not implicit.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from backend.database import Base


class RunStatus(str, Enum):
    """Run execution states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectRun(Base):
    """
    Represents a single build/execution session.
    Multiple runs per project are supported.
    """
    __tablename__ = "project_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Run metadata
    status = Column(String(20), default=RunStatus.PENDING, nullable=False, index=True)
    triggered_by = Column(String(50), default="user")  # user | auto | system
    
    # Summary stats
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    files_created = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="runs")
    logs = relationship("ExecutionLog", back_populates="run", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")
    messages = relationship("AgentMessage", backref="run")

    def __repr__(self) -> str:
        return f"<ProjectRun id={self.id} project={self.project_id} status={self.status}>"

    def complete(self, tasks_completed: int = 0, tasks_failed: int = 0, files_created: int = 0):
        """Mark run as completed"""
        self.status = RunStatus.COMPLETED
        self.finished_at = func.now()
        self.tasks_completed = tasks_completed
        self.tasks_failed = tasks_failed
        self.files_created = files_created

    def fail(self, error_message: str):
        """Mark run as failed"""
        self.status = RunStatus.FAILED
        self.finished_at = func.now()
        self.error_message = error_message
