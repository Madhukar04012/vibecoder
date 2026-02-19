"""
Artifact Model - Tracks generated files and outputs.
MetaGPT-style: Artifacts are first-class, not just files on disk.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from backend.database import Base


class ArtifactType(str, Enum):
    """Types of artifacts"""
    FILE = "file"
    FOLDER = "folder"
    CONFIG = "config"
    DOC = "doc"
    CODE = "code"


class Artifact(Base):
    """
    Represents a generated file or output.
    Enables file tree UI, diffing, and audit trails.
    """
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("project_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Artifact info
    name = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)  # Relative path from project root
    artifact_type = Column(String(20), default=ArtifactType.FILE, nullable=False)
    
    # Content metadata
    file_size = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)  # SHA256 for change detection
    description = Column(Text, nullable=True)
    
    # Creator tracking
    created_by_agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    created_by_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="artifacts")
    run = relationship("ProjectRun", back_populates="artifacts")

    def __repr__(self) -> str:
        return f"<Artifact id={self.id} path='{self.path}' type={self.artifact_type}>"
