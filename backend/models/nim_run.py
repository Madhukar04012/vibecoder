"""
NIM Run Models — Phase 5: PostgreSQL persistence for the NIM multi-agent system

Tables:
  nim_projects      — one row per user request (the "run")
  nim_dag_snapshots — DAG JSON produced by TEAM_LEAD for the run
  nim_tasks         — one row per task in the DAG
  nim_task_outputs  — full output text per task (separate table to keep nim_tasks lean)
  nim_agent_logs    — structured log entries per task
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from backend.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ── NimProject ─────────────────────────────────────────────────────────────────

class NimProject(Base):
    """
    Top-level record for a NIM multi-agent run.

    status values:  pending | running | complete | failed
    """

    __tablename__ = "nim_projects"

    id         = Column(String(36), primary_key=True, default=_uuid)
    name       = Column(String(255), nullable=False)
    user_id    = Column(String(255), nullable=False, index=True)
    prompt     = Column(Text, nullable=False)
    status     = Column(String(32), nullable=False, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    # Relations
    dag_snapshot = relationship("NimDagSnapshot", back_populates="project", uselist=False)
    tasks        = relationship("NimTask", back_populates="project", order_by="NimTask.created_at")

    def __repr__(self) -> str:
        return f"<NimProject id={self.id!r} status={self.status!r}>"


# ── NimDagSnapshot ─────────────────────────────────────────────────────────────

class NimDagSnapshot(Base):
    """
    Stores the raw DAG JSON produced by TEAM_LEAD for a given project.
    Enables replay, debugging, and audit.
    """

    __tablename__ = "nim_dag_snapshots"

    id         = Column(String(36), primary_key=True, default=_uuid)
    project_id = Column(String(36), ForeignKey("nim_projects.id", ondelete="CASCADE"),
                        nullable=False, unique=True, index=True)
    dag_json   = Column(JSON, nullable=False)   # raw DAG dict from TEAM_LEAD
    task_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("NimProject", back_populates="dag_snapshot")

    def __repr__(self) -> str:
        return f"<NimDagSnapshot project={self.project_id!r} tasks={self.task_count}>"


# ── NimTask ────────────────────────────────────────────────────────────────────

class NimTask(Base):
    """
    One row per task in the DAG.

    status values: PENDING | RUNNING | COMPLETE | FAILED | BLOCKED
    """

    __tablename__ = "nim_tasks"

    id          = Column(String(36), primary_key=True, default=_uuid)
    dag_task_id = Column(String(128), nullable=False)   # the "t1", "t2" id from DAG JSON
    project_id  = Column(String(36), ForeignKey("nim_projects.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    role        = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    status      = Column(String(32), nullable=False, default="PENDING", index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    error       = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at  = Column(DateTime(timezone=True), server_default=func.now(),
                         onupdate=func.now(), nullable=False)

    # Relations
    project = relationship("NimProject", back_populates="tasks")
    output  = relationship("NimTaskOutput", back_populates="task", uselist=False)
    logs    = relationship("NimAgentLog", back_populates="task", order_by="NimAgentLog.created_at")

    def __repr__(self) -> str:
        return f"<NimTask dag_id={self.dag_task_id!r} role={self.role!r} status={self.status!r}>"


# ── NimTaskOutput ──────────────────────────────────────────────────────────────

class NimTaskOutput(Base):
    """
    Full LLM output text for a completed task.
    Stored separately to keep nim_tasks rows lean and allow large outputs.
    """

    __tablename__ = "nim_task_outputs"

    id          = Column(String(36), primary_key=True, default=_uuid)
    task_id     = Column(String(36), ForeignKey("nim_tasks.id", ondelete="CASCADE"),
                         nullable=False, unique=True, index=True)
    content     = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("NimTask", back_populates="output")

    def __repr__(self) -> str:
        return f"<NimTaskOutput task={self.task_id!r} tokens={self.token_count}>"


# ── NimAgentLog ────────────────────────────────────────────────────────────────

class NimAgentLog(Base):
    """
    Structured log entry from an agent during task execution.
    All errors must be logged here — no silent failures.

    level values: info | warning | error
    """

    __tablename__ = "nim_agent_logs"

    id         = Column(String(36), primary_key=True, default=_uuid)
    task_id    = Column(String(36), ForeignKey("nim_tasks.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    level      = Column(String(16), nullable=False, default="info")
    message    = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("NimTask", back_populates="logs")

    def __repr__(self) -> str:
        return f"<NimAgentLog task={self.task_id!r} level={self.level!r}>"
