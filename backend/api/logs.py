"""
Execution Logs API - Read-only access to task execution history.
Provides audit trail and debugging visibility.
"""

from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func as sa_func, case
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.execution_log import ExecutionLog
from backend.models.project import Project
from backend.models.user import User

router = APIRouter(prefix="/logs", tags=["Execution Logs"])


# Response schema
class ExecutionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    project_id: str
    agent: str
    status: str
    message: str | None
    files_created: int
    output_dir: str | None
    created_at: datetime


@router.get("/projects/{project_id}", response_model=List[ExecutionLogResponse])
def get_project_logs(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all execution logs for a project.
    Returns newest first.
    """
    # Verify project ownership
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logs = (
        db.query(ExecutionLog)
        .filter(ExecutionLog.project_id == project_id)
        .order_by(ExecutionLog.created_at.desc())
        .all()
    )

    return logs


@router.get("/tasks/{task_id}", response_model=List[ExecutionLogResponse])
def get_task_logs(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all execution logs for a specific task.
    Useful for debugging failed tasks.
    """
    logs = (
        db.query(ExecutionLog)
        .join(Project, ExecutionLog.project_id == Project.id)
        .filter(
            ExecutionLog.task_id == task_id,
            Project.user_id == current_user.id
        )
        .order_by(ExecutionLog.created_at.desc())
        .all()
    )

    if not logs:
        raise HTTPException(status_code=404, detail="No logs found for this task")

    return logs


@router.get("/projects/{project_id}/summary")
def get_project_log_summary(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get execution summary for a project.
    Quick overview of success/failure counts.
    """
    # Verify project ownership
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Use SQL aggregation instead of loading all rows into Python
    row = (
        db.query(
            sa_func.count(ExecutionLog.id).label("total"),
            sa_func.sum(case((ExecutionLog.status == "success", 1), else_=0)).label("success"),
            sa_func.sum(case((ExecutionLog.status == "failure", 1), else_=0)).label("failure"),
            sa_func.coalesce(sa_func.sum(ExecutionLog.files_created), 0).label("files"),
        )
        .filter(ExecutionLog.project_id == project_id)
        .first()
    )

    return {
        "project_id": project_id,
        "total_executions": row.total,
        "success_count": row.success,
        "failure_count": row.failure,
        "total_files_created": row.files,
    }
