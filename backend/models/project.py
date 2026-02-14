"""
Project Model - Stores user projects
Enhanced with MetaGPT-style relationships
"""

from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from backend.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False, default="Untitled Project")
    idea = Column(String, nullable=True)
    status = Column(String, default="planning")  # planning / building / reviewing / completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships (original)
    owner = relationship("User", back_populates="projects")
    agents = relationship("ProjectAgent", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    
    # Relationships (MetaGPT-style additions)
    agents_v2 = relationship("Agent", back_populates="project", cascade="all, delete-orphan")
    runs = relationship("ProjectRun", back_populates="project", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")
    agent_messages = relationship("AgentMessage", back_populates="project", cascade="all, delete-orphan")
