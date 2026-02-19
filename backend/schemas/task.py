"""
Task Schemas - Pydantic models for task management
Production-ready schemas for API input/output
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.models.enums import TaskStatus, TaskPriority, AgentRole


class TaskBase(BaseModel):
    """Base schema with common task fields"""
    title: str
    description: Optional[str] = None
    priority: TaskPriority
    status: TaskStatus
    assigned_agent: Optional[AgentRole]


class TaskRead(TaskBase):
    """Schema for reading task data (API response)"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_agent: Optional[AgentRole] = None


class TaskUpdateStatus(BaseModel):
    """Schema for updating task status only"""
    status: TaskStatus


class TaskAssignAgent(BaseModel):
    """Schema for assigning an agent to a task"""
    assigned_agent: AgentRole
