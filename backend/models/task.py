"""
Task Model - Production-ready unit of work for projects.
Supports agent assignment, lifecycle tracking, and cascade deletion.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Enum,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.enums import TaskStatus, TaskPriority, AgentRole


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.TODO,
        nullable=False,
        index=True,
    )

    priority = Column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )

    assigned_agent = Column(
        Enum(AgentRole),
        nullable=True,
        index=True,
    )

    project_id = Column(
        String,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="tasks")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title='{self.title}' status={self.status}>"
