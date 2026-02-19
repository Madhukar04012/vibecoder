"""
Centralized Enums for VibeCober Models
Strict, predictable, and extensible enum definitions.
"""

from enum import Enum


class TaskStatus(str, Enum):
    """Task lifecycle states"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AgentRole(str, Enum):
    """AI Agent roles for task assignment"""
    TEAM_LEAD = "team_lead"
    BACKEND_ENGINEER = "backend_engineer"
    FRONTEND_ENGINEER = "frontend_engineer"
    DATABASE_ENGINEER = "database_engineer"
    QA_ENGINEER = "qa_engineer"
